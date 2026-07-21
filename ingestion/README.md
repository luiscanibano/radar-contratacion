# Ingesta

Descarga los datos abiertos de PLACSP (y, más adelante, TED) y los aterriza en
DuckDB (`data/radar.duckdb`, esquema `raw`).

## Fuentes

Ver [`sources.py`](sources.py) para el catálogo con las URLs oficiales. PLACSP
publica **ZIP anuales** que contienen ficheros `.atom` paginados (~500 `<entry>`
cada uno) en **CODICE 2.07**. Ojo: el ZIP anual de licitaciones pesa **~2 GB**
(~1400 ficheros `.atom`), por eso se descarga en streaming a disco y se cachea.

## Ejecución

```bash
make ingest                                   # usa PLACSP_YEARS del .env
uv run python -m ingestion.placsp_pipeline 2024 2025
```

Variables de entorno útiles:

| Variable | Efecto |
|----------|--------|
| `PLACSP_YEARS` | años a descargar (coma-separados; por defecto `2025`) |
| `PLACSP_MAX_FILES` | procesa solo los N primeros `.atom` del ZIP (dev/CI rápido) |
| `PLACSP_CACHE_DIR` | dónde cachear los ZIP (por defecto `data/cache/`) |
| `DUCKDB_PATH` | fichero DuckDB destino (por defecto `data/radar.duckdb`) |

Prueba rápida sin cargar un año entero:

```bash
PLACSP_MAX_FILES=10 uv run python -m ingestion.placsp_pipeline 2025
```

## Modelo relacional (esquema `raw`)

[`codice.py`](codice.py) extrae un **registro anidado** por expediente que dlt
normaliza en tres tablas con clave foránea (`_dlt_id` ← `_dlt_parent_id`):

```
raw.licitaciones                 cabecera: expediente, estado, objeto, CPV,
                                 importes, órgano (NIF/DIR3), NUTS, procedimiento...
raw.licitaciones__lotes          un lote por fila (objeto, CPV, presupuesto)
raw.licitaciones__adjudicaciones un resultado por fila (adjudicatario+NIF,
                                 importe, nº ofertas, PYME, fecha)
```

Rutas CODICE validadas contra ficheros reales de 2025. Tests de regresión en
[`tests/test_codice.py`](tests/test_codice.py) sobre un fixture recortado.

## Cómo explorar un fichero real

```python
import io, zipfile, httpx
from ingestion.sources import PLACSP_DATASETS

url = PLACSP_DATASETS["licitaciones"].zip_url(2025)
zf = zipfile.ZipFile(io.BytesIO(httpx.get(url, timeout=120, follow_redirects=True).content))
print(zf.namelist()[:3])
print(zf.read(zf.namelist()[0])[:2000].decode())   # inspecciona el XML CODICE
```

## Siguiente paso

Una vez en `raw`, el modelado y la limpieza se hacen en [`../transform`](../transform)
con dbt (staging → intermediate → marts). Pendientes conocidos: decodificar los
códigos de lista CODICE (tipo de contrato, procedimiento, resultado) a etiquetas,
capturar los `<at:deleted-entry>` (expedientes anulados) y descomponer las UTE.
