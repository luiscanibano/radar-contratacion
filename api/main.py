"""API FastAPI del Radar de Contratación Pública."""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from api.agent.graph import responder
from api.agent.tools import buscar_licitaciones, run_readonly_sql
from api.alertas import borrar_alerta, crear_alerta, listar_alertas
from api.auth import (
    Usuario,
    autenticar_usuario,
    borrar_cookie_sesion,
    create_access_token,
    fijar_cookie_sesion,
    registrar_usuario,
    usuario_actual,
)
from api.billing import crear_checkout_session, crear_portal_session, plan_actual, procesar_webhook
from api.cuota import consumir_cuota, uso_actual
from api.observabilidad import emitir
from api.rate_limit import limitar
from mcp_server.auth_middleware import BearerAuthASGIMiddleware
from mcp_server.server import mcp

# Límites de intentos en los endpoints de auth: frenan fuerza bruta y
# credential stuffing sin necesitar un backend compartido (ver api/rate_limit.py).
_limite_login = limitar("login", intentos=10, ventana_segundos=300)
_limite_registro = limitar("registro", intentos=5, ventana_segundos=3600)

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

# /docs y /redoc (Swagger UI / ReDoc) cargan sus assets desde un CDN
# (jsdelivr) por defecto en FastAPI: una CSP estricta de origen propio los
# rompería. Son referencia para desarrolladores, no la interfaz de usuario
# final, así que quedan fuera de la CSP en vez de aflojarla para todo el sitio.
_RUTAS_SIN_CSP_ESTRICTA = {"/docs", "/redoc", "/openapi.json"}

_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "object-src 'none'"
)


@app.middleware("http")
async def _cabeceras_seguridad(request: Request, call_next):
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    respuesta.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    # El navegador ignora esta cabecera si la respuesta no llegó por HTTPS
    # (p. ej. en desarrollo local), así que es seguro mandarla siempre.
    respuesta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path not in _RUTAS_SIN_CSP_ESTRICTA:
        respuesta.headers["Content-Security-Policy"] = _CSP
    return respuesta


# Interfaz web: build de producción de web/ (Vite + React), servida por la
# propia API. Fuera del esquema OpenAPI para que /docs siga siendo solo la
# referencia de la API.
_STATIC = Path(__file__).parent / "static"

# JS/CSS/fuentes con hash que genera el build de Vite (web/dist/assets). En
# desarrollo local no existe (se usa el dev server de Vite, no esta API, para
# servir la interfaz — ver web/vite.config.ts); solo lo monta si ya se ha
# copiado el build, para que la app arranque igual sin él.
if (_STATIC / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=_STATIC / "assets"), name="assets")


@app.get("/favicon.svg", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(_STATIC / "favicon.svg")


@app.get("/theme-init.js", include_in_schema=False)
def theme_init_js() -> FileResponse:
    return FileResponse(_STATIC / "theme-init.js", media_type="application/javascript")


@app.get("/", include_in_schema=False)
def portada() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.get("/app", include_in_schema=False)
def panel() -> FileResponse:
    return FileResponse(_STATIC / "app" / "index.html")


@app.get("/billing/exito", include_in_schema=False)
def billing_exito() -> FileResponse:
    """Página de retorno de Stripe Checkout (ver billing_success_url en settings)."""
    return FileResponse(_STATIC / "billing" / "exito" / "index.html")


@app.get("/billing/cancelado", include_in_schema=False)
def billing_cancelado() -> FileResponse:
    """Página de retorno de Stripe Checkout (ver billing_cancel_url en settings)."""
    return FileResponse(_STATIC / "billing" / "cancelado" / "index.html")


@app.get("/legal", include_in_schema=False)
def legal() -> FileResponse:
    return FileResponse(_STATIC / "legal" / "index.html")


class Pregunta(BaseModel):
    texto: str


class Consulta(BaseModel):
    sql: str


class Credenciales(BaseModel):
    """Login: el email no se valida como EmailStr a propósito — debe seguir
    aceptando cuentas ya registradas antes de que existiera esa validación."""

    email: str
    password: str


class CredencialesRegistro(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


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


@app.post(
    "/auth/registro",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_limite_registro)],
)
def registro(credenciales: CredencialesRegistro, response: Response) -> Token:
    try:
        usuario = registrar_usuario(credenciales.email, credenciales.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    token = create_access_token(usuario)
    fijar_cookie_sesion(response, token)
    return Token(access_token=token)


@app.post("/auth/login", dependencies=[Depends(_limite_login)])
def login(credenciales: Credenciales, response: Response) -> Token:
    usuario = autenticar_usuario(credenciales.email, credenciales.password)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    token = create_access_token(usuario)
    fijar_cookie_sesion(response, token)
    return Token(access_token=token)


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    borrar_cookie_sesion(response)


@app.post("/auth/mcp-token")
def mcp_token(usuario: Usuario = Depends(usuario_actual)) -> Token:  # noqa: B008
    """Emite un token nuevo para pegar en un cliente MCP externo (ver
    /mcp): a diferencia de la cookie de sesión, este token sí viaja fuera
    del navegador, así que se entrega bajo demanda en el cuerpo de la
    respuesta en vez de guardarse en ningún sitio accesible por JS."""
    return Token(access_token=create_access_token(usuario))


@app.get("/auth/me")
def me(usuario: Usuario = Depends(usuario_actual)) -> dict[str, str | int]:  # noqa: B008
    return {"id": usuario.id, "email": usuario.email}


@app.get("/me/plan")
def mi_plan(usuario: Usuario = Depends(usuario_actual)) -> dict:  # noqa: B008
    """Plan vigente del usuario y su consumo de preguntas este mes."""
    plan = plan_actual(usuario.id)
    usadas = uso_actual(usuario.id)
    restantes = None if plan.cuota is None else max(plan.cuota - usadas, 0)
    return {"plan": plan.nombre, "cuota": plan.cuota, "usadas": usadas, "restantes": restantes}


@app.get("/buscar")
def buscar(
    q: str = Query(min_length=1),
    k: int = Query(default=10, ge=1, le=50),
    usuario: Usuario = Depends(usuario_actual),  # noqa: B008
) -> dict:
    """Búsqueda híbrida de licitaciones (léxica + vectorial). No consume
    cuota de preguntas: el coste es un embedding local, no una llamada al LLM.
    """
    resultado = buscar_licitaciones(q, k=k)
    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=resultado["error"]
        )
    return resultado


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


@app.post("/billing/portal")
def portal(usuario: Usuario = Depends(usuario_actual)) -> dict[str, str]:  # noqa: B008
    """Crea una sesión del Billing Portal de Stripe para gestionar/cancelar la suscripción."""
    try:
        url = crear_portal_session(usuario)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"portal_url": url}


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
