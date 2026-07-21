"""Herramientas del agente. La principal es text-to-SQL de solo lectura sobre
DuckDB, con guardrails para impedir cualquier operación que no sea SELECT.
"""

from __future__ import annotations

import re
from typing import Any

import duckdb

from api.settings import settings

# Solo permitimos consultas de lectura. El agente nunca debe modificar datos.
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|copy|pragma|install|load)\b",
    re.IGNORECASE,
)

# Esquema que exponemos al agente en el system prompt (text-to-SQL fiable).
SCHEMA_DESCRIPTION = """
Tabla: main_marts.fct_licitaciones
Columnas:
  entry_id (texto), expediente (texto), objeto (texto),
  organo_contratacion (texto), estado (texto), tipo_contrato (texto),
  cpv (texto), cpv_division (texto, 2 dígitos = sector),
  valor_estimado (decimal), presupuesto_sin_impuestos (decimal),
  anio (entero), actualizado_en (timestamp), cerca_umbral_menor (booleano)
""".strip()


def run_readonly_sql(query: str, limit: int = 100) -> dict[str, Any]:
    """Ejecuta un SELECT contra DuckDB y devuelve filas + columnas.

    Bloquea cualquier sentencia que no sea de solo lectura.
    """
    if _FORBIDDEN.search(query):
        return {"error": "Solo se permiten consultas SELECT de solo lectura."}
    if not query.strip().lower().startswith(("select", "with")):
        return {"error": "La consulta debe empezar por SELECT o WITH."}

    con = duckdb.connect(settings.duckdb_path, read_only=True)
    try:
        rel = con.sql(f"select * from ({query}) limit {limit}")
        cols = rel.columns
        rows = [dict(zip(cols, r)) for r in rel.fetchall()]
        return {"columns": cols, "rows": rows, "row_count": len(rows)}
    except Exception as exc:  # noqa: BLE001 — devolvemos el error al agente para que corrija
        return {"error": str(exc)}
    finally:
        con.close()


# Definición de la tool en formato de la Claude API (tool use).
SQL_TOOL = {
    "name": "consultar_datos",
    "description": (
        "Ejecuta una consulta SQL de solo lectura (DuckDB) sobre los datos de "
        "contratación pública y devuelve las filas. Úsala para responder cualquier "
        "pregunta cuantitativa sobre licitaciones."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Consulta SELECT válida en dialecto DuckDB.",
            }
        },
        "required": ["query"],
    },
}
