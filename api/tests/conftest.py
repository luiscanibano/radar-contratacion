"""Fixtures compartidas de los tests de la API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="session")
def cliente():
    """TestClient único para todo el proceso de pytest.

    El `with` es necesario para que corra el lifespan combinado de
    api/main.py::_lifespan (arranca el session manager del MCP montado en
    /mcp). Y tiene que haber UNO solo por proceso: el `mcp` de
    mcp_server/server.py es un singleton cuyo
    `StreamableHTTPSessionManager.run()` admite una única entrada de por
    vida — dos módulos de test con su propio TestClient reventarían con
    RuntimeError al segundo lifespan (pasó de verdad al añadir
    test_web.py junto a test_mcp.py).
    """
    with TestClient(app) as client:
        yield client
