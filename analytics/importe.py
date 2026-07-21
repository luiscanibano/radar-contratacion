"""Baja esperada de una adjudicación **con intervalos de incertidumbre**.

En vez de predecir un único número para la baja de un contrato, damos un rango. Dos
aproximaciones complementarias, ambas sobre `main.fct_adjudicaciones`:

1. `ajustar_cuantilica` — **regresión cuantílica** (statsmodels `QuantReg`) en los
   cuantiles 0.1/0.5/0.9. Interpretable: cada coeficiente dice cuánto mueve la baja
   una división CPV, un tipo de contrato o el tamaño del presupuesto. Los intervalos,
   sin embargo, no tienen garantía de cobertura.

2. `intervalos_conformal` — **CQR** (Conformalized Quantile Regression, Romano et al.
   2019): sobre regresores cuantílicos base (gradient boosting) se calibra el intervalo
   con un conjunto de *calibración* para garantizar cobertura marginal ≥ 1−α, y se mide
   la cobertura empírica en un *test* independiente. Es la lectura honesta de la
   incertidumbre.

Se modela `baja_pct` (baja sobre el presupuesto de referencia): es adimensional y
comparable entre mercados, a diferencia del importe bruto. Sólo se usan variables
conocidas *antes* de la apertura (división CPV, tipo, procedimiento, tamaño del
presupuesto): así el modelo estima la baja *esperable a priori* de una licitación.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

from analytics.anomalias import BAJA_MAX, BAJA_MIN, PRESUPUESTO_MIN_FIABLE
from analytics.db import query

SEMILLA = 42
_FORMULA = "baja_pct ~ C(cpv_division) + C(tipo_contrato) + C(procedimiento) + log_presupuesto"
_NUM = "log_presupuesto"
_CAT = ["cpv_division", "tipo_contrato", "procedimiento"]


def cargar_datos() -> pd.DataFrame:
    """Subconjunto limpio para modelar la baja (mismos filtros de fiabilidad que anomalías)."""
    df = query(
        """
        select cpv_division, tipo_contrato, procedimiento,
               presupuesto_referencia, baja_pct
        from main.fct_adjudicaciones
        where baja_pct is not null
          and presupuesto_referencia >= $presupuesto_min
          and baja_pct between $baja_min and $baja_max
          and cpv_division is not null
          and tipo_contrato is not null
          and procedimiento is not null
        """,
        presupuesto_min=PRESUPUESTO_MIN_FIABLE,
        baja_min=BAJA_MIN,
        baja_max=BAJA_MAX,
    )
    df["log_presupuesto"] = np.log10(df["presupuesto_referencia"].astype(float))
    return df


# --- 1. Regresión cuantílica (interpretable) --------------------------------

@dataclass
class ModeloCuantilico:
    """Regresiones cuantílicas ajustadas y su predicción de intervalos."""

    modelos: dict[float, object]  # cuantil -> RegressionResults de QuantReg
    quantiles: tuple[float, ...]

    def predecir(self, nuevos: pd.DataFrame) -> pd.DataFrame:
        """Predice la baja en cada cuantil para filas nuevas (con `log_presupuesto`)."""
        out = pd.DataFrame(index=nuevos.index)
        for q, res in self.modelos.items():
            out[f"p{int(q * 100)}"] = res.predict(nuevos)
        return out

    def resumen_coeficientes(self, cuantil: float = 0.5) -> pd.DataFrame:
        """Coeficientes del cuantil indicado, ordenados por efecto absoluto."""
        res = self.modelos[cuantil]
        tabla = pd.DataFrame({"coef": res.params, "p_valor": res.pvalues})
        return tabla.reindex(tabla["coef"].abs().sort_values(ascending=False).index)


def ajustar_cuantilica(
    df: pd.DataFrame | None = None,
    quantiles: tuple[float, ...] = (0.1, 0.5, 0.9),
) -> ModeloCuantilico:
    """Ajusta `QuantReg` en cada cuantil sobre las features pre-adjudicación."""
    if df is None:
        df = cargar_datos()
    modelos = {q: smf.quantreg(_FORMULA, df).fit(q=q) for q in quantiles}
    return ModeloCuantilico(modelos=modelos, quantiles=quantiles)


# --- 2. CQR: intervalos con cobertura garantizada ---------------------------

@dataclass
class ResultadoConformal:
    """Intervalos CQR calibrados y sus métricas de cobertura en test."""

    alpha: float
    cobertura_objetivo: float
    cobertura_empirica: float
    anchura_media: float
    correccion: float  # ajuste conformal aplicado a los bordes del intervalo
    n_train: int
    n_calibracion: int
    n_test: int
    predicciones: pd.DataFrame  # test: y_real, q_bajo, q_alto (ya corregidos)


def _codificar(df: pd.DataFrame, columnas: pd.Index | None = None) -> pd.DataFrame:
    """One-hot de las categóricas + la numérica, alineado a `columnas` si se da."""
    X = pd.get_dummies(df[_CAT + [_NUM]], columns=_CAT, dummy_na=False)
    if columnas is not None:
        X = X.reindex(columns=columnas, fill_value=0)
    return X


def intervalos_conformal(
    df: pd.DataFrame | None = None,
    alpha: float = 0.1,
    semilla: int = SEMILLA,
) -> ResultadoConformal:
    """CQR: intervalos de baja con cobertura marginal ≥ 1−α, medida en un test hold-out.

    Reparte los datos en train (ajuste de los regresores cuantílicos base), calibración
    (cálculo de la corrección conformal) y test (verificación de cobertura). El regresor
    base es *gradient boosting* con pérdida cuantílica en α/2 y 1−α/2.
    """
    if df is None:
        df = cargar_datos()

    q_bajo, q_alto = alpha / 2, 1 - alpha / 2
    y = df["baja_pct"].to_numpy()
    X = _codificar(df)

    # train (50%) / calibración (25%) / test (25%)
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(
        X, y, test_size=0.5, random_state=semilla
    )
    X_cal, X_te, y_cal, y_te = train_test_split(
        X_tmp, y_tmp, test_size=0.5, random_state=semilla
    )

    comun = dict(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=semilla)
    m_bajo = GradientBoostingRegressor(loss="quantile", alpha=q_bajo, **comun).fit(X_tr, y_tr)
    m_alto = GradientBoostingRegressor(loss="quantile", alpha=q_alto, **comun).fit(X_tr, y_tr)

    # Puntuación de conformidad en calibración: cuánto se sale y del intervalo base.
    lo_cal, hi_cal = m_bajo.predict(X_cal), m_alto.predict(X_cal)
    scores = np.maximum(lo_cal - y_cal, y_cal - hi_cal)
    n = len(scores)
    # Cuantil conformal con la corrección de muestra finita (nivel ajustado).
    nivel = min(1.0, np.ceil((n + 1) * (1 - alpha)) / n)
    correccion = float(np.quantile(scores, nivel, method="higher"))

    lo_te = m_bajo.predict(X_te) - correccion
    hi_te = m_alto.predict(X_te) + correccion
    dentro = (y_te >= lo_te) & (y_te <= hi_te)

    predicciones = pd.DataFrame(
        {"y_real": y_te, "q_bajo": lo_te, "q_alto": hi_te, "dentro": dentro}
    )
    return ResultadoConformal(
        alpha=alpha,
        cobertura_objetivo=1 - alpha,
        cobertura_empirica=float(dentro.mean()),
        anchura_media=float((hi_te - lo_te).mean()),
        correccion=correccion,
        n_train=len(y_tr),
        n_calibracion=len(y_cal),
        n_test=len(y_te),
        predicciones=predicciones,
    )
