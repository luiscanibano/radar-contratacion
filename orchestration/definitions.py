"""Definiciones Dagster: orquesta ingesta -> dbt como assets con linaje.

Arranca la UI con:  make orchestrate   (localhost:3000)

El schedule diario refresca los datos automáticamente en el VPS.
"""

from __future__ import annotations

import os
import subprocess

from dagster import (
    AssetExecutionContext,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
)

from ingestion.placsp_pipeline import run as run_placsp


@asset(group_name="ingesta", compute_kind="dlt")
def placsp_licitaciones(context: AssetExecutionContext) -> None:
    """Descarga y carga las licitaciones de PLACSP en DuckDB (esquema raw)."""
    years = [int(y) for y in os.getenv("PLACSP_YEARS", "2025").split(",")]
    context.log.info(f"Ingiriendo años: {years}")
    run_placsp(years=years, datasets=["licitaciones"])


@asset(group_name="transformacion", compute_kind="dbt", deps=[placsp_licitaciones])
def dbt_models(context: AssetExecutionContext) -> None:
    """Ejecuta los modelos y tests de dbt sobre los datos crudos."""
    for cmd in (["dbt", "run"], ["dbt", "test"]):
        result = subprocess.run(cmd, cwd="transform", capture_output=True, text=True)
        context.log.info(result.stdout)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)


daily_refresh_job = define_asset_job("daily_refresh", selection="*")

daily_schedule = ScheduleDefinition(
    job=daily_refresh_job,
    cron_schedule="0 6 * * *",  # cada día a las 06:00
)

defs = Definitions(
    assets=[placsp_licitaciones, dbt_models],
    jobs=[daily_refresh_job],
    schedules=[daily_schedule],
)
