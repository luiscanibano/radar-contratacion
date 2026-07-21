"""Tests de las utilidades estadísticas de anomalías, con datos sintéticos.

No tocan DuckDB: validan la lógica pura (z robusto, HHI, test de proporción) sobre
entradas construidas a mano con resultado conocido.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from analytics.anomalias import _z_robusto, hhi


class TestZRobusto:
    def test_outlier_destaca_y_mediana_es_cero(self):
        # 100 valores en ~0 y un outlier claro en 10.
        base = pd.Series([0.0] * 50 + [1.0] * 50 + [10.0])
        z = _z_robusto(base)
        # El outlier debe tener |z| muy por encima del corte 3.5.
        assert z.iloc[-1] > 3.5
        # Un valor típico se queda dentro.
        assert abs(z.iloc[0]) < 3.5

    def test_mad_cero_devuelve_ceros(self):
        # Serie constante: sin dispersión no hay atípicos.
        z = _z_robusto(pd.Series([5.0] * 20))
        assert (z == 0.0).all()

    def test_resistente_a_contaminacion(self):
        # Insertar varios outliers no desplaza la referencia como haría la media/std.
        limpio = pd.Series(np.zeros(100))
        contaminado = pd.concat([limpio, pd.Series([1e6] * 5)], ignore_index=True)
        z = _z_robusto(contaminado)
        # Los 100 ceros siguen con z=0 (mediana y MAD intactos frente a 5 outliers).
        assert (z.iloc[:100] == 0.0).all()


class TestHHI:
    def test_monopolio(self):
        assert hhi(pd.Series([100.0])) == pytest.approx(10_000)

    def test_reparto_uniforme(self):
        # N iguales -> HHI = 10000/N.
        assert hhi(np.array([25.0, 25.0, 25.0, 25.0])) == pytest.approx(2_500)

    def test_ignora_no_positivos(self):
        # Ceros/negativos no cuentan: equivale a dos adjudicatarios iguales.
        assert hhi([50.0, 50.0, 0.0, -10.0]) == pytest.approx(5_000)

    def test_total_cero_es_nan(self):
        assert np.isnan(hhi([0.0, 0.0]))

    def test_dominante_eleva_hhi(self):
        concentrado = hhi([90.0, 5.0, 5.0])
        repartido = hhi([34.0, 33.0, 33.0])
        assert concentrado > repartido > 3_000


class TestProporcion:
    """Réplica de la lógica del test z de proporción usada en exceso_oferta_unica."""

    def test_tasa_muy_por_encima_es_significativa(self):
        p0 = 0.36
        n, exitos = 30, 30  # 100% oferta única con n grande
        tasa = exitos / n
        se = np.sqrt(p0 * (1 - p0) / n)
        p_valor = stats.norm.sf((tasa - p0) / se)
        assert p_valor < 0.01

    def test_tasa_en_la_media_no_es_significativa(self):
        p0 = 0.36
        n, exitos = 30, 11  # ~0.367, junto a p0
        tasa = exitos / n
        se = np.sqrt(p0 * (1 - p0) / n)
        p_valor = stats.norm.sf((tasa - p0) / se)
        assert p_valor > 0.05
