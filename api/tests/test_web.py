"""Tests de la interfaz web estática (landing, panel y retornos de Stripe).

Solo comprueba que las rutas sirven el HTML correcto: la lógica de verdad
vive en el JS del navegador (api/static/app.html) y en los endpoints de la
API que ya tienen sus propios tests.
"""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("ruta", "marcador"),
    [
        ("/", "Radar de"),
        ("/app", "Pregunta al agente"),
        ("/billing/exito", "Suscripción completada"),
        ("/billing/cancelado", "Pago cancelado"),
    ],
)
def test_paginas_html_responden_200(cliente, ruta, marcador):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert marcador in respuesta.text


def test_las_paginas_web_no_ensucian_el_esquema_openapi(cliente):
    rutas_documentadas = cliente.get("/openapi.json").json()["paths"]
    assert "/" not in rutas_documentadas
    assert "/app" not in rutas_documentadas
    assert "/billing/exito" not in rutas_documentadas


def test_la_landing_enlaza_al_panel_y_a_los_docs(cliente):
    portada = cliente.get("/").text
    assert 'href="/app"' in portada
    assert 'href="/docs"' in portada
