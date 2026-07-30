"""Tests de la interfaz web (landing, panel y retornos de Stripe).

La interfaz es ahora una SPA de React construida con Vite (`web/`, ver
`web/vite.config.ts` para las 4 páginas): el HTML que sirve esta API es solo
el cascarón (`<title>` + `<div id="root">` + el bundle con hash), el
contenido real lo pinta React en el navegador. Estos tests solo pueden
comprobar lo que vive en ese cascarón — el resto (formularios, fetch a la
API, navegación) está cubierto por la verificación manual en el navegador,
no por pytest.

Se saltan si `api/static` no tiene el build copiado (`npm run build` en
`web/` + copia a `api/static`, que es lo que hace `api/Dockerfile`) — en
desarrollo local la interfaz se sirve con el dev server de Vite, no con
esta API, así que `api/static` normalmente está vacío fuera de Docker.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_STATIC = Path(__file__).parent.parent / "static"

pytestmark = pytest.mark.skipif(
    not (_STATIC / "index.html").exists(),
    reason=(
        "web/ no está construido en api/static (ejecuta 'npm run build' en "
        "web/ y copia web/dist a api/static, o usa api/Dockerfile)"
    ),
)


@pytest.mark.parametrize(
    ("ruta", "titulo"),
    [
        ("/", "Radar de Contratación Pública"),
        ("/app", "Panel · Radar de Contratación Pública"),
        ("/billing/exito", "Suscripción completada"),
        ("/billing/cancelado", "Pago cancelado"),
        ("/legal", "Aviso legal · Radar de Contratación Pública"),
    ],
)
def test_paginas_html_responden_200(cliente, ruta, titulo):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert f"<title>{titulo}" in respuesta.text
    assert '<div id="root">' in respuesta.text


def test_las_paginas_web_no_ensucian_el_esquema_openapi(cliente):
    rutas_documentadas = cliente.get("/openapi.json").json()["paths"]
    assert "/" not in rutas_documentadas
    assert "/app" not in rutas_documentadas
    assert "/billing/exito" not in rutas_documentadas
    assert "/legal" not in rutas_documentadas
