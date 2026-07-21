"""Detección de anomalías sobre la contratación adjudicada.

IMPORTANTE: son **señales estadísticas a revisar**, nunca acusaciones. Se calculan
sobre agregados y se apoyan en métodos *robustos* (mediana/MAD, cuotas, tests de
proporción) porque los datos abiertos traen colas sucias (importes de referencia
minúsculos, bajas fuera de rango, etc.).

Tres familias de señal, sobre `main.fct_adjudicaciones`:

- `baja_atipica`   — baja porcentual anómala dentro de su mercado (CPV × tipo),
  vía z-score robusto (MAD). Ambas colas importan: baja ~0 (adjudicación pegada al
  presupuesto) y baja extrema (posible temeridad).
- `concentracion_organo` — índice HHI de reparto del importe entre adjudicatarios de
  cada órgano, más la cuota del adjudicatario dominante.
- `exceso_oferta_unica`  — órganos cuya tasa de adjudicaciones con oferta única supera
  el promedio del sistema de forma estadísticamente significativa (test de proporción).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from analytics.db import query

# --- Umbrales por defecto (ajustables por argumento) -------------------------

# Denominador mínimo de `presupuesto_referencia` para fiarse de una `baja_pct`.
# Por debajo, una desviación absoluta pequeña dispara bajas porcentuales absurdas.
PRESUPUESTO_MIN_FIABLE = 1_000.0

# Ventana de saneamiento de la baja (fracción). Fuera de aquí es error de dato,
# no una baja real; se descarta antes de calcular la referencia del grupo.
BAJA_MIN, BAJA_MAX = -0.5, 1.0

# Corte de |z robusto| para marcar atípico. 3.5 es el valor habitual para MAD.
Z_ROBUSTO_CORTE = 3.5

# Tamaño mínimo de grupo/órgano para que un estadístico sea creíble.
MIN_GRUPO = 30
MIN_ADJ_ORGANO = 10


# --- Utilidades estadísticas -------------------------------------------------

def _z_robusto(x: pd.Series) -> pd.Series:
    """z-score robusto (basado en mediana y MAD) de una serie.

    z = 0.6745 · (x − mediana) / MAD, donde MAD = mediana(|x − mediana|). El factor
    0.6745 escala el MAD para que sea comparable a una desviación típica bajo
    normalidad. Si MAD = 0 (grupo casi constante) devuelve 0: sin dispersión no hay
    atípicos que declarar.
    """
    mediana = x.median()
    mad = (x - mediana).abs().median()
    if mad == 0 or np.isnan(mad):
        return pd.Series(0.0, index=x.index)
    return 0.6745 * (x - mediana) / mad


def hhi(importes: pd.Series | np.ndarray) -> float:
    """Índice Herfindahl-Hirschman (0–10.000) de un reparto de importes.

    Suma de las cuotas de mercado al cuadrado, escalada a 10.000. Un único
    adjudicatario da 10.000 (monopolio); N adjudicatarios a partes iguales dan
    10.000/N. Ignora importes no positivos y devuelve `nan` si el total es 0.
    """
    v = np.asarray(importes, dtype=float)
    v = v[v > 0]
    total = v.sum()
    if total <= 0:
        return float("nan")
    cuotas = v / total
    return float((cuotas**2).sum() * 10_000)


# --- Señal 1: baja atípica por mercado --------------------------------------

def baja_atipica(
    *,
    min_grupo: int = MIN_GRUPO,
    z_corte: float = Z_ROBUSTO_CORTE,
) -> pd.DataFrame:
    """Adjudicaciones con baja porcentual atípica dentro de su mercado.

    El "mercado" es el par `cpv_division × tipo_contrato`: comparar la baja de una
    obra de la división 45 contra la de un servicio informático no tendría sentido.
    Dentro de cada grupo con al menos `min_grupo` adjudicaciones fiables se calcula
    el z-score robusto de `baja_pct`; se marcan las que superan `z_corte` en valor
    absoluto y se etiqueta la cola.

    Devuelve una fila por adjudicación atípica, ordenada por |z| descendente.
    """
    df = query(
        """
        select
            adjudicacion_id, expediente, organo_nif, organo_contratacion,
            adjudicatario_nif, adjudicatario, cpv_division, tipo_contrato,
            presupuesto_referencia, importe_sin_impuestos, baja_pct
        from main.fct_adjudicaciones
        where baja_pct is not null
          and presupuesto_referencia >= $presupuesto_min
          and baja_pct between $baja_min and $baja_max
        """,
        presupuesto_min=PRESUPUESTO_MIN_FIABLE,
        baja_min=BAJA_MIN,
        baja_max=BAJA_MAX,
    )
    if df.empty:
        return df.assign(z_robusto=[], cola=[], n_grupo=[])

    df["grupo"] = df["cpv_division"].fillna("?") + "|" + df["tipo_contrato"].fillna("?")
    tam = df.groupby("grupo")["baja_pct"].transform("size")
    df = df[tam >= min_grupo].copy()
    if df.empty:
        return df.assign(z_robusto=[], cola=[], n_grupo=[])

    df["z_robusto"] = df.groupby("grupo")["baja_pct"].transform(_z_robusto)
    df["n_grupo"] = df.groupby("grupo")["baja_pct"].transform("size")

    atipicas = df[df["z_robusto"].abs() >= z_corte].copy()
    atipicas["cola"] = np.where(
        atipicas["z_robusto"] < 0, "baja_anormalmente_baja", "baja_anormalmente_alta"
    )
    orden = atipicas["z_robusto"].abs().sort_values(ascending=False).index
    return atipicas.loc[orden].reset_index(drop=True)


# --- Señal 2: concentración por órgano (HHI) --------------------------------

def concentracion_organo(*, min_adjudicaciones: int = MIN_ADJ_ORGANO) -> pd.DataFrame:
    """Índice HHI del reparto del importe adjudicado entre adjudicatarios por órgano.

    Para cada órgano con al menos `min_adjudicaciones` adjudicaciones con importe, se
    calcula la cuota de cada adjudicatario sobre el importe total del órgano y:

        HHI = Σ (cuota_i)² · 10.000          (rango 0–10.000)

    Interpretación habitual (referencia antitrust): < 1500 competido, 1500–2500
    moderadamente concentrado, > 2500 concentrado. Se añade la cuota del adjudicatario
    dominante, que es la lectura más accionable ("un proveedor se lleva el X%").

    Una fila por órgano, ordenada por HHI descendente.
    """
    df = query(
        """
        select organo_nif, organo_contratacion, adjudicatario_nif, adjudicatario,
               importe_sin_impuestos
        from main.fct_adjudicaciones
        where importe_sin_impuestos is not null and importe_sin_impuestos > 0
          and adjudicatario_nif is not null
        """
    )
    if df.empty:
        return pd.DataFrame(
            columns=[
                "organo_nif", "organo_contratacion", "n_adjudicaciones",
                "n_adjudicatarios", "importe_total", "hhi", "cuota_dominante",
                "adjudicatario_dominante", "nivel",
            ]
        )

    filas = []
    # La identidad del órgano es su NIF; el nombre puede venir con grafías distintas
    # entre filas, así que se toma una representativa por grupo.
    for nif, g in df.groupby("organo_nif"):
        if len(g) < min_adjudicaciones:
            continue
        nombre = g["organo_contratacion"].iloc[0]
        por_adj = g.groupby(["adjudicatario_nif", "adjudicatario"])[
            "importe_sin_impuestos"
        ].sum()
        total = por_adj.sum()
        cuotas = por_adj / total
        dom_idx = cuotas.idxmax()
        filas.append(
            {
                "organo_nif": nif,
                "organo_contratacion": nombre,
                "n_adjudicaciones": int(len(g)),
                "n_adjudicatarios": int(por_adj.size),
                "importe_total": float(total),
                "hhi": hhi(por_adj),
                "cuota_dominante": float(cuotas.max()),
                "adjudicatario_dominante": dom_idx[1],
            }
        )

    res = pd.DataFrame(filas)
    if res.empty:
        return res
    res["nivel"] = pd.cut(
        res["hhi"],
        bins=[-np.inf, 1500, 2500, np.inf],
        labels=["competido", "moderado", "concentrado"],
    )
    return res.sort_values("hhi", ascending=False).reset_index(drop=True)


# --- Señal 3: exceso de oferta única ----------------------------------------

def exceso_oferta_unica(
    *,
    min_adjudicaciones: int = MIN_ADJ_ORGANO,
    alpha: float = 0.01,
) -> pd.DataFrame:
    """Órganos con tasa de oferta única significativamente por encima del promedio.

    La adjudicación con un único licitador no es de por sí irregular, pero una tasa
    sistemáticamente alta en un órgano concreto es una señal a revisar. Se compara la
    proporción del órgano contra la proporción global `p0` mediante un test z de una
    cola (H1: p_órgano > p0). Se marca `significativo` cuando el p-valor < `alpha`.

    Una fila por órgano (con ≥ `min_adjudicaciones`), ordenada por tasa descendente.
    """
    df = query(
        """
        select organo_nif,
               any_value(organo_contratacion) as organo_contratacion,
               count(*) as n,
               sum(case when oferta_unica then 1 else 0 end) as n_unica
        from main.fct_adjudicaciones
        where oferta_unica is not null
        group by organo_nif
        """
    )
    if df.empty:
        return df.assign(tasa=[], p_valor=[], significativo=[])

    p0 = df["n_unica"].sum() / df["n"].sum()
    df = df[df["n"] >= min_adjudicaciones].copy()
    if df.empty:
        return df.assign(tasa=[], p_valor=[], significativo=[])

    df["tasa"] = df["n_unica"] / df["n"]
    # z de proporción de una muestra frente a p0, cola derecha.
    se = np.sqrt(p0 * (1 - p0) / df["n"])
    df["z"] = (df["tasa"] - p0) / se
    df["p_valor"] = stats.norm.sf(df["z"])
    df["significativo"] = df["p_valor"] < alpha
    df.attrs["p0_global"] = float(p0)
    return df.sort_values("tasa", ascending=False).reset_index(drop=True)
