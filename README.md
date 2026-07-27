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
make init-db                  # crea las tablas de la app (usuarios, suscripciones, alertas...)

make ingest                   # descarga y carga un año de PLACSP en DuckDB
make transform                # dbt build: seeds + modelos + tests de calidad
make embeddings                # ingesta incremental de embeddings a Postgres+pgvector
make orchestrate              # Dagster en localhost:3000 (ingesta -> dbt con linaje)
make api                      # arranca FastAPI en localhost:8000
```

La API es multi-usuario con auth JWT propia: hay que registrar un usuario antes
de poder llamar a `/preguntar` o `/consultar` (`POST /auth/registro`). Stripe y
Resend (alertas por email) son opcionales en desarrollo — sin sus claves en
`.env`, `/billing/*` y el job de alertas fallan con un error explícito, pero el
resto de la API funciona igual (ver `.env.example`).

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

## Evals y observabilidad

Cada respuesta del agente deja una **traza** (turnos, herramientas usadas,
tokens, coste estimado, ratio de caché de prompt y latencias) en
`data/trazas.jsonl` y, si hay claves, en **Langfuse**.

La calidad se mide contra un **golden set** por dos vías que hay que superar a
la vez: una comprobación determinista de qué herramienta usó el agente y un
**LLM-as-judge** con un modelo más capaz que el suyo. La recuperación de la
búsqueda híbrida se mide aparte con métricas de IR (`recall@k`, `nDCG@k`, `MRR`).

```bash
make evals            # golden set completo (usa la API)
make evals-rapido     # solo comprobaciones deterministas, gratis
make evals-retrieval  # métricas de la búsqueda híbrida
```

Detalle en [evals/README.md](evals/README.md).

## Despliegue en producción (VPS)

Sin Alembic ni CI/CD todavía: el despliegue es manual y el esquema de Postgres
se aplica a mano (`make init-db` / `make embeddings`), igual que en desarrollo.

1. **DNS**: registro **A** de `radarcontratacion.com` apuntando al IP del VPS
   (necesario para que Caddy pueda emitir el certificado TLS con Let's Encrypt).
2. **En el VPS**: clonar el repo, copiar `.env.example` a `.env` y rellenar
   claves reales — incluidas `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` en
   modo **live** (no test) y `RESEND_API_KEY` (requiere el dominio verificado
   en Resend, ver `.env.example`). `DOMAIN=radarcontratacion.com`.
   ```bash
   git clone <repo> && cd radar-contratacion
   cp .env.example .env   # y editar con las claves reales
   docker compose up -d --build   # postgres + api (sin caddy, ver más abajo)
   ```
3. **Reverse proxy / TLS** — depende de si el VPS es solo para este proyecto:
   - **VPS dedicado**: `docker compose --profile standalone-caddy up -d caddy`
     levanta el Caddy incluido (usa `./Caddyfile` y `$DOMAIN` del `.env`).
   - **VPS compartido con otro proyecto que ya ocupa el 80/443** (un único
     reverse proxy para todo el host, nuestro caso real): no actives el
     perfil `standalone-caddy`. En su lugar:
     ```bash
     # Conecta el contenedor de la API a la red del Caddy ya existente
     docker network connect <red_del_otro_proyecto> radar-contratacion-api-1
     ```
     y añade un bloque de sitio a la Caddyfile de ese otro proyecto:
     ```caddyfile
     radarcontratacion.com {
         reverse_proxy radar-contratacion-api-1:8000
     }
     ```
     Recarga sin downtime del otro servicio con
     `docker exec <nombre_del_otro_caddy> caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile`.
     Caso real de este proyecto: VPS compartido con `fakenews-insight`, cuyo
     Caddy (`fakenews-caddy`) vive en la red `vps_default` — mismo patrón,
     sustituyendo los placeholders por esos nombres.
4. **Esquema de Postgres** (una vez el contenedor de Postgres esté sano). Ojo:
   `python` a secas, **no** `uv run python` — la imagen instala las
   dependencias con `uv pip install --system` (sin `.venv` de proyecto), así
   que `uv run` crearía una venv nueva desde cero sin los extras y fallaría
   con `ModuleNotFoundError: psycopg`. Asegúrate también de que `.env` tiene
   `POSTGRES_HOST=postgres` (el nombre del servicio en `docker-compose.yml`),
   no `localhost` — ese es el valor por defecto de `.env.example`, pensado
   para desarrollo fuera de Docker.
   ```bash
   docker compose run --rm api python -c "from api.db import init_schema; init_schema()"
   docker compose run --rm api python -c "from search.db import init_schema; init_schema()"
   ```
5. **Verificar**: `curl https://radarcontratacion.com/health` (TLS válido,
   `{"status": "ok"}`); registrar un usuario de prueba (`POST /auth/registro`)
   para confirmar que la tabla `usuarios` responde.
6. **Orquestación** (opcional, en el mismo VPS o aparte):
   `docker compose --profile orchestration up -d dagster` para la ingesta
   diaria, embeddings y el job de alertas.

Los webhooks de Stripe deben apuntar a
`https://radarcontratacion.com/billing/webhook` en el dashboard de Stripe
(modo live) — el secreto que da esa pantalla es el `STRIPE_WEBHOOK_SECRET`
de producción, distinto del de `stripe listen` en local.

## Roadmap (8 semanas)

1. ✅ Ingesta PLACSP + modelo relacional
2. ✅ Marts dbt + tests de calidad + orquestación Dagster
3. ✅ Modelos estadísticos (anomalías, importe con incertidumbre)
4. ✅ Capa vectorial + búsqueda híbrida
5. ✅ Agente conversacional (text-to-SQL + RAG)
6. ✅ Evals + observabilidad
7. ✅ Producto (auth, Stripe, alertas) + despliegue en VPS — en producción en
   [radarcontratacion.com](https://radarcontratacion.com), con Stripe (live) y
   Resend (dominio verificado) configurados
8. Servidor MCP + pulido + lanzamiento

## Aviso legal

Se usan exclusivamente datos abiertos oficiales. Contienen nombres de adjudicatarios;
el análisis se presenta de forma **agregada** y el módulo de riesgo describe **señales
estadísticas a revisar**, nunca acusaciones. Cumplimiento RGPD por diseño.
