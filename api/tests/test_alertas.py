"""Tests de alertas: CRUD contra Postgres real (patrón de test_auth.py) +
ejecutar_alertas con la búsqueda híbrida y el envío de email mockeados
(patrón de test_billing.py con Stripe)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from api.alertas import borrar_alerta, crear_alerta, ejecutar_alertas, listar_alertas
from api.auth import registrar_usuario
from api.db import connect, init_schema
from search.hibrida import Resultado


@pytest.fixture(autouse=True, scope="module")
def _esquema():
    init_schema()


@pytest.fixture
def usuario():
    email = f"test-{uuid.uuid4().hex}@example.com"
    creado = registrar_usuario(email, "contraseña-larga")
    yield creado
    with connect() as con:
        con.execute("delete from alertas where usuario_id = %s", (creado.id,))
        con.execute("delete from usuarios where id = %s", (creado.id,))
        con.commit()


def _resultado(entry_id: str) -> Resultado:
    return Resultado(
        entry_id=entry_id,
        expediente=f"EXP-{entry_id}",
        objeto="Asfaltado de carreteras",
        organo="Ayuntamiento de Prueba",
        cpv_division="45",
        anio=2025,
        presupuesto=12345.0,
        score=1.0,
    )


# --- CRUD ----------------------------------------------------------------------


def test_crear_listar_borrar_alerta(usuario):
    alerta_id = crear_alerta(usuario.id, "asfaltado de carreteras")

    alertas = listar_alertas(usuario.id)
    assert len(alertas) == 1
    assert alertas[0]["id"] == alerta_id
    assert alertas[0]["consulta_texto"] == "asfaltado de carreteras"

    assert borrar_alerta(usuario.id, alerta_id) is True
    assert listar_alertas(usuario.id) == []


def test_borrar_alerta_inexistente_devuelve_false(usuario):
    assert borrar_alerta(usuario.id, 999999) is False


def test_borrar_alerta_ajena_devuelve_false(usuario):
    otro_email = f"test-{uuid.uuid4().hex}@example.com"
    otro = registrar_usuario(otro_email, "contraseña-larga")
    alerta_id = crear_alerta(otro.id, "obras públicas")
    try:
        assert borrar_alerta(usuario.id, alerta_id) is False
        assert len(listar_alertas(otro.id)) == 1
    finally:
        with connect() as con:
            con.execute("delete from alertas where usuario_id = %s", (otro.id,))
            con.execute("delete from usuarios where id = %s", (otro.id,))
            con.commit()


# --- ejecutar_alertas ------------------------------------------------------------


def test_ejecutar_alertas_manda_email_con_resultados_nuevos(usuario):
    crear_alerta(usuario.id, "asfaltado de carreteras")
    resultados = [_resultado("a"), _resultado("b")]

    with (
        patch("search.hibrida.buscar", return_value=resultados, create=True),
        patch("api.email.enviar_email", create=True) as mock_enviar,
    ):
        resumen = ejecutar_alertas()

    assert resumen.alertas_procesadas == 1
    assert resumen.emails_enviados == 1
    assert resumen.errores == []
    mock_enviar.assert_called_once()
    destinatario = mock_enviar.call_args.args[0]
    assert destinatario == usuario.email


def test_ejecutar_alertas_manda_email_con_la_plantilla_de_marca(usuario):
    crear_alerta(usuario.id, "asfaltado de carreteras")
    resultados = [_resultado("a")]

    with (
        patch("search.hibrida.buscar", return_value=resultados, create=True),
        patch("api.email.enviar_email", create=True) as mock_enviar,
    ):
        ejecutar_alertas()

    _destinatario, _asunto, html, texto = mock_enviar.call_args.args
    assert "Radar de Contratación Pública" in html
    assert "asfaltado de carreteras" in html
    assert "Radar de Contratación Pública" in texto


def test_ejecutar_alertas_no_repite_email_si_no_hay_resultados_nuevos(usuario):
    crear_alerta(usuario.id, "asfaltado de carreteras")
    resultados = [_resultado("a"), _resultado("b")]

    with (
        patch("search.hibrida.buscar", return_value=resultados, create=True),
        patch("api.email.enviar_email", create=True) as mock_enviar,
    ):
        ejecutar_alertas()
        resumen = ejecutar_alertas()  # segunda vuelta, mismos resultados

    assert resumen.emails_enviados == 0
    mock_enviar.assert_called_once()  # solo la primera vez


def test_ejecutar_alertas_registra_error_sin_abortar_las_demas(usuario):
    crear_alerta(usuario.id, "consulta que falla")
    crear_alerta(usuario.id, "consulta que funciona")

    def _buscar(consulta_texto: str, k: int = 20):
        if consulta_texto == "consulta que falla":
            raise RuntimeError("Postgres no disponible")
        return [_resultado("z")]

    with (
        patch("search.hibrida.buscar", side_effect=_buscar, create=True),
        patch("api.email.enviar_email", create=True) as mock_enviar,
    ):
        resumen = ejecutar_alertas()

    assert resumen.alertas_procesadas == 2
    assert resumen.emails_enviados == 1
    assert len(resumen.errores) == 1
    assert "Postgres no disponible" in resumen.errores[0]
    mock_enviar.assert_called_once()
