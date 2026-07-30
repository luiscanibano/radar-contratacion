# Etapa 1: build de la interfaz web (Vite + React + Tailwind). Genera
# web/dist con las 4 páginas (landing, app, billing/exito, billing/cancelado)
# más los assets con hash (JS, CSS, fuentes autohospedadas).
FROM node:20-slim AS web-build

WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
RUN npm run build

# Etapa 2: la API. Usa uv para instalar dependencias rápido.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copia metadatos primero para aprovechar la caché de capas
COPY pyproject.toml README.md ./
# 'search' añade la tool de búsqueda híbrida (arrastra sentence-transformers/torch)
# 'mcp' añade el servidor MCP montado bajo /mcp (ver api/main.py)
RUN uv pip install --system --no-cache ".[api,search,mcp]"

# Código de la aplicación
COPY api ./api
COPY ingestion ./ingestion
COPY search ./search
COPY mcp_server ./mcp_server

# Interfaz web construida: sustituye a los HTML/fuentes estáticos que antes
# vivían directamente en api/static (ver api/main.py).
COPY --from=web-build /web/dist ./api/static

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
