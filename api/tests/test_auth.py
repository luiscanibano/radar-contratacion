"""Tests de auth: hash/JWT (unitarios) + registro/login/protección (contra Postgres real).

Igual que search/ingest, la parte que toca Postgres asume la instancia local
levantada con `docker compose up -d postgres` (ver docker-compose.yml). Cada
test que escribe usuarios limpia su propia fila al terminar.
"""

from __future__ import annotations

import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

from api.auth import (
    SESSION_COOKIE_NAME,
    Usuario,
    autenticar_usuario,
    create_access_token,
    hash_password,
    registrar_usuario,
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
    # base_url https: la cookie de sesión lleva Secure, y el jar de cookies
    # de httpx (como cualquier navegador) no la reenvía en peticiones
    # posteriores si cree que está hablando en claro por http. No sale a la
    # red de verdad — sigue siendo el transporte ASGI in-process.
    return TestClient(app, base_url="https://testserver")


def _ip_unica() -> str:
    # Cabecera X-Forwarded-For con una IP de ejemplo (RFC 5737, TEST-NET-3)
    # distinta por test: aísla el contador de rate limiting (api/rate_limit.py)
    # de los demás tests que comparten la IP por defecto del TestClient.
    octeto = uuid.uuid4().int % 254 + 1
    return f"203.0.113.{octeto}"


def test_endpoint_registro_y_login(cliente, email):
    respuesta = cliente.post(
        "/auth/registro", json={"email": email, "password": "contraseña-larga"}
    )
    assert respuesta.status_code == 201
    assert "access_token" in respuesta.json()
    cookie = respuesta.cookies.get(SESSION_COOKIE_NAME)
    assert cookie is not None

    cliente.cookies.clear()
    respuesta = cliente.post("/auth/login", json={"email": email, "password": "contraseña-larga"})
    assert respuesta.status_code == 200
    assert respuesta.cookies.get(SESSION_COOKIE_NAME) is not None

    # La cookie httpOnly la reenvía el propio cliente (como un navegador):
    # /auth/me no necesita ninguna cabecera Authorization.
    respuesta = cliente.get("/auth/me")
    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == email


def test_endpoint_login_con_credenciales_incorrectas_da_401(cliente, email):
    registrar_usuario(email, "contraseña-larga")
    respuesta = cliente.post(
        "/auth/login",
        json={"email": email, "password": "incorrecta"},
        headers={"X-Forwarded-For": _ip_unica()},
    )
    assert respuesta.status_code == 401


def test_registro_rechaza_contraseña_corta(cliente):
    respuesta = cliente.post(
        "/auth/registro",
        json={"email": f"{uuid.uuid4().hex}@example.com", "password": "corta12"},
    )
    assert respuesta.status_code == 422


def test_registro_rechaza_email_con_formato_invalido(cliente):
    respuesta = cliente.post(
        "/auth/registro",
        json={"email": "no-es-un-email", "password": "contraseña-larga"},
    )
    assert respuesta.status_code == 422


def test_logout_borra_la_cookie_de_sesion(cliente, email):
    registrar_usuario(email, "contraseña-larga")
    cliente.post("/auth/login", json={"email": email, "password": "contraseña-larga"})
    assert cliente.get("/auth/me").status_code == 200

    respuesta = cliente.post("/auth/logout")
    assert respuesta.status_code == 204
    assert cliente.get("/auth/me").status_code == 401


def test_mcp_token_funciona_como_bearer_sin_cookie(email):
    registrado = registrar_usuario(email, "contraseña-larga")
    cliente_con_cookie = TestClient(app, base_url="https://testserver")
    cliente_con_cookie.post("/auth/login", json={"email": email, "password": "contraseña-larga"})

    respuesta = cliente_con_cookie.post("/auth/mcp-token")
    assert respuesta.status_code == 200
    token = respuesta.json()["access_token"]

    # Cliente nuevo, sin ninguna cookie: el token de /auth/mcp-token debe
    # bastar por sí solo como Authorization: Bearer (uso desde MCP/API).
    cliente_sin_cookie = TestClient(app, base_url="https://testserver")
    respuesta = cliente_sin_cookie.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == registrado.email


def test_login_con_cabecera_authorization_invalida_da_401(cliente):
    respuesta = cliente.get("/auth/me", headers={"Authorization": "Bearer token-falso"})
    assert respuesta.status_code == 401


def test_preguntar_sin_token_da_401(cliente):
    respuesta = cliente.post("/preguntar", json={"texto": "hola"})
    assert respuesta.status_code == 401


def test_consultar_sin_token_da_401(cliente):
    respuesta = cliente.post("/consultar", json={"sql": "select 1"})
    assert respuesta.status_code == 401


def test_login_con_demasiados_intentos_da_429(cliente, email):
    registrar_usuario(email, "contraseña-larga")
    cabeceras = {"X-Forwarded-For": _ip_unica()}
    for _ in range(10):
        respuesta = cliente.post(
            "/auth/login",
            json={"email": email, "password": "incorrecta"},
            headers=cabeceras,
        )
        assert respuesta.status_code == 401
    respuesta = cliente.post(
        "/auth/login",
        json={"email": email, "password": "incorrecta"},
        headers=cabeceras,
    )
    assert respuesta.status_code == 429


def test_cabeceras_de_seguridad_presentes(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.headers["x-content-type-options"] == "nosniff"
    assert respuesta.headers["x-frame-options"] == "DENY"
    assert "Content-Security-Policy" in respuesta.headers
    assert "Strict-Transport-Security" in respuesta.headers


def test_docs_no_lleva_csp_estricta_por_el_cdn_de_swagger(cliente):
    respuesta = cliente.get("/docs")
    assert "content-security-policy" not in {k.lower() for k in respuesta.headers.keys()}
