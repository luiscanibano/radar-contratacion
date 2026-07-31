"""Auth: hash de contraseñas, JWT, tokens de un solo uso y dependencia
`usuario_actual`.

Casi stateless: `usuario_actual` decodifica el JWT sin tocar Postgres, pero
además compara el claim `sv` (sesion_version) contra la base de datos — una
única consulta indexada por PK. Es el coste de poder invalidar todas las
sesiones abiertas de un usuario (p. ej. tras un reset de contraseña) sin
mantener una lista de tokens revocados: basta con incrementar
`sesion_version` y cualquier JWT anterior deja de coincidir.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

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

# TTL de los tokens de un solo uso (ver crear_token_verificacion/crear_token_reset).
_TTL_VERIFICACION = timedelta(hours=24)
_TTL_RESET = timedelta(minutes=30)


@dataclass
class Usuario:
    id: int
    email: str
    # Con default para no romper los sitios (incl. tests) que construyen
    # Usuario(id=.., email=..) a mano sin pasar estos dos campos.
    email_verificado: bool = True
    sesion_version: int = 0


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
        "sv": usuario.sesion_version,
        "iat": ahora,
        "exp": ahora + settings.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def registrar_usuario(email: str, password: str, acepta_terminos: bool = False) -> Usuario:
    """Crea un usuario nuevo sin el email confirmado. Lanza ValueError si el
    email ya existe.

    `acepta_terminos` con default False para no romper las llamadas directas
    (fixtures de tests, scripts) que no pasan por el endpoint /auth/registro
    — ese endpoint es quien exige de verdad la aceptación (ver api/main.py).
    """
    password_hash = hash_password(password)
    with connect() as con:
        try:
            with con.cursor() as cur:
                cur.execute(
                    "insert into usuarios (email, password_hash, email_verificado,"
                    " terminos_aceptados_en)"
                    " values (%s, %s, false, %s) returning id",
                    (email, password_hash, datetime.now(UTC) if acepta_terminos else None),
                )
                (usuario_id,) = cur.fetchone()
            con.commit()
        except psycopg.errors.UniqueViolation as exc:
            con.rollback()
            raise ValueError(f"Ya existe un usuario con el email {email}") from exc
    return Usuario(id=usuario_id, email=email, email_verificado=False)


def autenticar_usuario(email: str, password: str) -> Usuario | None:
    """Verifica email + contraseña. Devuelve None si no coinciden.

    No comprueba `email_verificado`: esta función solo responde "¿la
    contraseña es correcta?" — bloquear el login de una cuenta sin confirmar
    es una decisión del endpoint (ver /auth/login en api/main.py), no de la
    verificación de credenciales en sí.
    """
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "select id, password_hash, email_verificado, sesion_version"
                " from usuarios where email = %s",
                (email,),
            )
            fila = cur.fetchone()
    if fila is None:
        return None
    usuario_id, password_hash, email_verificado, sesion_version = fila
    if not verify_password(password, password_hash):
        return None
    return Usuario(
        id=usuario_id,
        email=email,
        email_verificado=email_verificado,
        sesion_version=sesion_version,
    )


def buscar_usuario_por_email(email: str) -> Usuario | None:
    """Como obtener_usuario, pero por email (usado por /auth/reenviar-verificacion
    y /auth/olvide-password para saber si hay que mandar el email, sin exponer
    en la respuesta si la cuenta existe)."""
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "select id, email_verificado, sesion_version from usuarios where email = %s",
                (email,),
            )
            fila = cur.fetchone()
    if fila is None:
        return None
    usuario_id, email_verificado, sesion_version = fila
    return Usuario(
        id=usuario_id, email=email, email_verificado=email_verificado, sesion_version=sesion_version
    )


def obtener_usuario(usuario_id: int) -> Usuario | None:
    """Lee el estado actual de un usuario (usado tras canjear un token de un
    solo uso, para construir su JWT con datos frescos)."""
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "select email, email_verificado, sesion_version from usuarios where id = %s",
                (usuario_id,),
            )
            fila = cur.fetchone()
    if fila is None:
        return None
    email, email_verificado, sesion_version = fila
    return Usuario(
        id=usuario_id, email=email, email_verificado=email_verificado, sesion_version=sesion_version
    )


def marcar_email_verificado(usuario_id: int) -> None:
    with connect() as con:
        con.execute("update usuarios set email_verificado = true where id = %s", (usuario_id,))
        con.commit()


def cambiar_password(usuario_id: int, password: str) -> None:
    """Fija una contraseña nueva y revoca todas las sesiones abiertas de este
    usuario (incrementa sesion_version, ver usuario_actual)."""
    password_hash = hash_password(password)
    with connect() as con:
        con.execute(
            "update usuarios set password_hash = %s, sesion_version = sesion_version + 1"
            " where id = %s",
            (password_hash, usuario_id),
        )
        con.commit()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _crear_token(usuario_id: int, tipo: str, ttl: timedelta) -> str:
    token = secrets.token_urlsafe(32)
    expira_en = datetime.now(UTC) + ttl
    with connect() as con:
        con.execute(
            "insert into tokens_un_uso (token_hash, usuario_id, tipo, expira_en)"
            " values (%s, %s, %s, %s)",
            (_hash_token(token), usuario_id, tipo, expira_en),
        )
        con.commit()
    return token


def crear_token_verificacion(usuario_id: int) -> str:
    return _crear_token(usuario_id, "verificacion", _TTL_VERIFICACION)


def crear_token_reset(usuario_id: int) -> str:
    return _crear_token(usuario_id, "reset_password", _TTL_RESET)


def consumir_token(token: str, tipo: str) -> int | None:
    """Valida un token de un solo uso y lo marca gastado en el mismo UPDATE
    (evita que dos peticiones simultáneas lo canjeen dos veces). Devuelve el
    usuario_id o None si es inválido, ya usado o caducado."""
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "update tokens_un_uso set usado_en = now()"
                " where token_hash = %s and tipo = %s and usado_en is null and expira_en > now()"
                " returning usuario_id",
                (_hash_token(token), tipo),
            )
            fila = cur.fetchone()
        con.commit()
    return fila[0] if fila else None


def decode_token(token: str) -> Usuario:
    """Decodifica y valida un JWT propio. Lanza ValueError si es inválido/caducado."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise ValueError("Token inválido o caducado") from exc
    return Usuario(
        id=int(payload["sub"]), email=payload["email"], sesion_version=payload.get("sv", 0)
    )


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
        usuario = decode_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    with connect() as con:
        with con.cursor() as cur:
            cur.execute("select sesion_version from usuarios where id = %s", (usuario.id,))
            fila = cur.fetchone()
    if fila is None or fila[0] != usuario.sesion_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida, vuelve a iniciar sesión.",
        )
    return usuario
