"""Pipeline dlt: descarga los ZIP anuales de PLACSP, parsea los `.atom` embebidos
y carga los registros (con lotes y adjudicaciones anidados) en DuckDB.

Los ZIP anuales son enormes (el de licitaciones 2025 pesa ~2 GB con ~1400 ficheros
`.atom`). Por eso:

  * el ZIP se **descarga en streaming a disco** (caché `data/cache/`), nunca a RAM,
    y se reutiliza si ya está descargado;
  * el ZIP se abre desde disco y cada `.atom` se parsea de uno en uno.

Uso:
    uv run python -m ingestion.placsp_pipeline            # años de PLACSP_YEARS
    uv run python -m ingestion.placsp_pipeline 2023 2024  # años concretos

Variables de entorno útiles en desarrollo:
    PLACSP_YEARS       años a descargar (coma-separados; por defecto 2025)
    PLACSP_MAX_FILES   procesa solo los N primeros `.atom` de cada ZIP (para probar
                       rápido sin cargar el año entero)
    PLACSP_CACHE_DIR   dónde cachear los ZIP descargados (por defecto data/cache)
"""

from __future__ import annotations

import os
import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import dlt
import httpx

from ingestion.codice import parse_atom_bytes
from ingestion.sources import PLACSP_DATASETS, PlacspDataset

CACHE_DIR = Path(os.getenv("PLACSP_CACHE_DIR", "data/cache"))


def _cached_zip(dataset: PlacspDataset, year: int) -> Path:
    """Descarga (en streaming a disco) el ZIP del dataset/año, o lo reutiliza."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target = CACHE_DIR / f"{dataset.file_prefix}_{year}.zip"
    if target.exists() and target.stat().st_size > 0:
        return target

    url = dataset.zip_url(year)
    tmp = target.with_suffix(".zip.part")
    print(f"  descargando {url}")
    with httpx.stream("GET", url, timeout=300, follow_redirects=True) as resp:
        resp.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_bytes(chunk_size=1 << 20):
                fh.write(chunk)
    tmp.replace(target)
    print(f"  cacheado {target} ({target.stat().st_size / 1e6:.0f} MB)")
    return target


def _iter_records(
    dataset: PlacspDataset, year: int, max_files: int | None
) -> Iterator[dict[str, Any]]:
    """Hace yield de cada registro parseado del ZIP de un dataset/año."""
    zip_path = _cached_zip(dataset, year)
    with zipfile.ZipFile(zip_path) as zf:
        atoms = [n for n in zf.namelist() if n.endswith(".atom")]
        if max_files is not None:
            atoms = atoms[:max_files]
        for name in atoms:
            for record in parse_atom_bytes(zf.read(name)):
                record["_dataset"] = dataset.key
                record["_year"] = year
                record["_source_file"] = name
                yield record


@dlt.source(name="placsp")
def placsp_source(
    years: list[int],
    datasets: list[str] | None = None,
    max_files: int | None = None,
):
    """Un recurso dlt por cada dataset de PLACSP solicitado."""
    keys = datasets or ["licitaciones"]
    for key in keys:
        dataset = PLACSP_DATASETS[key]

        @dlt.resource(name=key, write_disposition="replace", primary_key="entry_id")
        def _resource(dataset: PlacspDataset = dataset) -> Iterator[dict[str, Any]]:
            for year in years:
                if year < dataset.first_year:
                    continue
                yield from _iter_records(dataset, year, max_files)

        yield _resource


def run(
    years: list[int],
    datasets: list[str] | None = None,
    max_files: int | None = None,
) -> None:
    db_path = os.getenv("DUCKDB_PATH", "data/radar.duckdb")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    pipeline = dlt.pipeline(
        pipeline_name="placsp",
        destination=dlt.destinations.duckdb(db_path),
        dataset_name="raw",
    )
    load_info = pipeline.run(placsp_source(years=years, datasets=datasets, max_files=max_files))
    print(load_info)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        env_years = os.getenv("PLACSP_YEARS", "2025")
        years = [int(y.strip()) for y in env_years.split(",")]

    env_max = os.getenv("PLACSP_MAX_FILES")
    max_files = int(env_max) if env_max else None
    run(years=years, datasets=["licitaciones"], max_files=max_files)
