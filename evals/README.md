# Evals

Evaluación de la calidad del agente. Empezamos con un **golden set** de preguntas
con criterios de corrección y un juez LLM (`run.py`). En la Semana 6 se amplía con:

- **Métricas de exactitud SQL** (¿la consulta generada devuelve lo correcto?).
- **Ragas** para las respuestas con RAG sobre pliegos (fidelidad, relevancia).
- **Langfuse** para trazar cada ejecución (coste, latencia, tokens) y detectar
  regresiones al cambiar prompts o modelo.

```bash
make evals
```
