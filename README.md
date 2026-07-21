# Radar de Contratación Pública

Plataforma de **inteligencia sobre contratación pública española**: ingiere los datos
abiertos de licitaciones y adjudicaciones del sector público, los modela, les aplica
análisis estadístico y los expone a través de un **agente conversacional** (lenguaje
natural → consultas sobre los datos) y un **servidor MCP**.

Proyecto de portfolio que cubre las tres disciplinas de extremo a extremo:

| Área | Qué demuestra | Herramientas |
|------|---------------|--------------|
| **Data Engineering** | Ingesta de datos sucios (ATOM/CODICE), modelado, orquestación | `dlt`, `DuckDB`, `dbt`, `Dagster` |
| **Data Science** | Rigor estadístico: incertidumbre, anomalías, segmentación | `scikit-learn`, `statsmodels`, `polars` |
| **AI Engineering** | Agente, RAG, evals, observabilidad, MCP | Claude API, `pgvector`, `Langfuse`, `Ragas`, `mcp` |

Diseñado para correr entero en un **VPS modesto (4 vCPU / 8 GB)** con Docker Compose.

---

## Arquitectura

```
Fuentes                Ingesta            Almacén analítico        Transformación
PLACSP (ATOM/CODICE) ─► dlt ────────────► DuckDB ────────────────► dbt (staging→marts)
TED (eForms/CSV)     ─┘                     │                          │
                                            │  orquestación: Dagster   │
                                            ▼                          ▼
                                   Postgres + pgvector  ◄──── embeddings + modelos DS
                                            │
   Next.js / Streamlit ◄── FastAPI ── Agente (Claude API) ── tools: text-to-SQL · búsqueda híbrida · RAG
                                            │
                                    Servidor MCP  ─► Claude Desktop / Code
```

Ver [docs/architecture.md](docs/architecture.md) para el detalle.

## Estructura del repositorio

```
ingestion/       Pipelines dlt (PLACSP, TED) + catálogo de fuentes reales
transform/       Proyecto dbt-duckdb (staging → intermediate → marts)
orchestration/   Definiciones Dagster (assets + schedules)
analytics/       Modelos estadísticos y notebooks (DS)
api/             FastAPI + agente conversacional (Claude API)
mcp_server/      Servidor MCP que expone los datos como herramientas
evals/           Golden set + arnés de evaluación del agente
docs/            Arquitectura y documentación
data/            DuckDB local y artefactos (git-ignored)
```

## Puesta en marcha (desarrollo)

Requisitos: [uv](https://docs.astral.sh/uv/), Docker, y una `ANTHROPIC_API_KEY`.

```bash
uv sync --all-extras          # instala dependencias
cp .env.example .env          # rellena las claves
docker compose up -d postgres # levanta Postgres + pgvector

make ingest                   # descarga y carga un año de PLACSP en DuckDB
make transform                # ejecuta los modelos dbt
make api                      # arranca FastAPI en localhost:8000
```

## Roadmap (8 semanas)

1. Ingesta PLACSP + modelo relacional
2. Marts dbt + tests de calidad + orquestación Dagster
3. Modelos estadísticos (anomalías, importe con incertidumbre)
4. Capa vectorial + búsqueda híbrida
5. Agente conversacional (text-to-SQL + RAG)
6. Evals + observabilidad
7. Producto (auth, Stripe, alertas) + despliegue en VPS
8. Servidor MCP + pulido + lanzamiento

## Aviso legal

Se usan exclusivamente datos abiertos oficiales. Contienen nombres de adjudicatarios;
el análisis se presenta de forma **agregada** y el módulo de riesgo describe **señales
estadísticas a revisar**, nunca acusaciones. Cumplimiento RGPD por diseño.
