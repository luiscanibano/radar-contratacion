# Analytics (Data Science)

Capa estadística sobre los marts de dbt (`main.fct_adjudicaciones`, `…dim_organo`, …).
Métodos **robustos** por diseño: los datos abiertos traen colas sucias (importes de
referencia minúsculos, bajas fuera de rango) que hundirían a media/desviación ingenuas.

> ⚠️ Todo son **señales estadísticas a revisar**, nunca acusaciones. Análisis agregado,
> RGPD por diseño.

## Módulos

- `db.py` — conexión de solo lectura a DuckDB, resuelta contra la raíz del repo (funciona
  desde cualquier cwd: notebooks, tests, orquestación).
- `anomalias.py` — tres familias de señal:
  - `baja_atipica()` — baja porcentual anómala dentro de su mercado (`cpv_division ×
    tipo_contrato`) vía **z-score robusto (MAD)**. Marca ambas colas.
  - `concentracion_organo()` — **índice HHI** del reparto del importe entre
    adjudicatarios de cada órgano + cuota del adjudicatario dominante.
  - `exceso_oferta_unica()` — órganos con tasa de oferta única significativamente alta
    (**test z de proporción** frente al promedio del sistema).
- `importe.py` — **baja esperada con incertidumbre** (features pre-adjudicación):
  - `ajustar_cuantilica()` — regresión cuantílica (`QuantReg`) p10/p50/p90, interpretable.
  - `intervalos_conformal()` — **CQR** (Conformalized Quantile Regression) con cobertura
    marginal garantizada ≥ 1−α, medida en un test hold-out.
- `riesgo.py` — orquestador: compone las señales en un `InformeRiesgo` y ranquea órganos
  por número de indicios acumulados.

## Tests

`analytics/tests/` valida la estadística pura con fixtures sintéticos (z robusto, HHI,
test de proporción, cobertura conformal) — sin dependencia de DuckDB:

```bash
pytest analytics/tests -q
```

## Exploración

`notebooks/01_exploracion_riesgo.ipynb` — recorrido reproducible por todas las señales.
Se versiona sin outputs; ejecútalo con Jupyter desde la raíz del repo.
