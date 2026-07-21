# Ingesta

Descarga los datos abiertos de PLACSP (y, más adelante, TED) y los aterriza en
DuckDB (`data/radar.duckdb`, esquema `raw`).

## Fuentes

Ver [`sources.py`](sources.py) para el catálogo con las URLs oficiales. PLACSP
publica **ZIP anuales** que contienen ficheros `.atom` paginados (máx. 500
entradas cada uno) en **CODICE 2.07**.

## Ejecución

```bash
make ingest                 # usa PLACSP_YEARS del .env
uv run python -m ingestion.placsp_pipeline 2024 2025
```

## Cómo explorar un fichero real (recomendado antes de refinar el parser)

```python
import io, zipfile, httpx
from ingestion.sources import PLACSP_DATASETS

url = PLACSP_DATASETS["licitaciones"].zip_url(2025)
zf = zipfile.ZipFile(io.BytesIO(httpx.get(url, timeout=120, follow_redirects=True).content))
print(zf.namelist()[:3])
print(zf.read(zf.namelist()[0])[:2000].decode())   # inspecciona el XML CODICE
```

El parser de [`codice.py`](codice.py) cubre los campos de alto valor. Amplíalo
con las rutas que veas en los ficheros reales (lotes, adjudicatario, importe de
adjudicación, fechas de presentación, ubicación NUTS...).

## Siguiente paso

Una vez en `raw`, el modelado y la limpieza se hacen en [`../transform`](../transform)
con dbt (staging → intermediate → marts).
