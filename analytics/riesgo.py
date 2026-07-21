"""Orquestador de señales de riesgo/transparencia sobre la contratación.

IMPORTANTE: son **señales estadísticas a revisar**, no acusaciones. Todo se calcula
sobre agregados de los marts (`main.fct_adjudicaciones`) con métodos robustos. Este
módulo no implementa estadística: compone las señales de `analytics.anomalias` en un
informe único y prioriza los órganos que acumulan más indicios.

Uso:
    from analytics.riesgo import informe_riesgo
    inf = informe_riesgo()
    inf.organos.head(20)      # ranking de órganos por nº de señales
    inf.baja_atipica          # detalle de adjudicaciones con baja anómala
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analytics.anomalias import (
    baja_atipica,
    concentracion_organo,
    exceso_oferta_unica,
)


@dataclass
class InformeRiesgo:
    """Señales crudas por familia más un ranking de órganos por indicios acumulados."""

    organos: pd.DataFrame       # una fila por órgano con las señales que dispara
    baja_atipica: pd.DataFrame  # detalle de adjudicaciones con baja anómala
    concentracion: pd.DataFrame
    oferta_unica: pd.DataFrame


def informe_riesgo(
    *,
    hhi_concentrado: float = 2500,
    cuota_dominante_alta: float = 0.5,
) -> InformeRiesgo:
    """Compone las tres señales y ranquea órganos por número de indicios.

    Un órgano suma una señal si: (a) tiene adjudicaciones con baja atípica, (b) su HHI
    supera `hhi_concentrado` o un adjudicatario acapara más de `cuota_dominante_alta`,
    o (c) su tasa de oferta única es significativamente alta. El ranking ordena por
    número de señales y, a igualdad, por importe adjudicado.
    """
    ba = baja_atipica()
    conc = concentracion_organo()
    ofu = exceso_oferta_unica()

    # (a) órganos con al menos una baja atípica
    s_baja = (
        ba.groupby("organo_nif").size().rename("n_bajas_atipicas")
        if not ba.empty
        else pd.Series(dtype="int64", name="n_bajas_atipicas")
    )

    # (b) órganos concentrados
    conc_flag = conc[
        (conc["hhi"] >= hhi_concentrado) | (conc["cuota_dominante"] >= cuota_dominante_alta)
    ] if not conc.empty else conc
    s_conc = conc.set_index("organo_nif") if not conc.empty else conc

    # (c) órganos con exceso de oferta única significativo
    ofu_sig = ofu[ofu["significativo"]] if not ofu.empty else ofu

    # Ensamblar una fila por órgano
    organos = (
        conc[["organo_nif", "organo_contratacion", "importe_total"]].copy()
        if not conc.empty
        else pd.DataFrame(columns=["organo_nif", "organo_contratacion", "importe_total"])
    )
    organos = organos.set_index("organo_nif")
    organos["n_bajas_atipicas"] = s_baja.reindex(organos.index).fillna(0).astype(int)
    organos["hhi"] = (
        s_conc["hhi"].reindex(organos.index) if not s_conc.empty else pd.NA
    )
    organos["cuota_dominante"] = (
        s_conc["cuota_dominante"].reindex(organos.index) if not s_conc.empty else pd.NA
    )
    organos["concentrado"] = organos.index.isin(
        conc_flag["organo_nif"] if not conc_flag.empty else []
    )
    tasa_ofu = (
        ofu.set_index("organo_nif")["tasa"].reindex(organos.index)
        if not ofu.empty
        else pd.NA
    )
    organos["tasa_oferta_unica"] = tasa_ofu
    organos["oferta_unica_alta"] = organos.index.isin(
        ofu_sig["organo_nif"] if not ofu_sig.empty else []
    )

    organos["n_senales"] = (
        (organos["n_bajas_atipicas"] > 0).astype(int)
        + organos["concentrado"].astype(int)
        + organos["oferta_unica_alta"].astype(int)
    )
    organos = (
        organos[organos["n_senales"] > 0]
        .sort_values(["n_senales", "importe_total"], ascending=[False, False])
        .reset_index()
    )

    return InformeRiesgo(
        organos=organos,
        baja_atipica=ba,
        concentracion=conc,
        oferta_unica=ofu,
    )
