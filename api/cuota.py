"""Cuota mensual de preguntas al agente (plan gratuito y de pago por volumen).

Un plan sin límite (`cuota=None`) sigue contando en `uso_mensual` para
analítica, pero nunca bloquea.
"""

from __future__ import annotations

from datetime import UTC, datetime

from api.billing import plan_actual
from api.db import connect


def _mes_actual() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


def uso_actual(usuario_id: int) -> int:
    """Preguntas ya consumidas este mes (0 si aún no hay fila en uso_mensual)."""
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "select preguntas from uso_mensual where usuario_id = %s and mes = %s",
                (usuario_id, _mes_actual()),
            )
            fila = cur.fetchone()
    return fila[0] if fila else 0


def consumir_cuota(usuario_id: int) -> bool:
    """Cuenta una pregunta del usuario si le queda cuota este mes.

    Devuelve False (sin contar nada) si ya agotó la cuota de su plan.
    El chequeo y el incremento son atómicos (bloqueo de fila) para que dos
    peticiones concurrentes del mismo usuario no se cuelen por encima del
    límite.
    """
    plan = plan_actual(usuario_id)
    mes = _mes_actual()
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                insert into uso_mensual (usuario_id, mes, preguntas)
                values (%s, %s, 0)
                on conflict (usuario_id, mes) do nothing
                """,
                (usuario_id, mes),
            )
            cur.execute(
                "select preguntas from uso_mensual where usuario_id = %s and mes = %s for update",
                (usuario_id, mes),
            )
            (preguntas,) = cur.fetchone()

            if plan.cuota is not None and preguntas >= plan.cuota:
                con.commit()  # libera el bloqueo de fila sin cambiar nada
                return False

            cur.execute(
                "update uso_mensual set preguntas = preguntas + 1"
                " where usuario_id = %s and mes = %s",
                (usuario_id, mes),
            )
        con.commit()
    return True
