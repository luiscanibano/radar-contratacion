"""Tests de billing: Checkout y webhook de Stripe.

El SDK de Stripe se mockea igual que el cliente de Anthropic en
test_graph.py (nunca hablamos con Stripe de verdad). El estado que el webhook
escribe (`suscripciones`) sí se verifica contra el Postgres real, igual que
en test_auth.py.
"""

from __future__ import annotations

import uuid
from unittest.mock import Mock, patch

import pytest
import stripe
from fastapi.testclient import TestClient

from api.auth import create_access_token, registrar_usuario
from api.billing import crear_checkout_session, crear_portal_session, plan_actual, procesar_webhook
from api.db import connect, init_schema
from api.main import app
from api.planes import FREE, obtener_plan
from api.settings import settings


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


@pytest.fixture
def stripe_configurado(monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_falsa")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_falso")
    monkeypatch.setattr(settings, "stripe_price_basico", "price_basico_falso")
    monkeypatch.setattr(settings, "stripe_price_pro", "price_pro_falso")
    monkeypatch.setattr(settings, "stripe_price_ilimitado", "price_ilimitado_falso")


def _evento_suscripcion(usuario_id: int, plan: str, status: str, customer="cus_1", sub_id="sub_1"):
    return {
        "type": f"customer.subscription.{status if status == 'deleted' else 'updated'}",
        "data": {
            "object": {
                "id": sub_id,
                "customer": customer,
                "status": status if status != "deleted" else "canceled",
                "current_period_end": 1900000000,
                "metadata": {"usuario_id": str(usuario_id), "plan": plan},
            }
        },
    }


# --- crear_checkout_session ---------------------------------------------------


def test_checkout_sin_stripe_configurado_lanza_value_error(usuario):
    with pytest.raises(ValueError, match="STRIPE_SECRET_KEY"):
        crear_checkout_session(usuario, "basico")


def test_checkout_con_plan_gratuito_lanza_value_error(usuario, stripe_configurado):
    with pytest.raises(ValueError, match="gratuito"):
        crear_checkout_session(usuario, FREE)


def test_checkout_con_plan_desconocido_lanza_value_error(usuario, stripe_configurado):
    with pytest.raises(ValueError, match="desconocido"):
        crear_checkout_session(usuario, "no-existe")


def test_checkout_sin_price_id_configurado_lanza_value_error(usuario, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_falsa")
    with pytest.raises(ValueError, match="price_id"):
        crear_checkout_session(usuario, "basico")


def test_checkout_exitoso_crea_sesion_de_stripe(usuario, stripe_configurado):
    sesion_falsa = Mock(url="https://checkout.stripe.com/session/x")
    with patch("stripe.checkout.Session.create", return_value=sesion_falsa) as mock_create:
        url = crear_checkout_session(usuario, "pro")

    assert url == "https://checkout.stripe.com/session/x"
    kwargs = mock_create.call_args.kwargs
    assert kwargs["customer_email"] == usuario.email
    assert kwargs["line_items"] == [{"price": "price_pro_falso", "quantity": 1}]
    assert kwargs["subscription_data"]["metadata"] == {
        "usuario_id": str(usuario.id),
        "plan": "pro",
    }


# --- procesar_webhook ----------------------------------------------------------


def test_webhook_sin_secreto_configurado_lanza_value_error():
    with pytest.raises(ValueError, match="STRIPE_WEBHOOK_SECRET"):
        procesar_webhook(b"{}", "firma")


def test_webhook_con_firma_invalida_lanza_value_error(stripe_configurado):
    with patch(
        "stripe.Webhook.construct_event",
        side_effect=stripe.SignatureVerificationError("mala firma", "firma"),
    ):
        with pytest.raises(ValueError, match="Firma"):
            procesar_webhook(b"{}", "firma-mala")


def test_webhook_de_suscripcion_activa_actualiza_el_plan(usuario, stripe_configurado):
    evento = _evento_suscripcion(usuario.id, "pro", "active")
    with patch("stripe.Webhook.construct_event", return_value=evento):
        procesar_webhook(b"{}", "firma-cualquiera")

    assert plan_actual(usuario.id).nombre == "pro"


def test_webhook_de_suscripcion_cancelada_vuelve_a_gratuito(usuario, stripe_configurado):
    with patch(
        "stripe.Webhook.construct_event",
        return_value=_evento_suscripcion(usuario.id, "pro", "active"),
    ):
        procesar_webhook(b"{}", "firma")
    assert plan_actual(usuario.id).nombre == "pro"

    with patch(
        "stripe.Webhook.construct_event",
        return_value=_evento_suscripcion(usuario.id, "pro", "deleted"),
    ):
        procesar_webhook(b"{}", "firma")
    assert plan_actual(usuario.id).nombre == FREE


def test_webhook_ignora_eventos_que_no_son_de_suscripcion(usuario, stripe_configurado):
    evento = {"type": "invoice.paid", "data": {"object": {}}}
    with patch("stripe.Webhook.construct_event", return_value=evento):
        procesar_webhook(b"{}", "firma")  # no debe reventar
    assert plan_actual(usuario.id).nombre == FREE


def test_webhook_ignora_suscripcion_sin_usuario_id(stripe_configurado):
    evento = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_ajeno",
                "customer": "cus_ajeno",
                "status": "active",
                "current_period_end": 1900000000,
                "metadata": {},
            }
        },
    }
    with patch("stripe.Webhook.construct_event", return_value=evento):
        procesar_webhook(b"{}", "firma")  # no debe reventar ni escribir nada


# --- plan_actual -----------------------------------------------------------------


def test_plan_actual_sin_suscripcion_es_gratuito(usuario):
    assert plan_actual(usuario.id).nombre == FREE


def test_plan_actual_con_estado_no_activo_es_gratuito(usuario, stripe_configurado):
    with patch(
        "stripe.Webhook.construct_event",
        return_value=_evento_suscripcion(usuario.id, "basico", "past_due"),
    ):
        procesar_webhook(b"{}", "firma")
    assert plan_actual(usuario.id).nombre == FREE


# --- crear_portal_session -------------------------------------------------------


def test_portal_sin_stripe_configurado_lanza_value_error(usuario):
    with pytest.raises(ValueError, match="STRIPE_SECRET_KEY"):
        crear_portal_session(usuario)


def test_portal_sin_suscripcion_lanza_value_error(usuario, stripe_configurado):
    with pytest.raises(ValueError, match="suscripción"):
        crear_portal_session(usuario)


def test_portal_con_suscripcion_crea_sesion_de_stripe(usuario, stripe_configurado):
    evento = _evento_suscripcion(usuario.id, "pro", "active", customer="cus_test_1")
    with patch("stripe.Webhook.construct_event", return_value=evento):
        procesar_webhook(b"{}", "firma")

    sesion_falsa = Mock(url="https://billing.stripe.com/session/x")
    with patch("stripe.billing_portal.Session.create", return_value=sesion_falsa) as mock_create:
        url = crear_portal_session(usuario)

    assert url == "https://billing.stripe.com/session/x"
    kwargs = mock_create.call_args.kwargs
    assert kwargs["customer"] == "cus_test_1"
    assert kwargs["return_url"] == settings.billing_portal_return_url


# --- endpoints HTTP -----------------------------------------------------------


@pytest.fixture
def cliente():
    return TestClient(app)


def test_endpoint_checkout_devuelve_la_url_de_stripe(cliente, usuario, stripe_configurado):
    token = create_access_token(usuario)
    sesion_falsa = Mock(url="https://checkout.stripe.com/session/x")
    with patch("stripe.checkout.Session.create", return_value=sesion_falsa):
        respuesta = cliente.post(
            "/billing/checkout",
            json={"plan": "pro"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"checkout_url": "https://checkout.stripe.com/session/x"}


def test_endpoint_checkout_sin_token_da_401(cliente):
    respuesta = cliente.post("/billing/checkout", json={"plan": "pro"})
    assert respuesta.status_code == 401


def test_endpoint_checkout_con_plan_invalido_da_400(cliente, usuario, stripe_configurado):
    token = create_access_token(usuario)
    respuesta = cliente.post(
        "/billing/checkout",
        json={"plan": "no-existe"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 400


def test_endpoint_webhook_con_firma_invalida_da_400(cliente, stripe_configurado):
    with patch(
        "stripe.Webhook.construct_event",
        side_effect=stripe.SignatureVerificationError("mala firma", "firma"),
    ):
        respuesta = cliente.post(
            "/billing/webhook", content=b"{}", headers={"stripe-signature": "firma-mala"}
        )
    assert respuesta.status_code == 400


def test_endpoint_webhook_aplica_el_evento(cliente, usuario, stripe_configurado):
    evento = _evento_suscripcion(usuario.id, "basico", "active")
    with patch("stripe.Webhook.construct_event", return_value=evento):
        respuesta = cliente.post(
            "/billing/webhook", content=b"{}", headers={"stripe-signature": "firma"}
        )
    assert respuesta.status_code == 204
    assert plan_actual(usuario.id).nombre == "basico"


def test_endpoint_portal_devuelve_la_url_de_stripe(cliente, usuario, stripe_configurado):
    evento = _evento_suscripcion(usuario.id, "pro", "active")
    with patch("stripe.Webhook.construct_event", return_value=evento):
        procesar_webhook(b"{}", "firma")

    token = create_access_token(usuario)
    sesion_falsa = Mock(url="https://billing.stripe.com/session/x")
    with patch("stripe.billing_portal.Session.create", return_value=sesion_falsa):
        respuesta = cliente.post("/billing/portal", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    assert respuesta.json() == {"portal_url": "https://billing.stripe.com/session/x"}


def test_endpoint_portal_sin_token_da_401(cliente):
    respuesta = cliente.post("/billing/portal")
    assert respuesta.status_code == 401


def test_endpoint_portal_sin_suscripcion_da_400(cliente, usuario, stripe_configurado):
    token = create_access_token(usuario)
    respuesta = cliente.post("/billing/portal", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 400


def test_endpoint_mi_plan_gratuito_recien_creado(cliente, usuario):
    token = create_access_token(usuario)
    respuesta = cliente.get("/me/plan", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    assert respuesta.json() == {"plan": FREE, "cuota": 10, "usadas": 0, "restantes": 10}


def test_endpoint_mi_plan_tras_suscripcion_pro(cliente, usuario, stripe_configurado):
    evento = _evento_suscripcion(usuario.id, "pro", "active")
    with patch("stripe.Webhook.construct_event", return_value=evento):
        procesar_webhook(b"{}", "firma")

    token = create_access_token(usuario)
    respuesta = cliente.get("/me/plan", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    assert respuesta.json() == {"plan": "pro", "cuota": 1000, "usadas": 0, "restantes": 1000}


def test_endpoint_mi_plan_ilimitado_no_tiene_restantes(cliente, usuario, stripe_configurado):
    evento = _evento_suscripcion(usuario.id, "ilimitado", "active")
    with patch("stripe.Webhook.construct_event", return_value=evento):
        procesar_webhook(b"{}", "firma")

    token = create_access_token(usuario)
    respuesta = cliente.get("/me/plan", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "plan": "ilimitado",
        "cuota": None,
        "usadas": 0,
        "restantes": None,
    }


def test_endpoint_mi_plan_sin_token_da_401(cliente):
    respuesta = cliente.get("/me/plan")
    assert respuesta.status_code == 401


def test_preguntar_devuelve_402_al_agotar_la_cuota(cliente, usuario):
    token = create_access_token(usuario)
    headers = {"Authorization": f"Bearer {token}"}
    cuota = obtener_plan(FREE).cuota
    with patch("api.main.responder", return_value=("hola", Mock())), patch("api.main.emitir"):
        for _ in range(cuota):
            respuesta = cliente.post("/preguntar", json={"texto": "hola"}, headers=headers)
            assert respuesta.status_code == 200
        respuesta = cliente.post("/preguntar", json={"texto": "hola"}, headers=headers)
    assert respuesta.status_code == 402
