"""Catálogo de planes: cuota mensual de preguntas al agente y price_id de Stripe.

`FREE` no tiene price_id (nunca pasa por Checkout) y es el plan implícito de
cualquier usuario sin fila en `suscripciones` o con una suscripción no activa.
`cuota=None` significa sin límite.
"""

from __future__ import annotations

from dataclasses import dataclass

from api.settings import settings

FREE = "free"


@dataclass(frozen=True)
class Plan:
    nombre: str
    cuota: int | None
    price_id: str | None


def _planes_pago() -> dict[str, Plan]:
    # Función (no constante a nivel de módulo) porque `settings` puede
    # cambiar entre tests; los price_id reales solo existen en producción.
    return {
        "basico": Plan("basico", cuota=200, price_id=settings.stripe_price_basico),
        "pro": Plan("pro", cuota=1000, price_id=settings.stripe_price_pro),
        "ilimitado": Plan("ilimitado", cuota=None, price_id=settings.stripe_price_ilimitado),
    }


def planes() -> dict[str, Plan]:
    """Todos los planes, incluido el gratuito."""
    return {FREE: Plan(FREE, cuota=10, price_id=None), **_planes_pago()}


def obtener_plan(nombre: str) -> Plan:
    """Lanza KeyError si `nombre` no es un plan conocido."""
    return planes()[nombre]


def plan_por_price_id(price_id: str) -> Plan | None:
    """Busca qué plan de pago corresponde a un price_id de Stripe (para el webhook)."""
    for plan in _planes_pago().values():
        if plan.price_id == price_id:
            return plan
    return None
