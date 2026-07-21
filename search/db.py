"""Conexión a Postgres + pgvector para la capa de búsqueda.

A diferencia de `analytics/db.py` (DuckDB de solo lectura para los marts), aquí
Postgres es de lectura/escritura: la ingesta escribe embeddings y la búsqueda
los consulta. El DSN sale de `api.settings` (compartido con el resto de la app).

Los vectores se pasan como literales de texto (`'[0.1,0.2,...]'::vector`), así
que no necesitamos registrar adaptadores de pgvector: funciona con un psycopg
pelado y es robusto entre versiones.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

import psycopg

from api.settings import settings

_ESQUEMA = Path(__file__).parent / "schema.sql"


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Conexión a Postgres, cerrada al salir del contexto."""
    con = psycopg.connect(settings.postgres_dsn)
    try:
        yield con
    finally:
        con.close()


def init_schema() -> None:
    """Crea la extensión, la tabla y los índices (idempotente)."""
    ddl = _ESQUEMA.read_text(encoding="utf-8")
    with connect() as con:
        con.execute(ddl)
        con.commit()


def vector_literal(vec: Iterable[float]) -> str:
    """Serializa un vector a la representación textual que entiende pgvector."""
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
