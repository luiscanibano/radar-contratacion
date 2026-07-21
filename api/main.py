"""API FastAPI del Radar de Contratación Pública."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from api.agent.graph import answer
from api.agent.tools import run_readonly_sql

app = FastAPI(title="Radar de Contratación Pública", version="0.1.0")


class Pregunta(BaseModel):
    texto: str


class Consulta(BaseModel):
    sql: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/preguntar")
def preguntar(pregunta: Pregunta) -> dict[str, str]:
    """Endpoint del analista conversacional (lenguaje natural)."""
    return {"respuesta": answer(pregunta.texto)}


@app.post("/consultar")
def consultar(consulta: Consulta) -> dict:
    """Ejecuta SQL de solo lectura directamente (para debug / usuarios avanzados)."""
    return run_readonly_sql(consulta.sql)
