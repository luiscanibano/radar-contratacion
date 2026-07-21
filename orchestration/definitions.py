"""Definiciones Dagster: orquesta ingesta -> dbt con linaje por modelo.

La ingesta (dlt) es un asset; cada modelo, seed y test de dbt es su propio asset
gracias a `dagster-dbt`, encadenados por la fuente `raw` que llena la ingesta.

Arranca la UI con:  make orchestrate   (localhost:3000)
El schedule diario refresca los datos automáticamente en el VPS.
"""

import os
import sys
from pathlib import Path

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSpec,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
    multi_asset,
)
from dagster_dbt import (
    DbtCliResource,
    DbtProject,
    dbt_assets,
    get_asset_key_for_model,
)

from ingestion.placsp_pipeline import run as run_placsp

# --- Proyecto dbt -----------------------------------------------------------
# El ejecutable dbt vive en el mismo Scripts/ que este intérprete (venv). Lo
# resolvemos explícitamente y lo dejamos en PATH para que dagster-dbt lo localice.
DBT_EXECUTABLE = str(Path(sys.executable).with_name("dbt.exe" if os.name == "nt" else "dbt"))
os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")

TRANSFORM_DIR = Path(__file__).parent.parent / "transform"
dbt_project = DbtProject(project_dir=TRANSFORM_DIR)
dbt_project.prepare_if_dev()  # genera el manifest al lanzar `dagster dev`

# Las tres fuentes `raw.*` de dbt las produce una sola ingesta dlt. Modelamos la
# ingesta como un multi-asset que materializa esas tres claves, de modo que el
# linaje conecta ingesta -> modelos dbt sin colisionar claves.
RAW_TABLES = ("licitaciones", "licitaciones__lotes", "licitaciones__adjudicaciones")
RAW_SPECS = [
    AssetSpec(key=AssetKey(["raw", t]), group_name="ingesta", kinds={"dlt"}) for t in RAW_TABLES
]


# --- Ingesta ----------------------------------------------------------------
@multi_asset(specs=RAW_SPECS)
def raw_placsp(context: AssetExecutionContext):
    """Descarga y carga PLACSP en DuckDB (esquema raw) con dlt."""
    years = [int(y) for y in os.getenv("PLACSP_YEARS", "2025").split(",")]
    context.log.info(f"Ingiriendo años: {years}")
    run_placsp(years=years, datasets=["licitaciones"])


# --- Transformación dbt (un asset por modelo/seed/test) ---------------------
@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_radar(context: AssetExecutionContext, dbt: DbtCliResource):
    """Ejecuta `dbt build` (seeds + modelos + tests) con linaje en Dagster."""
    yield from dbt.cli(["build"], context=context).stream()


# --- Capa vectorial ---------------------------------------------------------
# La ingesta de embeddings cuelga del mart `fct_licitaciones`: cuando dbt lo
# refresca, se re-embeben (incrementalmente) los expedientes nuevos o cambiados
# y se hace upsert en Postgres+pgvector.
@asset(
    deps=[get_asset_key_for_model([dbt_radar], "fct_licitaciones")],
    group_name="vectorial",
    kinds={"postgres"},
)
def licitacion_embeddings(context: AssetExecutionContext):
    """Ingesta incremental de embeddings (marts DuckDB -> Postgres+pgvector)."""
    from search.ingest import ingest  # import diferido: no cargar torch al definir

    resultado = ingest()
    context.log.info(
        f"Embeddings: {resultado.embebidos} embebidos, "
        f"{resultado.sin_cambios} sin cambios (total {resultado.total})."
    )
    context.add_output_metadata(
        {
            "embebidos": resultado.embebidos,
            "sin_cambios": resultado.sin_cambios,
            "total": resultado.total,
        }
    )


# --- Job + schedule ---------------------------------------------------------
daily_refresh_job = define_asset_job("daily_refresh", selection="*")

daily_schedule = ScheduleDefinition(
    job=daily_refresh_job,
    cron_schedule="0 6 * * *",  # cada día a las 06:00
)

defs = Definitions(
    assets=[raw_placsp, dbt_radar, licitacion_embeddings],
    jobs=[daily_refresh_job],
    schedules=[daily_schedule],
    resources={"dbt": DbtCliResource(project_dir=dbt_project, dbt_executable=DBT_EXECUTABLE)},
)
