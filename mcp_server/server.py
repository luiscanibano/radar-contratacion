"""Servidor MCP: expone los datos de contratación pública como herramientas
que se integran directamente en Claude Desktop / Claude Code, u otro cliente
MCP.

Reexpone las mismas funciones que usa el agente conversacional
(`api/agent/tools.py`) — nada de lógica nueva aquí, solo el envoltorio MCP.

Dos formas de arrancarlo:
- **Local, stdio, sin auth** (desarrollo con Claude Desktop en tu máquina):
    make mcp
  Config de Claude Desktop:
    {
      "mcpServers": {
        "radar-contratacion": {
          "command": "uv",
          "args": ["run", "python", "-m", "mcp_server.server"],
          "cwd": "/ruta/al/proyecto"
        }
      }
    }
- **Remoto, HTTP, con JWT** (producción): montado bajo `/mcp` dentro de la
  API FastAPI (ver `api/main.py`), protegido por `BearerAuthASGIMiddleware`
  con el mismo JWT que emite `/auth/login`.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from api.agent.tools import buscar_licitaciones as _buscar_hibrida
from api.agent.tools import run_readonly_sql

mcp = FastMCP("radar-contratacion")


@mcp.tool()
def consultar_datos(query: str) -> dict[str, Any]:
    """Ejecuta una consulta SQL de solo lectura (DuckDB) sobre los datos de
    contratación pública y devuelve las filas. Úsala para responder cualquier
    pregunta cuantitativa sobre licitaciones.
    """
    return run_readonly_sql(query)


@mcp.tool()
def buscar_licitaciones(consulta: str, k: int = 10) -> dict[str, Any]:
    """Busca licitaciones por significado (no solo coincidencia exacta de
    texto), combinando búsqueda léxica y semántica. Úsala para preguntas en
    lenguaje natural sobre el objeto de una licitación (sinónimos, paráfrasis,
    conceptos) que no encajan bien como filtro SQL exacto.
    """
    return _buscar_hibrida(consulta, k=k)


if __name__ == "__main__":
    mcp.run()
