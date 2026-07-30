"""Tests de la cuota mensual de preguntas (contra Postgres real, como test_auth.py)."""

from __future__ import annotations

import uuid

import pytest

from api.auth import registrar_usuario
from api.cuota import consumir_cuota, uso_actual
from api.db import connect, init_schema
from api.planes import obtener_plan


@pytest.fixture(autouse=True, scope="module")
def _esquema():
    init_schema()


@pytest.fixture
def usuario():
    email = f"test-{uuid.uuid4().hex}@example.com"
    creado = registrar_usuario(email, "contraseña-larga")
    yield creado
    with connect() as con:
        con.execute("delete from uso_mensual where usuario_id = %s", (creado.id,))
        con.execute("delete from suscripciones where usuario_id = %s", (creado.id,))
        con.execute("delete from usuarios where id = %s", (creado.id,))
        con.commit()


def test_plan_gratuito_permite_hasta_su_cuota(usuario):
    cuota = obtener_plan("free").cuota
    for _ in range(cuota):
        assert consumir_cuota(usuario.id) is True
    assert consumir_cuota(usuario.id) is False


def test_uso_actual_es_cero_sin_preguntas(usuario):
    assert uso_actual(usuario.id) == 0


def test_uso_actual_cuenta_las_preguntas_consumidas(usuario):
    for _ in range(3):
        consumir_cuota(usuario.id)
    assert uso_actual(usuario.id) == 3


def test_plan_ilimitado_nunca_bloquea(usuario):
    with connect() as con:
        con.execute(
            """
            insert into suscripciones
                (usuario_id, stripe_customer_id, stripe_subscription_id, plan, estado)
            values (%s, 'cus_x', 'sub_x', 'ilimitado', 'active')
            """,
            (usuario.id,),
        )
        con.commit()

    cuota_free = obtener_plan("free").cuota
    for _ in range(cuota_free + 5):
        assert consumir_cuota(usuario.id) is True
