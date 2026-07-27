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
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.db import connect
from api.settings import settings

_hasher = PasswordHasher()
_bearer = HTTPBearer()


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


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(_bearer),  # noqa: B008
) -> Usuario:
    """Dependencia de FastAPI: exige `Authorization: Bearer <token>` válido."""
    try:
        return decode_token(credenciales.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
