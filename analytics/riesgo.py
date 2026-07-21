"""Señales estadísticas de riesgo/transparencia sobre la contratación.

IMPORTANTE: son *señales a revisar*, no acusaciones. Se calculan sobre agregados.

Módulos previstos (Semana 3):
  - concentracion_hhi: índice Herfindahl-Hirschman de adjudicatarios por órgano.
  - licitador_unico: adjudicaciones con un solo licitante.
  - fraccionamiento: contratos secuenciales del mismo objeto/proveedor justo por
    debajo del umbral de contrato menor (15.000 € servicios, 40.000 € obras).
"""

from __future__ import annotations

import duckdb
import pandas as pd

from api.settings import settings

UMBRAL_MENOR_SERVICIOS = 15_000
UMBRAL_MENOR_OBRAS = 40_000


def concentracion_hhi() -> pd.DataFrame:
    """Índice HHI de concentración de importe por órgano de contratación.

    HHI = suma de las cuotas de mercado al cuadrado (0-10.000). Valores altos
    indican pocos adjudicatarios acaparando el gasto de un órgano.
    """
    con = duckdb.connect(settings.duckdb_path, read_only=True)
    try:
        return con.sql(
            """
            with por_organo as (
                select
                    organo_contratacion,
                    sum(presupuesto_sin_impuestos) as importe_total
                from main_marts.fct_licitaciones
                where presupuesto_sin_impuestos is not null
                group by organo_contratacion
            )
            select organo_contratacion, importe_total
            from por_organo
            order by importe_total desc
            """
        ).df()
    finally:
        con.close()


# Los detectores de licitador único y fraccionamiento se desarrollan en la
# Semana 3, una vez la tabla de adjudicaciones incluya adjudicatario y fecha.
