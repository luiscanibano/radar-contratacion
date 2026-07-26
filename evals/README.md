# Evals y observabilidad

Dos cosas distintas que suelen confundirse:

- **Evals** (`evals/`): ¿el agente responde bien? Se mide contra un conjunto
  fijo de casos con criterio de corrección.
- **Observabilidad** (`api/observabilidad.py`): ¿qué hizo, cuánto tardó y
  cuánto costó *cada* respuesta, también en producción?

## Evaluación del agente

```bash
make evals          # golden set completo (llama a la API: cuesta dinero)
make evals-rapido   # solo comprobaciones deterministas, sin juez LLM (gratis)
```

Cada caso se puntúa por dos vías independientes y tiene que superar **las dos**:

1. **Comprobación determinista de herramientas.** Cada caso del golden set
   puede declarar `tools_esperadas` y `tools_prohibidas`. Sin varianza y sin
   coste: si un caso cuantitativo deja de llamar a `consultar_datos`, es una
   regresión real aunque el texto suene bien. Es lo que impide que el agente
   apruebe respondiendo "de memoria" sin mirar los datos.
2. **LLM-as-judge.** Un modelo distinto y más capaz que el del agente
   (`JUDGE_MODEL`, por defecto Opus 4.8 frente al Sonnet 5 del agente) decide
   si la respuesta cumple el criterio. Devuelve un veredicto **estructurado**
   (`structured outputs`), no texto libre que haya que adivinar. Si el juez
   falla por red, el caso se marca `ERROR_JUEZ` y **no** cuenta como suspenso
   del agente.

El comando sale con código 1 si la tasa de aprobados baja de `UMBRAL_APROBADO`
(80%), para poder colgarlo de un CI. Cada ejecución deja un informe JSON en
`evals/informes/` con coste, latencia y desglose por categoría.

Categorías del golden set: `cuantitativa`, `conceptual`, `ambiguedad`
(el agente debe pedir aclaración en vez de adivinar), `limites` (no inventar,
no acusar, no fingir que escribe en la base de datos).

## Evaluación de la búsqueda híbrida (recuperación)

El juez LLM no puede medir si el recuperador pone lo relevante *arriba*. Eso se
mide con métricas de IR sobre un conjunto etiquetado a mano:

```bash
uv run python -m evals.retrieval --preparar "mantenimiento de jardines"  # 1. candidatos
#    -> pegar los entry_id relevantes en evals/retrieval_set.jsonl        # 2. etiquetar
make evals-retrieval                                                      # 3. medir
```

Métricas: `recall@k`, `precision@k`, `nDCG@k` (premia los aciertos arriba) y
`MRR` (posición del primer acierto). Requiere Postgres levantado y el extra
`search`.

> **Sobre Ragas:** el plan original era usar Ragas para esta parte. Su versión
> actual (0.4.3) no llega ni a importarse con el stack de langchain instalado
> (`langchain_community.chat_models.vertexai` ya no existe, y
> `langchain-community` está en proceso de retirada). Las métricas no-LLM de
> Ragas para recuperación son exactamente estas cuatro fórmulas, así que están
> implementadas en `evals/retrieval.py` — unas 40 líneas, con tests propios y
> sin dependencia rota.

## Trazas

`responder()` (en `api/agent/graph.py`) devuelve, además del texto, una `Traza`
con turnos, herramientas usadas, tokens, coste estimado, ratio de caché y
latencias. Se emite a dos sitios:

- **`data/trazas.jsonl`**: siempre, sin configurar nada.
- **Langfuse**: solo si hay `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`.

La emisión nunca lanza excepciones: si Langfuse está caído, la respuesta ya se
le dio al usuario y no se puede perder por un fallo de telemetría.

El **ratio de caché** es la métrica a vigilar: el `SYSTEM_PROMPT` va con
`cache_control`, así que a partir de la segunda llamada debería servirse a ~0,1x
de coste. Si `ratio_cache` se queda en 0 ejecución tras ejecución, algo está
invalidando el prefijo del prompt.

Los precios viven en `PRECIOS_USD_POR_MTOK` (`api/observabilidad.py`) y hay que
actualizarlos al cambiar de modelo; un modelo sin precio conocido lanza `KeyError`
en vez de fingir que es gratis.
