"""Tests de la puerta de auth del servidor MCP montado en /mcp.

No valida el protocolo streamable-http completo (eso ya lo prueba el SDK
`mcp` en sus propios tests) — solo que `BearerAuthASGIMiddleware` deja pasar
peticiones con un JWT válido y bloquea las que no lo tienen, reutilizando
`api.auth.decode_token` igual que el resto de endpoints protegidos.
"""

from __future__ import annotations

import jwt
import pytest

from api.auth import Usuario, create_access_token, decode_token

# El TestClient viene de la fixture de sesión `cliente` (conftest.py): tiene
# que ser único por proceso porque el session manager del MCP solo admite un
# lifespan de por vida.


def test_decode_token_acepta_un_token_valido():
    usuario = decode_token(create_access_token(Usuario(id=1, email="a@b.com")))
    assert usuario == Usuario(id=1, email="a@b.com")


def test_decode_token_rechaza_secreto_distinto():
    otro_token = jwt.encode({"sub": "1", "email": "x@y.com"}, "otro-secreto", algorithm="HS256")
    with pytest.raises(ValueError):
        decode_token(otro_token)


def test_mcp_sin_cabecera_authorization_da_401(cliente):
    respuesta = cliente.get("/mcp")
    assert respuesta.status_code == 401


def test_mcp_con_token_invalido_da_401(cliente):
    respuesta = cliente.get("/mcp", headers={"Authorization": "Bearer no-soy-un-jwt"})
    assert respuesta.status_code == 401


def test_mcp_con_token_de_otro_secreto_da_401(cliente):
    otro_token = jwt.encode({"sub": "1", "email": "x@y.com"}, "otro-secreto", algorithm="HS256")
    respuesta = cliente.get("/mcp", headers={"Authorization": f"Bearer {otro_token}"})
    assert respuesta.status_code == 401


def test_mcp_con_token_valido_pasa_la_puerta_de_auth(cliente):
    token = create_access_token(Usuario(id=1, email="a@b.com"))
    respuesta = cliente.get("/mcp", headers={"Authorization": f"Bearer {token}"})
    # No validamos el protocolo MCP en sí (una GET sin sesión abierta es un
    # uso inválido del transporte streamable-http y dará error) — solo que
    # el middleware de auth no fue quien la bloqueó.
    assert respuesta.status_code != 401
