"""API FastAPI del Radar de Contratación Pública."""

from __future__ import annotations

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

from api.agent.graph import responder
from api.agent.tools import run_readonly_sql
from api.observabilidad import emitir

app = FastAPI(title="Radar de Contratación Pública", version="0.1.0")


class Pregunta(BaseModel):
    texto: str


class Consulta(BaseModel):
    sql: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/preguntar")
def preguntar(pregunta: Pregunta, tareas: BackgroundTasks) -> dict[str, str]:
    """Endpoint del analista conversacional (lenguaje natural).

    La traza se emite en segundo plano: el usuario no debe esperar a que
    Langfuse conteste para recibir su respuesta.
    """
    texto, traza = responder(pregunta.texto)
    tareas.add_task(emitir, traza)
    return {"respuesta": texto}


@app.post("/consultar")
def consultar(consulta: Consulta) -> dict:
    """Ejecuta SQL de solo lectura directamente (para debug / usuarios avanzados)."""
    return run_readonly_sql(consulta.sql)
