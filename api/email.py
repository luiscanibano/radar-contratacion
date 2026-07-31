"""Envío de emails transaccionales vía la API REST de Resend.

Cliente HTTP directo con httpx (ya es dependencia raíz del proyecto) en vez
del SDK oficial de Resend: la API es un único POST y no compensa añadir una
dependencia más para eso.
"""

from __future__ import annotations

import httpx

from api.settings import settings

_RESEND_URL = "https://api.resend.com/emails"


def enviar_email(
    destinatario: str, asunto: str, cuerpo_html: str, cuerpo_texto: str | None = None
) -> None:
    """Lanza ValueError si Resend no está configurado, o httpx.HTTPStatusError
    si la API de Resend rechaza el envío (p. ej. dominio remitente sin verificar).

    `cuerpo_texto` es opcional (mejora entregabilidad/accesibilidad) para no
    romper llamadas existentes que solo tienen HTML.
    """
    if not settings.resend_api_key:
        raise ValueError("Resend no está configurado (falta RESEND_API_KEY)")
    payload = {
        "from": settings.alert_from_email,
        "to": [destinatario],
        "subject": asunto,
        "html": cuerpo_html,
    }
    if cuerpo_texto is not None:
        payload["text"] = cuerpo_texto
    respuesta = httpx.post(
        _RESEND_URL,
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json=payload,
        timeout=10,
    )
    respuesta.raise_for_status()
