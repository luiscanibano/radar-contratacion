"""Evaluación de la búsqueda híbrida (semana 4) con métricas de recuperación.

Mide lo que el LLM-as-judge de `evals/run.py` no puede medir: si el recuperador
pone los documentos relevantes *arriba*. Son las métricas estándar de IR y las
mismas que calculan las métricas no-LLM de Ragas, pero implementadas aquí en
~40 líneas verificables en vez de arrastrar la dependencia (ver evals/README.md).

Flujo de trabajo:

1. `--preparar "mantenimiento de jardines"` lanza la búsqueda y vuelca los
   candidatos con su `entry_id` y su objeto, para poder etiquetar a mano.
2. Se pegan los `entry_id` relevantes en `evals/retrieval_set.jsonl`.
3. `uv run python -m evals.retrieval` evalúa el conjunto etiquetado.

Sin paso 2 no hay medida posible: un conjunto de relevancia se etiqueta, no se
adivina.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from math import log2
from pathlib import Path
from typing import Any

CONJUNTO = Path(__file__).parent / "retrieval_set.jsonl"
K_DEFECTO = 10


def recall_en_k(recuperados: list[str], relevantes: set[str], k: int) -> float:
    """Fracción de los documentos relevantes que aparecen en el top-k."""
    if not relevantes:
        return 0.0
    aciertos = len(set(recuperados[:k]) & relevantes)
    return aciertos / len(relevantes)


def precision_en_k(recuperados: list[str], relevantes: set[str], k: int) -> float:
    """Fracción del top-k que es relevante. Se divide entre k, no entre lo
    recuperado: devolver 2 resultados buenos cuando se pidieron 10 no es
    precisión perfecta, es cobertura insuficiente."""
    if k <= 0:
        return 0.0
    return len(set(recuperados[:k]) & relevantes) / k


def mrr(recuperados: list[str], relevantes: set[str]) -> float:
    """Reciprocal Rank: 1/posición del primer acierto (0 si no hay ninguno)."""
    for posicion, doc in enumerate(recuperados, start=1):
        if doc in relevantes:
            return 1 / posicion
    return 0.0


def ndcg_en_k(recuperados: list[str], relevantes: set[str], k: int) -> float:
    """nDCG@k con ganancia binaria: premia los aciertos cuanto más arriba estén."""
    if not relevantes:
        return 0.0
    dcg = sum(
        1 / log2(i + 1) for i, doc in enumerate(recuperados[:k], start=1) if doc in relevantes
    )
    ideal = sum(1 / log2(i + 1) for i in range(1, min(len(relevantes), k) + 1))
    return dcg / ideal if ideal else 0.0


def evaluar_consulta(recuperados: list[str], relevantes: set[str], k: int) -> dict[str, float]:
    return {
        f"recall@{k}": recall_en_k(recuperados, relevantes, k),
        f"precision@{k}": precision_en_k(recuperados, relevantes, k),
        f"ndcg@{k}": ndcg_en_k(recuperados, relevantes, k),
        "mrr": mrr(recuperados, relevantes),
    }


def _buscar(consulta: str, k: int) -> list[Any]:
    try:
        from search.hibrida import buscar
    except ImportError as exc:  # noqa: BLE001 — el extra 'search' es opcional
        print(
            f"Búsqueda híbrida no disponible (falta el extra 'search'): {exc}\n"
            "Instala con: uv sync --all-extras",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return buscar(consulta, k=k)


def preparar(consulta: str, k: int) -> None:
    """Vuelca candidatos para etiquetar a mano."""
    resultados = _buscar(consulta, k)
    print(f"Consulta: {consulta!r} — {len(resultados)} candidatos\n")
    for posicion, r in enumerate(resultados, start=1):
        objeto = (r.objeto or "")[:110]
        print(f"{posicion:2d}. {r.entry_id}  (score {r.score:.4f})")
        print(f"    {objeto}")
    print("\nPega los entry_id relevantes en evals/retrieval_set.jsonl:")
    print(json.dumps({"consulta": consulta, "relevantes": []}, ensure_ascii=False))


def evaluar_conjunto(k: int) -> int:
    if not CONJUNTO.exists():
        print(f"No existe {CONJUNTO}. Créalo con --preparar.", file=sys.stderr)
        return 2

    casos = [
        json.loads(linea) for linea in CONJUNTO.read_text(encoding="utf-8").splitlines() if linea
    ]
    etiquetados = [c for c in casos if c.get("relevantes")]
    sin_etiquetar = [c["consulta"] for c in casos if not c.get("relevantes")]

    if not etiquetados:
        print(
            "El conjunto no tiene ninguna consulta etiquetada todavía.\n"
            "Usa --preparar \"<consulta>\" y rellena el campo 'relevantes'.",
            file=sys.stderr,
        )
        return 2

    filas = []
    for caso in etiquetados:
        recuperados = [r.entry_id for r in _buscar(caso["consulta"], k)]
        metricas = evaluar_consulta(recuperados, set(caso["relevantes"]), k)
        filas.append((caso["consulta"], metricas))

    claves = list(filas[0][1])
    print(f"{'consulta':<48} " + " ".join(f"{c:>12}" for c in claves))
    for consulta, metricas in filas:
        print(f"{consulta[:47]:<48} " + " ".join(f"{metricas[c]:>12.3f}" for c in claves))

    print("\nMedia:")
    for clave in claves:
        media = statistics.mean(m[clave] for _, m in filas)
        print(f"  {clave:<14} {media:.3f}")

    if sin_etiquetar:
        print(f"\nSin etiquetar ({len(sin_etiquetar)}): {', '.join(sin_etiquetar)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalúa la búsqueda híbrida (recuperación).")
    parser.add_argument("--preparar", metavar="CONSULTA", help="Vuelca candidatos para etiquetar.")
    parser.add_argument("-k", type=int, default=K_DEFECTO, help=f"Top-k (por defecto {K_DEFECTO}).")
    args = parser.parse_args()

    if args.preparar:
        preparar(args.preparar, args.k)
        return 0
    return evaluar_conjunto(args.k)


if __name__ == "__main__":
    raise SystemExit(main())
