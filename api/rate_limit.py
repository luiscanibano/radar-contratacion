"""Rate limiting en memoria para endpoints sensibles (login, registro).

Ventana deslizante por IP + ruta. Un único proceso `api` en el VPS (ver
docker-compose.yml), así que no hace falta un backend compartido (Redis) —
bastaría con reiniciar el proceso para resetear los contadores, y eso ya pasa
en cada despliegue.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

# ruta -> IP -> timestamps de intentos dentro de la ventana
_intentos: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))


def _ip_cliente(request: Request) -> str:
    # Caddy (reverse_proxy) añade X-Forwarded-For con la IP real del
    # visitante; sin proxy delante (dev local), cae a la IP de la conexión.
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.client.host if request.client else "desconocido"


def limitar(clave: str, *, intentos: int, ventana_segundos: float):
    """Devuelve una dependencia de FastAPI que limita `intentos` por IP y
    `ventana_segundos` para la ruta identificada por `clave`."""

    def dependencia(request: Request) -> None:
        ahora = time.monotonic()
        ip = _ip_cliente(request)
        historial = _intentos[clave][ip]
        historial[:] = [t for t in historial if ahora - t < ventana_segundos]
        if len(historial) >= intentos:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos. Espera unos minutos y vuelve a intentarlo.",
            )
        historial.append(ahora)

    return dependencia
