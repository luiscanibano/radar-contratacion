# Imagen de Dagster (ingesta -> dbt -> embeddings -> alertas). Usa uv para
# instalar dependencias rápido. --all-extras: el job de alertas cuelga de la
# búsqueda híbrida (extra `search`, arrastra torch) y del email (extra `api`),
# además de la propia ingesta/transformación.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copia metadatos primero para aprovechar la caché de capas
COPY pyproject.toml README.md ./
RUN uv pip install --system --no-cache ".[orchestration,ingestion,transform,search,api]"

# Código de la aplicación
COPY api ./api
COPY ingestion ./ingestion
COPY orchestration ./orchestration
COPY search ./search
COPY transform ./transform

RUN cd transform && dbt deps

EXPOSE 3000
CMD ["dagster", "dev", "-m", "orchestration.definitions", "-h", "0.0.0.0", "-p", "3000"]
