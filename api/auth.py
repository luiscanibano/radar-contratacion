"""Auth: hash de contraseñas, JWT y dependencia `usuario_actual`.

Stateless: `usuario_actual` decodifica el JWT y no vuelve a tocar Postgres en
cada petición protegida (los claims llevan id + email, que es cuanto necesita
el resto de la API). Solo se toca la base de datos al registrar o hacer login.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import jwt
import psycopg
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.db import connect
from api.settings import settings

_hasher = PasswordHasher()
# auto_error=False: la cabecera Authorization es solo el *fallback* de
# usuario_actual (MCP, API, clientes que no son el navegador) — la interfaz
# web se autentica con la cookie de sesión, así que su ausencia no debe dar
# 403 antes de haber podido mirar la cookie.
_bearer = HTTPBearer(auto_error=False)

# Nombre de la cookie de sesión de la interfaz web. httpOnly (JS no puede
# leerla, así que un XSS no puede robarla) + Secure (solo viaja por HTTPS) +
# SameSite=Strict (el navegador nunca la manda en peticiones iniciadas desde
# otro sitio, lo que también cubre CSRF sin necesitar un token aparte: esta
# app no tiene ningún caso de uso legítimo que dependa de mandarla
# cross-site). Vive el mismo tiempo que el JWT que contiene.
SESSION_COOKIE_NAME = "radar_session"
_MAX_AGE_SESION = settings.jwt_expire_minutes * 60


@dataclass
class Usuario:
    id: int
    email: str


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_access_token(usuario: Usuario) -> str:
    ahora = int(time.time())
    payload = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "iat": ahora,
        "exp": ahora + settings.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def registrar_usuario(email: str, password: str) -> Usuario:
    """Crea un usuario nuevo. Lanza ValueError si el email ya existe."""
    password_hash = hash_password(password)
    with connect() as con:
        try:
            with con.cursor() as cur:
                cur.execute(
                    "insert into usuarios (email, password_hash) values (%s, %s) returning id",
                    (email, password_hash),
                )
                (usuario_id,) = cur.fetchone()
            con.commit()
        except psycopg.errors.UniqueViolation as exc:
            con.rollback()
            raise ValueError(f"Ya existe un usuario con el email {email}") from exc
    return Usuario(id=usuario_id, email=email)


def autenticar_usuario(email: str, password: str) -> Usuario | None:
    """Verifica email + contraseña. Devuelve None si no coinciden."""
    with connect() as con:
        with con.cursor() as cur:
            cur.execute("select id, password_hash from usuarios where email = %s", (email,))
            fila = cur.fetchone()
    if fila is None:
        return None
    usuario_id, password_hash = fila
    if not verify_password(password, password_hash):
        return None
    return Usuario(id=usuario_id, email=email)


def decode_token(token: str) -> Usuario:
    """Decodifica y valida un JWT propio. Lanza ValueError si es inválido/caducado."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise ValueError("Token inválido o caducado") from exc
    return Usuario(id=int(payload["sub"]), email=payload["email"])


def fijar_cookie_sesion(response: Response, token: str) -> None:
    """Fija la cookie de sesión de la interfaz web tras login/registro."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=_MAX_AGE_SESION,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )


def borrar_cookie_sesion(response: Response) -> None:
    """Cierra la sesión de la interfaz web (logout)."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


def usuario_actual(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008
) -> Usuario:
    """Dependencia de FastAPI: exige sesión válida.

    Acepta la cookie httpOnly de la interfaz web o, si no hay cookie, una
    cabecera `Authorization: Bearer <token>` — así los mismos endpoints
    sirven de API para el token MCP (ver /auth/mcp-token) sin que la web
    tenga que exponer el JWT a JavaScript.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME) or (
        credenciales.credentials if credenciales else None
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )
    try:
        return decode_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
