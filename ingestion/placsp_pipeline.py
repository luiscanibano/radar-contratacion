"""Pipeline dlt: descarga los ZIP anuales de PLACSP, parsea los .atom embebidos
y carga los registros en DuckDB.

Uso:
    uv run python -m ingestion.placsp_pipeline            # años de PLACSP_YEARS
    uv run python -m ingestion.placsp_pipeline 2023 2024  # años concretos
"""

from __future__ import annotations

import io
import os
import sys
import zipfile
from collections.abc import Iterator
from typing import Any

import dlt
import httpx

from ingestion.codice import parse_atom_bytes
from ingestion.sources import PLACSP_DATASETS, PlacspDataset


def _download_and_parse(dataset: PlacspDataset, year: int) -> Iterator[dict[str, Any]]:
    """Descarga el ZIP de un dataset/año y hace yield de cada entrada parseada."""
    url = dataset.zip_url(year)
    with httpx.stream("GET", url, timeout=120, follow_redirects=True) as resp:
        resp.raise_for_status()
        buffer = io.BytesIO(resp.read())

    with zipfile.ZipFile(buffer) as zf:
        for name in zf.namelist():
            if not name.endswith(".atom"):
                continue
            with zf.open(name) as fh:
                for record in parse_atom_bytes(fh.read()):
                    record["_dataset"] = dataset.key
                    record["_year"] = year
                    record["_source_file"] = name
                    yield record


@dlt.source(name="placsp")
def placsp_source(years: list[int], datasets: list[str] | None = None):
    """Un recurso dlt por cada dataset de PLACSP solicitado."""
    keys = datasets or ["licitaciones"]
    for key in keys:
        dataset = PLACSP_DATASETS[key]

        @dlt.resource(name=key, write_disposition="replace")
        def _resource(dataset: PlacspDataset = dataset) -> Iterator[dict[str, Any]]:
            for year in years:
                if year < dataset.first_year:
                    continue
                yield from _download_and_parse(dataset, year)

        yield _resource


def run(years: list[int], datasets: list[str] | None = None) -> None:
    pipeline = dlt.pipeline(
        pipeline_name="placsp",
        destination="duckdb",
        dataset_name="raw",
    )
    load_info = pipeline.run(placsp_source(years=years, datasets=datasets))
    print(load_info)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        env_years = os.getenv("PLACSP_YEARS", "2025")
        years = [int(y.strip()) for y in env_years.split(",")]
    run(years=years, datasets=["licitaciones"])
