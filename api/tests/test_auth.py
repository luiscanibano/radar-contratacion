"""Tests de auth: hash/JWT (unitarios) + registro/login/verificación/reset/protección
(contra Postgres real).

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
    cambiar_password,
    consumir_token,
    crear_token_reset,
    crear_token_verificacion,
    create_access_token,
    hash_password,
    marcar_email_verificado,
    obtener_usuario,
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
    token = create_access_token(Usuario(id=42, email="a@b.com", sesion_version=3))
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    assert payload["sub"] == "42"
    assert payload["email"] == "a@b.com"
    assert payload["sv"] == 3


# --- registro / login (Postgres real) ----------------------------------------


def test_registrar_usuario_crea_la_cuenta_sin_confirmar(email):
    usuario = registrar_usuario(email, "contraseña-larga")
    assert usuario.email == email
    assert usuario.email_verificado is False

    autenticado = autenticar_usuario(email, "contraseña-larga")
    assert autenticado is not None
    assert autenticado.id == usuario.id
    assert autenticado.email_verificado is False


def test_marcar_email_verificado_activa_la_cuenta(email):
    usuario = registrar_usuario(email, "contraseña-larga")
    marcar_email_verificado(usuario.id)
    assert autenticar_usuario(email, "contraseña-larga").email_verificado is True


def test_registrar_usuario_duplicado_lanza_value_error(email):
    registrar_usuario(email, "contraseña-larga")
    with pytest.raises(ValueError):
        registrar_usuario(email, "otra-contraseña")


def test_autenticar_con_contraseña_incorrecta_devuelve_none(email):
    registrar_usuario(email, "contraseña-larga")
    assert autenticar_usuario(email, "incorrecta") is None


def test_autenticar_usuario_inexistente_devuelve_none():
    assert autenticar_usuario("no-existe@example.com", "cualquiera") is None


# --- tokens de un solo uso (verificación / reset) -----------------------------


def test_consumir_token_valido_devuelve_el_usuario_y_no_se_puede_reusar(email):
    usuario = registrar_usuario(email, "contraseña-larga")
    token = crear_token_verificacion(usuario.id)
    assert consumir_token(token, "verificacion") == usuario.id
    assert consumir_token(token, "verificacion") is None  # ya usado


def test_consumir_token_con_tipo_distinto_no_sirve(email):
    usuario = registrar_usuario(email, "contraseña-larga")
    token = crear_token_verificacion(usuario.id)
    assert consumir_token(token, "reset_password") is None


def test_consumir_token_inexistente_devuelve_none():
    assert consumir_token("no-existe", "verificacion") is None


def test_cambiar_password_incrementa_sesion_version_y_permite_login_con_la_nueva(email):
    usuario = registrar_usuario(email, "contraseña-larga")
    cambiar_password(usuario.id, "contraseña-nueva-larga")
    assert obtener_usuario(usuario.id).sesion_version == usuario.sesion_version + 1
    assert autenticar_usuario(email, "contraseña-nueva-larga") is not None
    assert autenticar_usuario(email, "contraseña-larga") is None


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


def test_endpoint_registro_no_abre_sesion_hasta_confirmar_el_email(cliente, email):
    respuesta = cliente.post(
        "/auth/registro", json={"email": email, "password": "contraseña-larga"}
    )
    assert respuesta.status_code == 201
    assert "mensaje" in respuesta.json()
    assert respuesta.cookies.get(SESSION_COOKIE_NAME) is None

    # login bloqueado hasta confirmar
    bloqueado = cliente.post("/auth/login", json={"email": email, "password": "contraseña-larga"})
    assert bloqueado.status_code == 403

    # simula el click del enlace del email
    with connect() as con:
        with con.cursor() as cur:
            cur.execute("select id from usuarios where email = %s", (email,))
            (usuario_id,) = cur.fetchone()
    token = crear_token_verificacion(usuario_id)
    verificacion = cliente.get(f"/auth/verificar?token={token}", follow_redirects=False)
    assert verificacion.status_code in (302, 307)
    assert verificacion.cookies.get(SESSION_COOKIE_NAME) is not None

    cliente.cookies.clear()
    login = cliente.post("/auth/login", json={"email": email, "password": "contraseña-larga"})
    assert login.status_code == 200
    assert login.cookies.get(SESSION_COOKIE_NAME) is not None

    me = cliente.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_login_con_email_sin_verificar_da_403(cliente, email):
    registrar_usuario(email, "contraseña-larga")
    respuesta = cliente.post("/auth/login", json={"email": email, "password": "contraseña-larga"})
    assert respuesta.status_code == 403


def test_verificar_con_token_invalido_no_abre_sesion(cliente):
    respuesta = cliente.get("/auth/verificar?token=no-existe", follow_redirects=False)
    assert respuesta.status_code in (302, 307)
    assert respuesta.headers["location"] == "/app?verificado=0"
    assert respuesta.cookies.get(SESSION_COOKIE_NAME) is None


def test_verificar_con_token_ya_usado_falla_la_segunda_vez(cliente, email):
    usuario = registrar_usuario(email, "contraseña-larga")
    token = crear_token_verificacion(usuario.id)
    primera = cliente.get(f"/auth/verificar?token={token}", follow_redirects=False)
    assert primera.cookies.get(SESSION_COOKIE_NAME) is not None

    cliente.cookies.clear()
    segunda = cliente.get(f"/auth/verificar?token={token}", follow_redirects=False)
    assert segunda.cookies.get(SESSION_COOKIE_NAME) is None


def test_reenviar_verificacion_responde_igual_exista_o_no_la_cuenta(cliente, email):
    registrar_usuario(email, "contraseña-larga")
    con_cuenta = cliente.post("/auth/reenviar-verificacion", json={"email": email})
    sin_cuenta = cliente.post("/auth/reenviar-verificacion", json={"email": f"no-existe-{email}"})
    assert con_cuenta.status_code == 200
    assert sin_cuenta.status_code == 200
    assert con_cuenta.json() == sin_cuenta.json()


def test_olvide_password_responde_igual_exista_o_no_la_cuenta(cliente, email):
    registrar_usuario(email, "contraseña-larga")
    con_cuenta = cliente.post("/auth/olvide-password", json={"email": email})
    sin_cuenta = cliente.post("/auth/olvide-password", json={"email": f"no-existe-{email}"})
    assert con_cuenta.status_code == 200
    assert sin_cuenta.status_code == 200
    assert con_cuenta.json() == sin_cuenta.json()


def test_resetear_password_permite_login_con_la_contraseña_nueva(cliente, email):
    usuario = registrar_usuario(email, "contraseña-larga")
    marcar_email_verificado(usuario.id)
    token = crear_token_reset(usuario.id)

    respuesta = cliente.post(
        "/auth/resetear-password", json={"token": token, "password": "contraseña-nueva-larga"}
    )
    assert respuesta.status_code == 200
    assert respuesta.cookies.get(SESSION_COOKIE_NAME) is not None

    cliente.cookies.clear()
    login = cliente.post("/auth/login", json={"email": email, "password": "contraseña-nueva-larga"})
    assert login.status_code == 200


def test_resetear_password_invalida_las_sesiones_abiertas_antes_del_reset(cliente, email):
    usuario = registrar_usuario(email, "contraseña-larga")
    marcar_email_verificado(usuario.id)
    cliente.post("/auth/login", json={"email": email, "password": "contraseña-larga"})
    assert cliente.get("/auth/me").status_code == 200

    otro_cliente = TestClient(app, base_url="https://testserver")
    token = crear_token_reset(usuario.id)
    reset = otro_cliente.post(
        "/auth/resetear-password", json={"token": token, "password": "contraseña-nueva-larga"}
    )
    assert reset.status_code == 200

    # la cookie de la sesión abierta antes del reset ya no sirve
    assert cliente.get("/auth/me").status_code == 401


def test_resetear_password_con_token_invalido_da_400(cliente):
    respuesta = cliente.post(
        "/auth/resetear-password", json={"token": "no-existe", "password": "contraseña-larga"}
    )
    assert respuesta.status_code == 400


def test_olvide_password_con_demasiadas_peticiones_da_429(cliente, email):
    cabeceras = {"X-Forwarded-For": _ip_unica()}
    for _ in range(5):
        respuesta = cliente.post("/auth/olvide-password", json={"email": email}, headers=cabeceras)
        assert respuesta.status_code == 200
    respuesta = cliente.post("/auth/olvide-password", json={"email": email}, headers=cabeceras)
    assert respuesta.status_code == 429


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
    usuario = registrar_usuario(email, "contraseña-larga")
    marcar_email_verificado(usuario.id)
    cliente.post("/auth/login", json={"email": email, "password": "contraseña-larga"})
    assert cliente.get("/auth/me").status_code == 200

    respuesta = cliente.post("/auth/logout")
    assert respuesta.status_code == 204
    assert cliente.get("/auth/me").status_code == 401


def test_mcp_token_funciona_como_bearer_sin_cookie(email):
    usuario = registrar_usuario(email, "contraseña-larga")
    marcar_email_verificado(usuario.id)
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
    assert respuesta.json()["email"] == usuario.email


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
