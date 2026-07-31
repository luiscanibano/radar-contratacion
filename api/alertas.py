"""Alertas: búsquedas guardadas que se reejecutan periódicamente.

Las funciones CRUD (`crear_alerta`, `listar_alertas`, `borrar_alerta`) son
livianas y las usa `api/main.py` directamente. `ejecutar_alertas` es el job
periódico (ver `orchestration/definitions.py`): importa `search.hibrida`
(arrastra torch, extra opcional `search`) de forma perezoza para no
convertirlo en una dependencia dura de toda la API.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from api.db import connect
from api.email_templates import plantilla_email


@dataclass
class ResumenAlertas:
    alertas_procesadas: int = 0
    emails_enviados: int = 0
    errores: list[str] = field(default_factory=list)


def crear_alerta(usuario_id: int, consulta_texto: str) -> int:
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "insert into alertas (usuario_id, consulta_texto) values (%s, %s) returning id",
                (usuario_id, consulta_texto),
            )
            (alerta_id,) = cur.fetchone()
        con.commit()
    return alerta_id


def listar_alertas(usuario_id: int) -> list[dict]:
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "select id, consulta_texto, creado_en from alertas"
                " where usuario_id = %s order by creado_en desc",
                (usuario_id,),
            )
            cols = [c.name for c in cur.description]
            return [dict(zip(cols, fila, strict=True)) for fila in cur.fetchall()]


def borrar_alerta(usuario_id: int, alerta_id: int) -> bool:
    """Devuelve False si la alerta no existe o no pertenece al usuario."""
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "delete from alertas where id = %s and usuario_id = %s", (alerta_id, usuario_id)
            )
            borrada = cur.rowcount > 0
        con.commit()
    return borrada


def _entry_ids_vistos(con, alerta_id: int) -> set[str]:
    with con.cursor() as cur:
        cur.execute("select entry_id from alertas_vistos where alerta_id = %s", (alerta_id,))
        return {fila[0] for fila in cur.fetchall()}


def _marcar_vistos(con, alerta_id: int, entry_ids: list[str]) -> None:
    with con.cursor() as cur:
        cur.executemany(
            "insert into alertas_vistos (alerta_id, entry_id) values (%s, %s)"
            " on conflict do nothing",
            [(alerta_id, entry_id) for entry_id in entry_ids],
        )


def _renderizar_email(consulta_texto: str, resultados: list) -> tuple[str, str]:
    filas = "".join(
        f'<li style="margin-bottom:10px;">'
        f"<strong>{r.objeto or r.expediente or r.entry_id}</strong><br/>"
        f'<span style="color:#64748b;">{r.organo or "órgano desconocido"}'
        f"{f' · {r.presupuesto:,.0f} €' if r.presupuesto else ''}</span><br/>"
        f'<a href="{r.entry_id}" style="color:#1e40af;">ver expediente</a></li>'
        for r in resultados
    )
    cuerpo = (
        f"<p>Hay novedades para tu alerta «{consulta_texto}»:</p>"
        f'<ul style="padding-left:20px;margin:16px 0;">{filas}</ul>'
    )
    return plantilla_email(
        f"Novedades en «{consulta_texto}»",
        cuerpo,
        pie_contexto="Recibes este email porque tienes una alerta guardada en Radar de"
        " Contratación Pública. Gestiona tus alertas desde tu panel.",
    )


def ejecutar_alertas(k: int = 20) -> ResumenAlertas:
    """Reejecuta todas las alertas guardadas y manda un email por cada una con
    resultados no vistos hasta ahora. Un fallo en una alerta (búsqueda o envío)
    se registra en el resumen y no aborta las demás.
    """
    from api.email import enviar_email
    from search.hibrida import buscar

    resumen = ResumenAlertas()
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "select a.id, a.consulta_texto, u.email"
                " from alertas a join usuarios u on u.id = a.usuario_id"
            )
            alertas = cur.fetchall()

        for alerta_id, consulta_texto, email in alertas:
            resumen.alertas_procesadas += 1
            try:
                resultados = buscar(consulta_texto, k=k)
                vistos = _entry_ids_vistos(con, alerta_id)
                nuevos = [r for r in resultados if r.entry_id not in vistos]
                if nuevos:
                    html, texto = _renderizar_email(consulta_texto, nuevos)
                    enviar_email(
                        email,
                        f"Radar de Contratación: novedades en «{consulta_texto}»",
                        html,
                        texto,
                    )
                    resumen.emails_enviados += 1
                _marcar_vistos(con, alerta_id, [r.entry_id for r in resultados])
                con.commit()
            except Exception as exc:  # noqa: BLE001 — una alerta rota no debe tumbar el resto
                con.rollback()
                resumen.errores.append(f"alerta {alerta_id}: {exc}")

    return resumen
