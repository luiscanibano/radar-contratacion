"""Billing con Stripe: Checkout de suscripción + procesado del webhook.

El estado autoritativo del plan de un usuario vive en Stripe, no aquí:
`suscripciones` es una caché que el webhook mantiene al día. El vínculo entre
una suscripción de Stripe y nuestro `usuario_id` se hace vía
`subscription_data.metadata` al crear la Checkout Session — así todos los
eventos `customer.subscription.*` posteriores (creada, actualizada, cancelada)
llevan `usuario_id` y `plan` en `subscription.metadata`, sin tener que
correlar por `client_reference_id` en `checkout.session.completed`.
"""

from __future__ import annotations

from datetime import UTC, datetime

import stripe

from api.auth import Usuario
from api.db import connect
from api.planes import FREE, Plan, obtener_plan
from api.settings import settings

stripe.api_key = settings.stripe_secret_key

# Estados de `subscription.status` de Stripe que dan derecho al plan de pago.
# El resto (past_due, canceled, unpaid, incomplete...) se trata como gratuito.
_ESTADOS_ACTIVOS = {"active", "trialing"}


def crear_checkout_session(usuario: Usuario, plan_nombre: str) -> str:
    """Crea una Checkout Session de Stripe para suscribirse a un plan de pago.

    Devuelve la URL a la que redirigir al usuario. Lanza ValueError si Stripe
    no está configurado o el plan no existe/no es de pago.
    """
    if not settings.stripe_secret_key:
        raise ValueError("Stripe no está configurado (falta STRIPE_SECRET_KEY)")
    if plan_nombre == FREE:
        raise ValueError("El plan gratuito no pasa por Checkout")
    try:
        plan = obtener_plan(plan_nombre)
    except KeyError as exc:
        raise ValueError(f"Plan desconocido: {plan_nombre}") from exc
    if not plan.price_id:
        raise ValueError(f"El plan '{plan_nombre}' no tiene price_id de Stripe configurado")

    sesion = stripe.checkout.Session.create(
        customer_email=usuario.email,
        mode="subscription",
        line_items=[{"price": plan.price_id, "quantity": 1}],
        success_url=settings.billing_success_url,
        cancel_url=settings.billing_cancel_url,
        subscription_data={"metadata": {"usuario_id": str(usuario.id), "plan": plan_nombre}},
    )
    return sesion.url


def procesar_webhook(payload: bytes, firma: str) -> None:
    """Verifica la firma y aplica el evento. Lanza ValueError si la firma no es válida."""
    if not settings.stripe_webhook_secret:
        raise ValueError("Stripe no está configurado (falta STRIPE_WEBHOOK_SECRET)")
    try:
        evento = stripe.Webhook.construct_event(payload, firma, settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise ValueError("Firma de webhook inválida") from exc

    # Solo nos interesan los eventos de la propia suscripción: son los que
    # traen el estado (active/past_due/canceled/...) y el periodo vigente.
    # `checkout.session.completed` e `invoice.*` se ignoran a propósito.
    if evento["type"].startswith("customer.subscription."):
        _aplicar_evento_suscripcion(evento["data"]["object"])


def _aplicar_evento_suscripcion(subscription: dict) -> None:
    usuario_id_str = subscription.get("metadata", {}).get("usuario_id")
    if not usuario_id_str:
        # Suscripción creada fuera de nuestro flujo de Checkout (p. ej. a mano
        # en el dashboard de Stripe): no hay usuario al que asociarla.
        return
    usuario_id = int(usuario_id_str)
    plan_nombre = subscription.get("metadata", {}).get("plan", "")
    periodo_fin_ts = subscription.get("current_period_end")
    periodo_fin = datetime.fromtimestamp(periodo_fin_ts, tz=UTC) if periodo_fin_ts else None

    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                insert into suscripciones
                    (usuario_id, stripe_customer_id, stripe_subscription_id,
                     plan, estado, periodo_fin, actualizado_en)
                values (%s, %s, %s, %s, %s, %s, now())
                on conflict (usuario_id) do update set
                    stripe_customer_id = excluded.stripe_customer_id,
                    stripe_subscription_id = excluded.stripe_subscription_id,
                    plan = excluded.plan,
                    estado = excluded.estado,
                    periodo_fin = excluded.periodo_fin,
                    actualizado_en = now()
                """,
                (
                    usuario_id,
                    subscription["customer"],
                    subscription["id"],
                    plan_nombre,
                    subscription["status"],
                    periodo_fin,
                ),
            )
        con.commit()


def plan_actual(usuario_id: int) -> Plan:
    """Plan vigente del usuario. Gratuito si nunca se suscribió o no está activo."""
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "select plan, estado from suscripciones where usuario_id = %s", (usuario_id,)
            )
            fila = cur.fetchone()
    if fila is None:
        return obtener_plan(FREE)
    plan_nombre, estado = fila
    if estado not in _ESTADOS_ACTIVOS:
        return obtener_plan(FREE)
    try:
        return obtener_plan(plan_nombre)
    except KeyError:
        return obtener_plan(FREE)
