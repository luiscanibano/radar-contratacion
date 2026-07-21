"""Modelo de embeddings local (multilingüe, CPU).

Usamos `sentence-transformers` con BAAI/bge-m3 (1024 dims), que rinde bien en
español y —a diferencia de la familia e5— no exige prefijos `query:`/`passage:`.
Coste cero y sin dependencia de red, a cambio de una ingesta más lenta en CPU
(pensada como job por lotes, no en caliente).

El import de `sentence_transformers` (que arrastra torch) es **perezoso**: así
los módulos que solo necesitan la fusión RRF o el DSL de búsqueda no pagan la
carga del modelo, y los tests puros corren sin torch instalado.
"""

from __future__ import annotations

from functools import lru_cache

from api.settings import settings


@lru_cache(maxsize=1)
def _modelo():
    from sentence_transformers import SentenceTransformer  # import perezoso (torch pesa)

    return SentenceTransformer(settings.embedding_model)


def embed(textos: list[str], batch_size: int = 32) -> list[list[float]]:
    """Embebe una lista de textos y devuelve vectores normalizados.

    Con `normalize_embeddings=True` el coseno equivale al producto interno, que
    es lo que mide el índice HNSW (`vector_cosine_ops`).
    """
    if not textos:
        return []
    vectores = _modelo().encode(
        textos,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectores]
