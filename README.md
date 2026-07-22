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
make transform                # dbt build: seeds + modelos + tests de calidad
make orchestrate              # Dagster en localhost:3000 (ingesta -> dbt con linaje)
make api                      # arranca FastAPI en localhost:8000
```

## Modelo dbt

Capas `staging → intermediate → marts` sobre el DuckDB `raw`:

- **staging** (views): deduplica los expedientes a su última versión publicada y
  tipa importes/fechas — `stg_placsp__licitaciones`, `…__lotes`, `…__adjudicaciones`.
- **intermediate** (ephemeral): `int_adjudicaciones_enriquecidas` cruza cada
  adjudicación con su expediente y su lote y calcula la *baja* sobre presupuesto.
- **marts** (tablas): `fct_licitaciones`, `fct_adjudicaciones`, `dim_organo`,
  `dim_adjudicatario`. Las etiquetas de códigos (estado, tipo, procedimiento)
  viven en **seeds** (`ref_*`).
- **calidad**: tests genéricos (`not_null`, `unique`, `accepted_values`,
  `relationships`), rangos con `dbt_utils` y tests singulares de negocio.

Orquestado con Dagster + `dagster-dbt`: la ingesta (dlt) y cada modelo/seed/test
de dbt son assets con linaje; los tests aparecen como *asset checks*.

## Roadmap (8 semanas)

1. ✅ Ingesta PLACSP + modelo relacional
2. ✅ Marts dbt + tests de calidad + orquestación Dagster
3. ✅ Modelos estadísticos (anomalías, importe con incertidumbre)
4. ✅ Capa vectorial + búsqueda híbrida
5. 🔄 Agente conversacional (text-to-SQL + RAG) — wiring y validación hechos, quedan edge cases
6. Evals + observabilidad
7. Producto (auth, Stripe, alertas) + despliegue en VPS
8. Servidor MCP + pulido + lanzamiento

## Aviso legal

Se usan exclusivamente datos abiertos oficiales. Contienen nombres de adjudicatarios;
el análisis se presenta de forma **agregada** y el módulo de riesgo describe **señales
estadísticas a revisar**, nunca acusaciones. Cumplimiento RGPD por diseño.
