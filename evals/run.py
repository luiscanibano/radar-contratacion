"""Arnés de evaluación del agente.

Cada caso del golden set se puntúa por dos vías independientes:

- **Comprobación determinista de herramientas**: ¿usó la tool que tocaba? ¿se
  abstuvo de llamar a ninguna cuando la pregunta era ambigua? Esto no necesita
  LLM y no tiene varianza, así que una regresión aquí es una regresión de
  verdad.
- **LLM-as-judge**: un modelo distinto (y más capaz) que el del agente decide
  si la respuesta cumple el criterio, devolviendo un veredicto **estructurado**
  (structured outputs) en vez de texto libre que haya que parsear a ojo.

Un caso pasa solo si supera ambas. Además se agregan coste, latencia y ratio de
caché a partir de las trazas (`api/observabilidad.py`), para que un cambio de
prompt que mejore la calidad pero triplique la factura se vea de inmediato.

    uv run python -m evals.run                # golden set completo
    uv run python -m evals.run --caso ambiguedad-sin-anio
    uv run python -m evals.run --sin-juez     # solo comprobaciones deterministas
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from anthropic import Anthropic, APIError
from pydantic import BaseModel

from api.agent.graph import responder
from api.observabilidad import Traza, emitir
from api.settings import settings

GOLDEN = Path(__file__).parent / "golden_set.jsonl"
INFORMES = Path(__file__).parent / "informes"

# Umbral de aprobado de la suite. Por debajo, `make evals` sale con código 1
# para que un CI lo pare.
UMBRAL_APROBADO = 0.8

JUDGE_PROMPT = """Eres un evaluador estricto de un agente de datos sobre contratación
pública española. Dada una PREGUNTA, un CRITERIO de corrección y la RESPUESTA del
agente, decide si la respuesta cumple el criterio.

Reglas de evaluación:
- Juzga solo contra el CRITERIO. No premies florituras ni penalices el estilo.
- Si el criterio pide una cifra concreta y la respuesta no la da, FALLA.
- Si el criterio pide pedir una aclaración y el agente responde con datos, FALLA.
- Si la respuesta inventa datos o dice haber hecho algo que no puede hacer, FALLA.

PREGUNTA: {pregunta}
CRITERIO: {criterio}
RESPUESTA: {respuesta}
"""


class Veredicto(BaseModel):
    """Salida estructurada del juez (structured outputs de la Claude API)."""

    veredicto: Literal["PASA", "FALLA"]
    razon: str


@dataclass
class Resultado:
    id: str
    categoria: str
    pregunta: str
    respuesta: str
    tools_usadas: list[str]
    fallos_tools: list[str] = field(default_factory=list)
    veredicto_juez: str | None = None
    razon_juez: str | None = None
    coste_usd: float = 0.0
    latencia_s: float = 0.0
    turnos: int = 0
    ratio_cache: float = 0.0

    @property
    def pasa(self) -> bool:
        if self.fallos_tools:
            return False
        # Sin juez (--sin-juez), un caso pasa si las comprobaciones deterministas
        # están limpias: no se le exige un veredicto que no se ha pedido.
        return self.veredicto_juez in (None, "PASA")


def comprobar_tools(caso: dict[str, Any], traza: Traza) -> list[str]:
    """Comprobaciones deterministas sobre qué herramientas usó el agente."""
    fallos = []
    usadas = set(traza.tools_usadas)
    for esperada in caso.get("tools_esperadas", []):
        if esperada not in usadas:
            fallos.append(f"no usó la herramienta esperada '{esperada}'")
    for prohibida in caso.get("tools_prohibidas", []):
        if prohibida in usadas:
            fallos.append(f"usó la herramienta prohibida '{prohibida}'")
    return fallos


def juzgar(client: Anthropic, caso: dict[str, Any], respuesta: str) -> Veredicto:
    mensaje = client.messages.parse(
        model=settings.judge_model,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(
                    pregunta=caso["pregunta"],
                    criterio=caso["criterio"],
                    respuesta=respuesta,
                ),
            }
        ],
        output_format=Veredicto,
    )
    return mensaje.parsed_output


def evaluar_caso(client: Anthropic | None, caso: dict[str, Any]) -> Resultado:
    respuesta, traza = responder(caso["pregunta"])
    emitir(traza)

    resultado = Resultado(
        id=caso["id"],
        categoria=caso.get("categoria", "sin-categoria"),
        pregunta=caso["pregunta"],
        respuesta=respuesta,
        tools_usadas=traza.tools_usadas,
        fallos_tools=comprobar_tools(caso, traza),
        coste_usd=traza.coste_usd,
        latencia_s=traza.latencia_total_s,
        turnos=traza.turnos,
        ratio_cache=traza.ratio_cache,
    )

    if client is not None:
        try:
            veredicto = juzgar(client, caso, respuesta)
            resultado.veredicto_juez = veredicto.veredicto
            resultado.razon_juez = veredicto.razon
        except APIError as exc:
            # Un fallo del juez no es un fallo del agente: se marca como tal
            # para no contaminar la tasa de aprobados con ruido de red.
            resultado.veredicto_juez = "ERROR_JUEZ"
            resultado.razon_juez = f"El juez no respondió: {exc}"

    return resultado


def agregar(resultados: list[Resultado]) -> dict[str, Any]:
    latencias = [r.latencia_s for r in resultados]
    juzgados = [r for r in resultados if r.veredicto_juez != "ERROR_JUEZ"]
    pasan = [r for r in juzgados if r.pasa]

    por_categoria: dict[str, dict[str, int]] = {}
    for r in juzgados:
        cat = por_categoria.setdefault(r.categoria, {"pasan": 0, "total": 0})
        cat["total"] += 1
        cat["pasan"] += int(r.pasa)

    return {
        "casos": len(resultados),
        "evaluables": len(juzgados),
        "pasan": len(pasan),
        "tasa_aprobados": len(pasan) / len(juzgados) if juzgados else 0.0,
        "errores_juez": len(resultados) - len(juzgados),
        "coste_total_usd": round(sum(r.coste_usd for r in resultados), 6),
        "latencia_media_s": round(statistics.mean(latencias), 2) if latencias else 0.0,
        "latencia_max_s": round(max(latencias), 2) if latencias else 0.0,
        "ratio_cache_medio": (
            round(statistics.mean([r.ratio_cache for r in resultados]), 3) if resultados else 0.0
        ),
        "por_categoria": por_categoria,
    }


def escribir_informe(resultados: list[Resultado], resumen: dict[str, Any]) -> Path:
    INFORMES.mkdir(parents=True, exist_ok=True)
    sello = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    ruta = INFORMES / f"{sello}.json"
    ruta.write_text(
        json.dumps(
            {
                "fecha": sello,
                "modelo_agente": settings.claude_model,
                "modelo_juez": settings.judge_model,
                "resumen": resumen,
                "resultados": [r.__dict__ for r in resultados],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return ruta


def imprimir(resultados: list[Resultado], resumen: dict[str, Any], informe: Path) -> None:
    for r in resultados:
        estado = "PASA" if r.pasa else "FALLA"
        if r.veredicto_juez == "ERROR_JUEZ":
            estado = "ERROR"
        print(f"[{estado}] {r.id} ({r.categoria})")
        print(
            f"        tools: {r.tools_usadas or 'ninguna'} · {r.turnos} turnos · "
            f"{r.latencia_s:.1f}s · ${r.coste_usd:.4f}"
        )
        for fallo in r.fallos_tools:
            print(f"        ✗ {fallo}")
        if r.razon_juez:
            print(f"        juez: {r.razon_juez}")
        print()

    print(
        f"Resultado: {resumen['pasan']}/{resumen['evaluables']} casos superados "
        f"({resumen['tasa_aprobados']:.0%})."
    )
    print(
        f"Coste total: ${resumen['coste_total_usd']:.4f} · "
        f"latencia media {resumen['latencia_media_s']}s (máx {resumen['latencia_max_s']}s) · "
        f"caché {resumen['ratio_cache_medio']:.0%}"
    )
    if resumen["errores_juez"]:
        print(f"Avisos: {resumen['errores_juez']} caso(s) sin veredicto por fallo del juez.")
    print(f"Informe: {informe}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalúa el agente contra el golden set.")
    parser.add_argument("--caso", help="Evalúa solo el caso con este id.")
    parser.add_argument("--categoria", help="Evalúa solo los casos de esta categoría.")
    parser.add_argument(
        "--sin-juez",
        action="store_true",
        help="Salta el LLM-as-judge y deja solo las comprobaciones deterministas.",
    )
    args = parser.parse_args()

    casos = [
        json.loads(linea) for linea in GOLDEN.read_text(encoding="utf-8").splitlines() if linea
    ]
    if args.caso:
        casos = [c for c in casos if c["id"] == args.caso]
    if args.categoria:
        casos = [c for c in casos if c.get("categoria") == args.categoria]
    if not casos:
        print("Ningún caso coincide con el filtro.", file=sys.stderr)
        return 2

    client = None if args.sin_juez else Anthropic(api_key=settings.anthropic_api_key)
    resultados = [evaluar_caso(client, caso) for caso in casos]
    resumen = agregar(resultados)
    informe = escribir_informe(resultados, resumen)
    imprimir(resultados, resumen, informe)

    return 0 if resumen["tasa_aprobados"] >= UMBRAL_APROBADO else 1


if __name__ == "__main__":
    raise SystemExit(main())
