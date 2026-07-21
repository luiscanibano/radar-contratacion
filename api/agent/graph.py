"""Agente conversacional con la Claude API (bucle de tool use).

Empezamos con un bucle directo sobre el SDK de Anthropic, honesto y fácil de
razonar. Cuando el flujo crezca (memoria, múltiples herramientas, ramificación),
se migra a LangGraph sin cambiar las tools.
"""

from __future__ import annotations

import json

from anthropic import Anthropic

from api.agent.tools import SCHEMA_DESCRIPTION, SQL_TOOL, run_readonly_sql
from api.settings import settings

SYSTEM_PROMPT = f"""
Eres el analista de datos de "Radar de Contratación Pública". Respondes preguntas
sobre licitaciones del sector público español consultando los datos con la
herramienta `consultar_datos` (SQL de solo lectura sobre DuckDB).

Reglas:
- Siempre basa tus respuestas en datos reales obtenidos con la herramienta.
- Cita las cifras y explica de dónde salen. Nunca inventes números.
- Al hablar de posibles irregularidades, usa lenguaje de "señal a revisar",
  nunca acusaciones.

Esquema disponible:
{SCHEMA_DESCRIPTION}
""".strip()


def answer(question: str, max_turns: int = 5) -> str:
    client = Anthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": question}]

    for _ in range(max_turns):
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=1500,
            # cache_control cachea el prompt de sistema (esquema + reglas): es
            # idéntico en cada petición, así que a partir de la 2ª se sirve a
            # ~0,1x del coste. Verifica con response.usage.cache_read_input_tokens.
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[SQL_TOOL],
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "consultar_datos":
                result = run_readonly_sql(block.input["query"])
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str, ensure_ascii=False),
                    }
                )
        messages.append({"role": "user", "content": tool_results})

    return "No he podido resolver la consulta en el número de pasos permitido."
