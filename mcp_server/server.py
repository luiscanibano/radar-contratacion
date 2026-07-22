"""Servidor MCP: expone los datos de contratación pública como herramientas
que se integran directamente en Claude Desktop / Claude Code.

Arranca con:  make mcp

Para usarlo en Claude Desktop, añade a su config:
    {
      "mcpServers": {
        "radar-contratacion": {
          "command": "uv",
          "args": ["run", "python", "-m", "mcp_server.server"],
          "cwd": "/ruta/al/proyecto"
        }
      }
    }
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from api.agent.tools import buscar_licitaciones as _buscar_hibrida
from api.agent.tools import run_readonly_sql

mcp = FastMCP("radar-contratacion")


@mcp.tool()
def buscar_licitaciones(cpv_division: str | None = None, anio: int | None = None) -> dict:
    """Busca licitaciones filtrando por sector (división CPV, 2 dígitos) y/o año."""
    where = []
    if cpv_division:
        where.append(f"cpv_division = '{cpv_division}'")
    if anio:
        where.append(f"anio = {anio}")
    clause = f"where {' and '.join(where)}" if where else ""
    return run_readonly_sql(
        f"select expediente, objeto, organo_contratacion, presupuesto_sin_impuestos "
        f"from main.fct_licitaciones {clause}"
    )


@mcp.tool()
def buscar_licitaciones_semantica(consulta: str, k: int = 10) -> dict:
    """Busca licitaciones por significado (léxica + vectorial, fusión RRF).

    A diferencia de `buscar_licitaciones` (filtros exactos por CPV/año), esta
    herramienta acepta lenguaje natural: sinónimos, paráfrasis y conceptos que
    no encajan bien como filtro SQL exacto.
    """
    return _buscar_hibrida(consulta, k=k)


@mcp.tool()
def consultar_sql(query: str) -> dict:
    """Ejecuta una consulta SQL de solo lectura sobre los datos de contratación."""
    return run_readonly_sql(query)


if __name__ == "__main__":
    mcp.run()
