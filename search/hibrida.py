"""Búsqueda híbrida: léxica (Postgres FTS español) + vectorial (pgvector) + RRF.

Cada consulta lanza dos recuperaciones independientes sobre
`licitacion_embeddings` y las fusiona con Reciprocal Rank Fusion:

- **Léxica**: `plainto_tsquery('spanish', ...)` sobre el tsvector, ordenado por
  `ts_rank`. Aporta precisión en términos exactos, siglas y nombres propios.
- **Vectorial**: distancia coseno (`<=>`) contra el embedding de la consulta.
  Aporta recuperación semántica (sinónimos, paráfrasis).

La fusión RRF (ver `search/fusion.py`) evita tener que calibrar pesos entre dos
puntuaciones de escalas distintas.
"""

from __future__ import annotations

from dataclasses import dataclass

from search import db
from search.embeddings import embed
from search.fusion import K_RRF_DEFECTO, fusionar

# Cuántos candidatos pide cada recuperador antes de fusionar. Se toma un pool más
# ancho que `k` para que RRF tenga material y los solapamientos puntúen alto.
_POOL_DEFECTO = 50

_SQL_VECTORIAL = """
select entry_id
from licitacion_embeddings
where embedding is not null
order by embedding <=> %(q)s::vector
limit %(pool)s
"""

_SQL_LEXICA = """
select entry_id
from licitacion_embeddings
where fts @@ plainto_tsquery('spanish', %(q)s)
order by ts_rank(fts, plainto_tsquery('spanish', %(q)s)) desc
limit %(pool)s
"""

_SQL_METADATOS = """
select entry_id, expediente, objeto, organo, cpv_division, anio, presupuesto
from licitacion_embeddings
where entry_id = any(%(ids)s)
"""


@dataclass
class Resultado:
    entry_id: str
    expediente: str | None
    objeto: str | None
    organo: str | None
    cpv_division: str | None
    anio: int | None
    presupuesto: float | None
    score: float


def _ranking(con, sql: str, params: dict) -> list[str]:
    with con.cursor() as cur:
        cur.execute(sql, params)
        return [fila[0] for fila in cur.fetchall()]


def buscar(
    consulta: str, k: int = 10, pool: int = _POOL_DEFECTO, k_rrf: int = K_RRF_DEFECTO
) -> list[Resultado]:
    """Devuelve las `k` licitaciones más relevantes para `consulta` (híbrido)."""
    q_vec = db.vector_literal(embed([consulta])[0])

    with db.connect() as con:
        ranking_vec = _ranking(con, _SQL_VECTORIAL, {"q": q_vec, "pool": pool})
        ranking_lex = _ranking(con, _SQL_LEXICA, {"q": consulta, "pool": pool})

        fusionados = fusionar([ranking_lex, ranking_vec], k=k_rrf, limite=k)
        if not fusionados:
            return []

        ids = [doc_id for doc_id, _ in fusionados]
        score_por_id = dict(fusionados)

        with con.cursor() as cur:
            cur.execute(_SQL_METADATOS, {"ids": ids})
            cols = [c.name for c in cur.description]
            filas = (dict(zip(cols, row, strict=True)) for row in cur.fetchall())
            metadatos = {r["entry_id"]: r for r in filas}

    # Respetamos el orden de la fusión (los metadatos vienen sin ordenar).
    resultados = []
    for doc_id in ids:
        m = metadatos.get(doc_id)
        if m is None:
            continue
        resultados.append(
            Resultado(
                entry_id=m["entry_id"],
                expediente=m["expediente"],
                objeto=m["objeto"],
                organo=m["organo"],
                cpv_division=m["cpv_division"],
                anio=m["anio"],
                presupuesto=float(m["presupuesto"]) if m["presupuesto"] is not None else None,
                score=score_por_id[doc_id],
            )
        )
    return resultados
