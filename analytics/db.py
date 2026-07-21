"""Acceso de solo lectura a los marts de DuckDB para los módulos de DS.

Todos los módulos de `analytics/` consultan los marts publicados por dbt (esquema
`main` del DuckDB de `settings.duckdb_path`). Nunca escriben: la capa DS lee los
marts y devuelve DataFrames; la persistencia de sus resultados, si hace falta, es
responsabilidad de la orquestación.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb
import pandas as pd

from api.settings import settings

# Raíz del repositorio (…/analytics/db.py -> …/). Permite abrir el DuckDB con
# independencia del directorio de trabajo (notebooks, tests, orquestación).
_RAIZ = Path(__file__).resolve().parents[1]


def _ruta_duckdb() -> str:
    ruta = Path(settings.duckdb_path)
    return str(ruta if ruta.is_absolute() else _RAIZ / ruta)


@contextmanager
def connect() -> Iterator[duckdb.DuckDBPyConnection]:
    """Conexión de solo lectura al DuckDB de marts, cerrada al salir del contexto."""
    con = duckdb.connect(_ruta_duckdb(), read_only=True)
    try:
        yield con
    finally:
        con.close()


def query(sql: str, **params: object) -> pd.DataFrame:
    """Ejecuta `sql` de solo lectura y devuelve el resultado como DataFrame.

    Los parámetros se pasan por nombre (`$nombre` en el SQL) para evitar
    interpolación de cadenas.
    """
    with connect() as con:
        rel = con.execute(sql, params) if params else con.execute(sql)
        return rel.df()
