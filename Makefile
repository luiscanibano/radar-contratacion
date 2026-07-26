.PHONY: help install ingest transform test-dbt init-db orchestrate api mcp evals evals-rapido evals-retrieval lint

help:  ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Instala dependencias con uv y los paquetes dbt
	uv sync --all-extras
	cd transform && uv run dbt deps

ingest:  ## Descarga y carga los años configurados de PLACSP en DuckDB
	uv run python -m ingestion.placsp_pipeline

transform:  ## Ejecuta el flujo dbt completo: seeds + modelos + tests
	cd transform && uv run dbt build

test-dbt:  ## Ejecuta solo los tests de calidad de dbt
	cd transform && uv run dbt test

embeddings:  ## Ingesta incremental de embeddings a Postgres+pgvector
	uv run python -m search.ingest

init-db:  ## Crea/actualiza las tablas de la app (usuarios, suscripciones, alertas...) en Postgres
	uv run python -c "from api.db import init_schema; init_schema()"

orchestrate:  ## Levanta Dagster en localhost:3000
	uv run dagster dev -m orchestration.definitions

api:  ## Arranca FastAPI en localhost:8000
	uv run uvicorn api.main:app --reload --port 8000

mcp:  ## Arranca el servidor MCP (stdio)
	uv run python -m mcp_server.server

evals:  ## Ejecuta la suite de evaluación del agente (LLM-as-judge + tools)
	uv run python -m evals.run

evals-rapido:  ## Evals sin juez LLM: solo comprobaciones deterministas (gratis)
	uv run python -m evals.run --sin-juez

evals-retrieval:  ## Métricas de recuperación de la búsqueda híbrida
	uv run python -m evals.retrieval

lint:  ## Formatea y revisa el código
	uv run ruff format . && uv run ruff check --fix .
