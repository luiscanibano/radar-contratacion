"""Conexión a Postgres para la capa de aplicación (auth, etc.).

Mismo patrón que `search/db.py`: el DSN sale de `api.settings` (misma
instancia de Postgres, esquema separado en `api/schema.sql`).
"""

from __future__ import annotations

from collections.abc import Iterator
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
    """Crea las tablas de la capa de aplicación (idempotente)."""
    ddl = _ESQUEMA.read_text(encoding="utf-8")
    with connect() as con:
        con.execute(ddl)
        con.commit()
