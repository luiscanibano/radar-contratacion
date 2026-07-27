"""Middleware ASGI que exige el mismo JWT que el resto de la API.

ASGI puro (no `Starlette.BaseHTTPMiddleware`) para no romper el streaming del
transporte streamable-http del servidor MCP. Reutiliza `api.auth.decode_token`
en vez de duplicar la validación del JWT.
"""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from api.auth import decode_token


class BearerAuthASGIMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        cabecera = headers.get(b"authorization", b"").decode()
        token = cabecera.removeprefix("Bearer ").strip() if cabecera.startswith("Bearer ") else ""

        if not token:
            await self._no_autorizado(send, "Falta la cabecera Authorization: Bearer <token>")
            return
        try:
            decode_token(token)
        except ValueError as exc:
            await self._no_autorizado(send, str(exc))
            return

        await self.app(scope, receive, send)

    @staticmethod
    async def _no_autorizado(send: Send, detalle: str) -> None:
        cuerpo = json.dumps({"detail": detalle}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": cuerpo})
