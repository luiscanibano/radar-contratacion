# Imagen de la API. Usa uv para instalar dependencias rápido.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copia metadatos primero para aprovechar la caché de capas
COPY pyproject.toml README.md ./
RUN uv pip install --system --no-cache ".[api]"

# Código de la aplicación
COPY api ./api
COPY ingestion ./ingestion

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
