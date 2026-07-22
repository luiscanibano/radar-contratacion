"""Ingesta de embeddings: marts DuckDB -> Postgres + pgvector.

Lee `main.fct_licitaciones` (mismo esquema que usa la capa `analytics/`),
construye el texto a embeber (título + objeto), y hace upsert en Postgres. La
ingesta es **incremental**: para cada expediente se calcula un hash del
contenido y solo se re-embeben los que son nuevos o cambiaron, de modo que un
refresco diario apenas toca el modelo.

Se ejecuta como job por lotes (Makefile: `make embeddings`; orquestación:
asset Dagster aguas abajo de los marts dbt).
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

import pandas as pd

from analytics.db import query as duck_query
from search import db
from search.embeddings import embed

# Solo expedientes con algo de texto; el título y el objeto pueden venir nulos
# por separado, pero al menos uno debe existir para que el embedding tenga sentido.
# `{limit_clause}` permite acotar filas en dev/CI (ver SEARCH_INGEST_LIMIT):
# embeber en CPU es lento (algunos segundos por documento), así que validar el
# pipeline completo con un subconjunto pequeño es mucho más rápido que esperar
# el lote completo.
_SQL_MARTS = """
select
    entry_id,
    expediente,
    coalesce(title, '')                 as title,
    coalesce(objeto, '')                as objeto,
    organo_contratacion                 as organo,
    left(cpv, 2)                        as cpv_division,
    anio,
    presupuesto_sin_impuestos           as presupuesto
from main.fct_licitaciones
where coalesce(title, objeto) is not null
{limit_clause}
"""

# Subimos los datos a una tabla de staging con COPY (un único stream, sin ida
# y vuelta por fila) y de ahí hacemos el upsert en una sola sentencia. Antes
# usábamos executemany() con miles de INSERT individuales: con ~16k filas de
# vectores de 1024 dims eso puede llenar a la vez el buffer de salida del
# cliente y el de respuesta del servidor y bloquear ambos lados sin avisar
# (deadlock de TCP), sin consumir CPU ni dar ningún error. COPY no tiene ese
# problema porque el protocolo es unidireccional.
_STAGING = """
create temporary table staging_embeddings (
    entry_id       text,
    expediente     text,
    objeto         text,
    organo         text,
    cpv_division   text,
    anio           integer,
    presupuesto    numeric,
    contenido      text,
    contenido_hash text,
    embedding      vector(1024)
) on commit drop
"""

_COPY_STAGING = """
copy staging_embeddings
    (entry_id, expediente, objeto, organo, cpv_division, anio, presupuesto,
     contenido, contenido_hash, embedding)
from stdin
"""

_UPSERT_DESDE_STAGING = """
insert into licitacion_embeddings
    (entry_id, expediente, objeto, organo, cpv_division, anio, presupuesto,
     contenido, contenido_hash, embedding, actualizado_en)
select entry_id, expediente, objeto, organo, cpv_division, anio, presupuesto,
       contenido, contenido_hash, embedding, now()
from staging_embeddings
on conflict (entry_id) do update set
    expediente     = excluded.expediente,
    objeto         = excluded.objeto,
    organo         = excluded.organo,
    cpv_division   = excluded.cpv_division,
    anio           = excluded.anio,
    presupuesto    = excluded.presupuesto,
    contenido      = excluded.contenido,
    contenido_hash = excluded.contenido_hash,
    embedding      = excluded.embedding,
    actualizado_en = now()
"""


@dataclass
class ResultadoIngesta:
    total: int          # filas candidatas en los marts
    embebidos: int      # filas nuevas/cambiadas re-embebidas
    sin_cambios: int    # filas ya al día (hash idéntico)


def _contenido(title: str, objeto: str) -> str:
    """Texto a embeber: título y objeto concatenados, sin ruido de espacios."""
    partes = [t.strip() for t in (title, objeto) if t and t.strip()]
    return ". ".join(partes)


def _hash(contenido: str) -> str:
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


def _hashes_existentes(con) -> dict[str, str]:
    with con.cursor() as cur:
        cur.execute("select entry_id, contenido_hash from licitacion_embeddings")
        return dict(cur.fetchall())


def ingest(batch_size: int = 64, limit: int | None = None) -> ResultadoIngesta:
    """Ejecuta la ingesta incremental completa y devuelve el conteo.

    `limit` acota el número de expedientes candidatos (ver SEARCH_INGEST_LIMIT
    en el bloque `__main__`), útil para validar el pipeline sin esperar el
    lote completo en una máquina lenta en CPU.
    """
    db.init_schema()

    limit_clause = f"limit {int(limit)}" if limit else ""
    df: pd.DataFrame = duck_query(_SQL_MARTS.format(limit_clause=limit_clause))
    df["contenido"] = [_contenido(t, o) for t, o in zip(df["title"], df["objeto"], strict=True)]
    df = df[df["contenido"].str.len() > 0].copy()
    df["contenido_hash"] = df["contenido"].map(_hash)

    with db.connect() as con:
        existentes = _hashes_existentes(con)

        pendientes = df[
            df.apply(lambda r: existentes.get(r["entry_id"]) != r["contenido_hash"], axis=1)
        ].copy()

        if not pendientes.empty:
            vectores = embed(pendientes["contenido"].tolist(), batch_size=batch_size)
            pendientes["embedding"] = [db.vector_literal(v) for v in vectores]

            with con.cursor() as cur:
                cur.execute(_STAGING)
                with cur.copy(_COPY_STAGING) as copy:
                    for _, r in pendientes.iterrows():
                        copy.write_row(
                            (
                                r["entry_id"],
                                r["expediente"],
                                r["objeto"] or None,
                                r["organo"],
                                r["cpv_division"],
                                int(r["anio"]) if pd.notna(r["anio"]) else None,
                                float(r["presupuesto"]) if pd.notna(r["presupuesto"]) else None,
                                r["contenido"],
                                r["contenido_hash"],
                                r["embedding"],
                            )
                        )
                cur.execute(_UPSERT_DESDE_STAGING)
            con.commit()

    return ResultadoIngesta(
        total=len(df),
        embebidos=len(pendientes),
        sin_cambios=len(df) - len(pendientes),
    )


if __name__ == "__main__":
    env_limit = os.getenv("SEARCH_INGEST_LIMIT")
    resultado = ingest(limit=int(env_limit) if env_limit else None)
    print(
        f"Ingesta de embeddings: {resultado.embebidos} embebidos, "
        f"{resultado.sin_cambios} sin cambios (total {resultado.total})."
    )
