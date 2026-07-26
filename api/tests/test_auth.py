"""Tests de auth: hash/JWT (unitarios) + registro/login/protección (contra Postgres real).

Igual que search/ingest, la parte que toca Postgres asume la instancia local
levantada con `docker compose up -d postgres` (ver docker-compose.yml). Cada
test que escribe usuarios limpia su propia fila al terminar.
"""

from __future__ import annotations

import uuid

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.auth import (
    Usuario,
    autenticar_usuario,
    create_access_token,
    hash_password,
    registrar_usuario,
    usuario_actual,
    verify_password,
)
from api.db import connect, init_schema
from api.main import app
from api.settings import settings


@pytest.fixture(autouse=True, scope="module")
def _esquema():
    init_schema()


@pytest.fixture
def email():
    # Email único por test para no chocar entre ejecuciones concurrentes.
    correo = f"test-{uuid.uuid4().hex}@example.com"
    yield correo
    with connect() as con:
        con.execute("delete from usuarios where email = %s", (correo,))
        con.commit()


# --- hash / verify -----------------------------------------------------------


def test_hash_no_guarda_la_contraseña_en_claro():
    assert hash_password("secreto123") != "secreto123"


def test_verify_acepta_la_contraseña_correcta():
    assert verify_password("secreto123", hash_password("secreto123"))


def test_verify_rechaza_la_contraseña_incorrecta():
    assert not verify_password("otra-cosa", hash_password("secreto123"))


# --- JWT -----------------------------------------------------------------


def test_create_access_token_decodifica_con_los_claims_esperados():
    token = create_access_token(Usuario(id=42, email="a@b.com"))
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    assert payload["sub"] == "42"
    assert payload["email"] == "a@b.com"


def test_usuario_actual_rechaza_token_con_secreto_distinto():
    otro_token = jwt.encode({"sub": "1", "email": "x@y.com"}, "otro-secreto", algorithm="HS256")
    from fastapi.security import HTTPAuthorizationCredentials

    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=otro_token)
    with pytest.raises(HTTPException) as exc_info:
        usuario_actual(credenciales)
    assert exc_info.value.status_code == 401


# --- registro / login (Postgres real) ----------------------------------------


def test_registrar_usuario_y_autenticar(email):
    usuario = registrar_usuario(email, "contraseña-larga")
    assert usuario.email == email

    autenticado = autenticar_usuario(email, "contraseña-larga")
    assert autenticado is not None
    assert autenticado.id == usuario.id


def test_registrar_usuario_duplicado_lanza_value_error(email):
    registrar_usuario(email, "contraseña-larga")
    with pytest.raises(ValueError):
        registrar_usuario(email, "otra-contraseña")


def test_autenticar_con_contraseña_incorrecta_devuelve_none(email):
    registrar_usuario(email, "contraseña-larga")
    assert autenticar_usuario(email, "incorrecta") is None


def test_autenticar_usuario_inexistente_devuelve_none():
    assert autenticar_usuario("no-existe@example.com", "cualquiera") is None


# --- endpoints HTTP -----------------------------------------------------------


@pytest.fixture
def cliente():
    return TestClient(app)


def test_endpoint_registro_y_login(cliente, email):
    respuesta = cliente.post(
        "/auth/registro", json={"email": email, "password": "contraseña-larga"}
    )
    assert respuesta.status_code == 201
    assert "access_token" in respuesta.json()

    respuesta = cliente.post("/auth/login", json={"email": email, "password": "contraseña-larga"})
    assert respuesta.status_code == 200
    token = respuesta.json()["access_token"]

    respuesta = cliente.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == email


def test_endpoint_login_con_credenciales_incorrectas_da_401(cliente, email):
    registrar_usuario(email, "contraseña-larga")
    respuesta = cliente.post("/auth/login", json={"email": email, "password": "incorrecta"})
    assert respuesta.status_code == 401


def test_preguntar_sin_token_da_401(cliente):
    respuesta = cliente.post("/preguntar", json={"texto": "hola"})
    assert respuesta.status_code == 401


def test_consultar_sin_token_da_401(cliente):
    respuesta = cliente.post("/consultar", json={"sql": "select 1"})
    assert respuesta.status_code == 401
