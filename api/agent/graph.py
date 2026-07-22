"""Agente conversacional con la Claude API (bucle de tool use).

Empezamos con un bucle directo sobre el SDK de Anthropic, honesto y fácil de
razonar. Cuando el flujo crezca (memoria, múltiples herramientas, ramificación),
se migra a LangGraph sin cambiar las tools.
"""

from __future__ import annotations

import json

from anthropic import Anthropic, APIError

from api.agent.tools import (
    BUSQUEDA_HIBRIDA_TOOL,
    SCHEMA_DESCRIPTION,
    SQL_TOOL,
    buscar_licitaciones,
    run_readonly_sql,
)
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


def answer(question: str, max_turns: int = 5) -> str:
    client = Anthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": question}]

    for _ in range(max_turns):
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
            return (
                f"No he podido contactar con el modelo ({exc.message}). "
                "Inténtalo de nuevo en unos segundos."
            )

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
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
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str, ensure_ascii=False),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return "No he podido resolver la consulta en el número de pasos permitido."
