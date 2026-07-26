"""API FastAPI del Radar de Contratación Pública."""

from __future__ import annotations

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

from api.agent.graph import responder
from api.agent.tools import run_readonly_sql
from api.auth import (
    Usuario,
    autenticar_usuario,
    create_access_token,
    registrar_usuario,
    usuario_actual,
)
from api.observabilidad import emitir

app = FastAPI(title="Radar de Contratación Pública", version="0.1.0")


class Pregunta(BaseModel):
    texto: str


class Consulta(BaseModel):
    sql: str


class Credenciales(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/registro", status_code=status.HTTP_201_CREATED)
def registro(credenciales: Credenciales) -> Token:
    try:
        usuario = registrar_usuario(credenciales.email, credenciales.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Token(access_token=create_access_token(usuario))


@app.post("/auth/login")
def login(credenciales: Credenciales) -> Token:
    usuario = autenticar_usuario(credenciales.email, credenciales.password)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    return Token(access_token=create_access_token(usuario))


@app.get("/auth/me")
def me(usuario: Usuario = Depends(usuario_actual)) -> dict[str, str | int]:  # noqa: B008
    return {"id": usuario.id, "email": usuario.email}


@app.post("/preguntar")
def preguntar(
    pregunta: Pregunta,
    tareas: BackgroundTasks,
    usuario: Usuario = Depends(usuario_actual),  # noqa: B008
) -> dict[str, str]:
    """Endpoint del analista conversacional (lenguaje natural).

    La traza se emite en segundo plano: el usuario no debe esperar a que
    Langfuse conteste para recibir su respuesta.
    """
    texto, traza = responder(pregunta.texto)
    tareas.add_task(emitir, traza)
    return {"respuesta": texto}


@app.post("/consultar")
def consultar(consulta: Consulta, usuario: Usuario = Depends(usuario_actual)) -> dict:  # noqa: B008
    """Ejecuta SQL de solo lectura directamente (para debug / usuarios avanzados)."""
    return run_readonly_sql(consulta.sql)
