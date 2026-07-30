"""Tests del endpoint de búsqueda híbrida (contra Postgres real, como test_auth.py)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.auth import create_access_token, registrar_usuario
from api.cuota import uso_actual
from api.db import connect, init_schema
from api.main import app


@pytest.fixture(autouse=True, scope="module")
def _esquema():
    init_schema()


@pytest.fixture
def usuario():
    email = f"test-{uuid.uuid4().hex}@example.com"
    creado = registrar_usuario(email, "contraseña-larga")
    yield creado
    with connect() as con:
        con.execute("delete from uso_mensual where usuario_id = %s", (creado.id,))
        con.execute("delete from suscripciones where usuario_id = %s", (creado.id,))
        con.execute("delete from usuarios where id = %s", (creado.id,))
        con.commit()


@pytest.fixture
def cliente():
    return TestClient(app)


_RESULTADO_FALSO = {
    "resultados": [
        {
            "entry_id": "e1",
            "expediente": "EXP-1",
            "objeto": "Obras de accesibilidad",
            "organo": "Ayuntamiento de Prueba",
            "cpv_division": "45",
            "anio": 2025,
            "presupuesto": 12345.67,
            "score": 0.9,
        }
    ],
    "row_count": 1,
}


def test_buscar_sin_token_da_401(cliente):
    respuesta = cliente.get("/buscar", params={"q": "obras"})
    assert respuesta.status_code == 401


def test_buscar_devuelve_resultados(cliente, usuario):
    token = create_access_token(usuario)
    with patch("api.main.buscar_licitaciones", return_value=_RESULTADO_FALSO) as mock_buscar:
        respuesta = cliente.get(
            "/buscar",
            params={"q": "obras de accesibilidad", "k": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert respuesta.status_code == 200
    assert respuesta.json() == _RESULTADO_FALSO
    mock_buscar.assert_called_once_with("obras de accesibilidad", k=5)


@pytest.mark.parametrize("k", [0, 51])
def test_buscar_con_k_fuera_de_rango_da_422(cliente, usuario, k):
    token = create_access_token(usuario)
    respuesta = cliente.get(
        "/buscar",
        params={"q": "obras", "k": k},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 422


def test_buscar_propaga_error_como_503(cliente, usuario):
    token = create_access_token(usuario)
    with patch(
        "api.main.buscar_licitaciones",
        return_value={"error": "Búsqueda híbrida no disponible"},
    ):
        respuesta = cliente.get(
            "/buscar",
            params={"q": "obras"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert respuesta.status_code == 503


def test_buscar_no_consume_cuota(cliente, usuario):
    token = create_access_token(usuario)
    with patch("api.main.buscar_licitaciones", return_value=_RESULTADO_FALSO):
        cliente.get(
            "/buscar",
            params={"q": "obras"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert uso_actual(usuario.id) == 0
