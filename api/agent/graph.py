"""Agente conversacional con la Claude API (bucle de tool use).

Empezamos con un bucle directo sobre el SDK de Anthropic, honesto y fácil de
razonar. Cuando el flujo crezca (memoria, múltiples herramientas, ramificación),
se migra a LangGraph sin cambiar las tools.
"""

from __future__ import annotations

import json
import time

from anthropic import Anthropic, APIError

from api.agent.tools import (
    BUSQUEDA_HIBRIDA_TOOL,
    SCHEMA_DESCRIPTION,
    SQL_TOOL,
    buscar_licitaciones,
    run_readonly_sql,
)
from api.observabilidad import LlamadaModelo, Traza, UsoTool
from api.settings import settings

SYSTEM_PROMPT = f"""
Eres el analista de datos de "Radar de Contratación Pública". Respondes preguntas
sobre licitaciones del sector público español consultando los datos con dos
herramientas: `consultar_datos` (SQL de solo lectura sobre DuckDB, para preguntas
cuantitativas o con filtros exactos) y `buscar_licitaciones` (búsqueda híbrida
léxica + semántica, para preguntas en lenguaje natural sobre el objeto de una
licitación que no encajan bien como filtro SQL exacto).

Reglas:
- Siempre basa tus respuestas en datos reales obtenidos con las herramientas.
- Cita las cifras y explica de dónde salen. Nunca inventes números.
- Al hablar de posibles irregularidades, usa lenguaje de "señal a revisar",
  nunca acusaciones.
- Si la pregunta es ambigua o le falta un dato imprescindible para elegir bien
  la herramienta o los filtros (p. ej. no está claro el año, el órgano, o si
  se busca un expediente concreto o una categoría amplia), no lo adivines:
  responde con una pregunta breve pidiendo esa aclaración en vez de llamar a
  una herramienta.
- Si una herramienta devuelve un error, o si las herramientas disponibles no
  bastan para responder con datos reales, dilo explícitamente en vez de
  inventar una respuesta.

Esquema disponible (para `consultar_datos`):
{SCHEMA_DESCRIPTION}
""".strip()


def _registrar_uso(traza: Traza, llamada: LlamadaModelo, response) -> None:
    """Copia los contadores de `usage` a la traza, si la respuesta los trae.

    `getattr` en vez de acceso directo: los dobles de test no simulan `usage`,
    y un campo nuevo o ausente en el SDK no debe tumbar una respuesta buena.
    """
    uso = getattr(response, "usage", None)
    if uso is None:
        return
    llamada.input_tokens = getattr(uso, "input_tokens", 0) or 0
    llamada.output_tokens = getattr(uso, "output_tokens", 0) or 0
    llamada.cache_read_input_tokens = getattr(uso, "cache_read_input_tokens", 0) or 0
    llamada.cache_creation_input_tokens = getattr(uso, "cache_creation_input_tokens", 0) or 0


def answer(question: str, max_turns: int = 5) -> str:
    """Respuesta en texto plano. Envoltorio de `responder()` para quien no quiera la traza."""
    return responder(question, max_turns=max_turns)[0]


def responder(question: str, max_turns: int = 5) -> tuple[str, Traza]:
    """Responde y devuelve además la traza (turnos, tools, tokens, coste, latencia).

    No persiste nada: emitir la traza es responsabilidad de quien llama
    (`api/main.py`, `evals/run.py`), vía `api.observabilidad.emitir`. Así el
    agente no depende de la red ni ensucia el disco durante los tests.
    """
    client = Anthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": question}]
    traza = Traza(pregunta=question, modelo=settings.claude_model)
    arranque = time.perf_counter()

    def _cerrar(texto: str) -> tuple[str, Traza]:
        traza.respuesta = texto
        traza.latencia_total_s = time.perf_counter() - arranque
        return texto, traza

    for turno in range(1, max_turns + 1):
        llamada = LlamadaModelo(turno=turno)
        inicio_llamada = time.perf_counter()
        try:
            response = client.messages.create(
                model=settings.claude_model,
                max_tokens=1500,
                # cache_control cachea el prompt de sistema (esquema + reglas): es
                # idéntico en cada petición, así que a partir de la 2ª se sirve a
                # ~0,1x del coste. Verifica con response.usage.cache_read_input_tokens.
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[SQL_TOOL, BUSQUEDA_HIBRIDA_TOOL],
                messages=messages,
            )
        except APIError as exc:
            llamada.latencia_s = time.perf_counter() - inicio_llamada
            traza.llamadas.append(llamada)
            traza.error = f"APIError: {exc.message}"
            return _cerrar(
                f"No he podido contactar con el modelo ({exc.message}). "
                "Inténtalo de nuevo en unos segundos."
            )

        llamada.latencia_s = time.perf_counter() - inicio_llamada
        llamada.stop_reason = response.stop_reason
        _registrar_uso(traza, llamada, response)
        traza.llamadas.append(llamada)

        if response.stop_reason != "tool_use":
            return _cerrar("".join(b.text for b in response.content if b.type == "text"))

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            uso = UsoTool(turno=turno, nombre=block.name, entrada=dict(block.input or {}))
            inicio_tool = time.perf_counter()
            try:
                if block.name == "consultar_datos":
                    result = run_readonly_sql(block.input["query"])
                elif block.name == "buscar_licitaciones":
                    result = buscar_licitaciones(
                        block.input["consulta"], k=block.input.get("k", 10)
                    )
                else:
                    result = {"error": f"Herramienta desconocida: {block.name}"}
            except Exception as exc:  # noqa: BLE001 — un tool_use mal formado no debe tumbar el agente
                result = {"error": f"No se pudo ejecutar la herramienta: {exc}"}
            uso.latencia_s = time.perf_counter() - inicio_tool
            uso.error = result.get("error")
            uso.ok = uso.error is None
            uso.filas = result.get("row_count")
            traza.tools.append(uso)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str, ensure_ascii=False),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    traza.error = f"max_turns ({max_turns}) agotado"
    return _cerrar("No he podido resolver la consulta en el número de pasos permitido.")
