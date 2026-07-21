"""Tests del módulo de incertidumbre sobre datos sintéticos (sin DuckDB).

Se genera un dataset con estructura conocida y se comprueba la propiedad central de
CQR: la cobertura empírica en el test hold-out alcanza el objetivo 1−α.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.importe import ajustar_cuantilica, intervalos_conformal


def _dataset_sintetico(n: int = 4000, semilla: int = 0) -> pd.DataFrame:
    """Baja simulada dependiente de las features + ruido heterocedástico acotado."""
    rng = np.random.default_rng(semilla)
    cpv = rng.choice(["45", "33", "72", "79"], size=n)
    tipo = rng.choice(["1", "2", "3"], size=n)
    proc = rng.choice(["1", "2", "9"], size=n)
    log_presupuesto = rng.uniform(3, 7, size=n)  # 1k–10M €

    efecto = {"45": 0.05, "33": 0.10, "72": 0.20, "79": 0.15}
    media = np.array([efecto[c] for c in cpv]) + 0.02 * (log_presupuesto - 5)
    # Ruido cuya escala crece con el presupuesto (heterocedástico) -> intervalos
    # que deben ensancharse; buen caso para regresión cuantílica + conformal.
    ruido = rng.normal(0, 0.03 + 0.02 * (log_presupuesto - 3), size=n)
    baja = np.clip(media + ruido, 0.0, 1.0)

    return pd.DataFrame(
        {
            "cpv_division": cpv,
            "tipo_contrato": tipo,
            "procedimiento": proc,
            "log_presupuesto": log_presupuesto,
            "baja_pct": baja,
        }
    )


class TestConformal:
    def test_cobertura_alcanza_objetivo(self):
        df = _dataset_sintetico()
        r = intervalos_conformal(df, alpha=0.1)
        # Garantía marginal ≥ 1−α; se admite un pequeño margen por muestra finita.
        assert r.cobertura_empirica >= 0.90 - 0.03
        assert r.cobertura_empirica <= 1.0

    def test_alpha_mayor_estrecha_el_intervalo(self):
        df = _dataset_sintetico()
        ancho90 = intervalos_conformal(df, alpha=0.1).anchura_media
        ancho80 = intervalos_conformal(df, alpha=0.2).anchura_media
        # Menos confianza (α=0.2 -> 80%) => intervalos más estrechos.
        assert ancho80 < ancho90

    def test_splits_disjuntos_suman_total(self):
        df = _dataset_sintetico(n=1000)
        r = intervalos_conformal(df, alpha=0.1)
        assert r.n_train + r.n_calibracion + r.n_test == len(df)


class TestCuantilica:
    def test_cuantiles_ordenados(self):
        df = _dataset_sintetico(n=2000)
        modelo = ajustar_cuantilica(df)
        pred = modelo.predecir(df.head(50))
        # p10 ≤ p50 ≤ p90 fila a fila (salvo cruces numéricos mínimos).
        assert (pred["p10"] <= pred["p50"] + 1e-9).all()
        assert (pred["p50"] <= pred["p90"] + 1e-9).all()

    def test_mediana_captura_efecto_cpv(self):
        df = _dataset_sintetico(n=3000)
        modelo = ajustar_cuantilica(df)
        coefs = modelo.resumen_coeficientes(0.5)["coef"]
        # La división 72 (efecto simulado 0.20) debe salir con coeficiente positivo
        # frente a la referencia (categoría base 33).
        assert coefs.get("C(cpv_division)[T.72]", 0) > 0
