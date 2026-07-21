"""Fusión de rankings con Reciprocal Rank Fusion (RRF).

RRF combina varias listas ordenadas (aquí: la léxica y la vectorial) sin
necesitar que sus puntuaciones sean comparables entre sí. Cada documento suma
`1 / (k + rango)` por cada lista en la que aparece; `k` (típicamente 60) atenúa
el peso de las primeras posiciones y hace la fusión robusta a outliers de score.

Función pura y sin dependencias: es el núcleo testeable de la búsqueda híbrida.
"""

from __future__ import annotations

from collections.abc import Sequence

K_RRF_DEFECTO = 60


def rrf(rankings: Sequence[Sequence[str]], k: int = K_RRF_DEFECTO) -> dict[str, float]:
    """Puntuación RRF por documento a partir de varias listas ordenadas.

    Cada `ranking` es una secuencia de IDs ya ordenada de más a menos relevante.
    Devuelve un dict {id: score} con la suma de contribuciones recíprocas.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for posicion, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + posicion)
    return scores


def fusionar(
    rankings: Sequence[Sequence[str]], k: int = K_RRF_DEFECTO, limite: int | None = None
) -> list[tuple[str, float]]:
    """Fusiona rankings y devuelve `(id, score)` ordenado desc, top-`limite`.

    Ante empate en score, desempata por ID para que el orden sea determinista.
    """
    scores = rrf(rankings, k=k)
    ordenado = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return ordenado[:limite] if limite is not None else ordenado
