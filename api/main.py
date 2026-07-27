"""API FastAPI del Radar de Contratación Pública."""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.agent.graph import responder
from api.agent.tools import run_readonly_sql
from api.alertas import borrar_alerta, crear_alerta, listar_alertas
from api.auth import (
    Usuario,
    autenticar_usuario,
    create_access_token,
    registrar_usuario,
    usuario_actual,
)
from api.billing import crear_checkout_session, procesar_webhook
from api.cuota import consumir_cuota
from api.observabilidad import emitir
from mcp_server.auth_middleware import BearerAuthASGIMiddleware
from mcp_server.server import mcp

_mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # El StreamableHTTPSessionManager del MCP montado abajo necesita su propio
    # lifespan activo (crea/limpia sus tareas de sesión) — `app.mount(...)` no
    # lo propaga solo, hay que entrarlo a mano junto al de la API.
    async with AsyncExitStack() as pila:
        await pila.enter_async_context(_mcp_app.router.lifespan_context(app))
        yield


app = FastAPI(title="Radar de Contratación Pública", version="0.1.0", lifespan=_lifespan)
app.mount("/mcp", BearerAuthASGIMiddleware(_mcp_app))

# Interfaz web mínima: HTML estático autocontenido (sin framework JS), servido
# por la propia API. Fuera del esquema OpenAPI para que /docs siga siendo
# solo la referencia de la API.
_STATIC = Path(__file__).parent / "static"


@app.get("/", include_in_schema=False)
def portada() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.get("/app", include_in_schema=False)
def panel() -> FileResponse:
    return FileResponse(_STATIC / "app.html")


@app.get("/billing/exito", include_in_schema=False)
def billing_exito() -> FileResponse:
    """Página de retorno de Stripe Checkout (ver billing_success_url en settings)."""
    return FileResponse(_STATIC / "billing_exito.html")


@app.get("/billing/cancelado", include_in_schema=False)
def billing_cancelado() -> FileResponse:
    """Página de retorno de Stripe Checkout (ver billing_cancel_url en settings)."""
    return FileResponse(_STATIC / "billing_cancelado.html")


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


class PlanSolicitado(BaseModel):
    plan: str


class AlertaSolicitada(BaseModel):
    consulta_texto: str


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
    if not consumir_cuota(usuario.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Cuota mensual de preguntas agotada. Amplíala en /billing/checkout.",
        )
    texto, traza = responder(pregunta.texto)
    tareas.add_task(emitir, traza)
    return {"respuesta": texto}


@app.post("/consultar")
def consultar(consulta: Consulta, usuario: Usuario = Depends(usuario_actual)) -> dict:  # noqa: B008
    """Ejecuta SQL de solo lectura directamente (para debug / usuarios avanzados)."""
    return run_readonly_sql(consulta.sql)


@app.post("/billing/checkout")
def checkout(
    solicitud: PlanSolicitado,
    usuario: Usuario = Depends(usuario_actual),  # noqa: B008
) -> dict[str, str]:
    """Crea una sesión de Stripe Checkout para suscribirse a un plan de pago."""
    try:
        url = crear_checkout_session(usuario, solicitud.plan)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"checkout_url": url}


@app.post("/billing/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def webhook(request: Request, stripe_signature: str = Header(default="")) -> None:
    """Recibe los eventos de suscripción de Stripe (firma verificada en api.billing)."""
    payload = await request.body()
    try:
        procesar_webhook(payload, stripe_signature)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/alertas", status_code=status.HTTP_201_CREATED)
def crear_alerta_endpoint(
    solicitud: AlertaSolicitada,
    usuario: Usuario = Depends(usuario_actual),  # noqa: B008
) -> dict[str, int]:
    return {"id": crear_alerta(usuario.id, solicitud.consulta_texto)}


@app.get("/alertas")
def listar_alertas_endpoint(usuario: Usuario = Depends(usuario_actual)) -> list[dict]:  # noqa: B008
    return listar_alertas(usuario.id)


@app.delete("/alertas/{alerta_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_alerta_endpoint(
    alerta_id: int,
    usuario: Usuario = Depends(usuario_actual),  # noqa: B008
) -> None:
    if not borrar_alerta(usuario.id, alerta_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada")
