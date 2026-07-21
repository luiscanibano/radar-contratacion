"""Arnés de evaluación del agente.

Recorre el golden set, obtiene la respuesta del agente y la puntúa con
LLM-as-judge (Claude evalúa si la respuesta cumple el criterio). En la Semana 6
se integra con Langfuse para trazar cada ejecución y con Ragas para métricas RAG.
"""

from __future__ import annotations

import json
from pathlib import Path

from anthropic import Anthropic

from api.agent.graph import answer
from api.settings import settings

GOLDEN = Path(__file__).parent / "golden_set.jsonl"

JUDGE_PROMPT = """Eres un evaluador. Dada una PREGUNTA, un CRITERIO de correción y
la RESPUESTA de un agente, responde solo con "PASA" o "FALLA" y una frase breve.

PREGUNTA: {pregunta}
CRITERIO: {criterio}
RESPUESTA: {respuesta}
"""


def judge(client: Anthropic, pregunta: str, criterio: str, respuesta: str) -> str:
    msg = client.messages.create(
        model=settings.claude_model,
        max_tokens=150,
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(
                    pregunta=pregunta, criterio=criterio, respuesta=respuesta
                ),
            }
        ],
    )
    return msg.content[0].text.strip()


def main() -> None:
    client = Anthropic(api_key=settings.anthropic_api_key)
    casos = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines()]

    pasa = 0
    for caso in casos:
        respuesta = answer(caso["pregunta"])
        veredicto = judge(client, caso["pregunta"], caso["criterio"], respuesta)
        estado = "PASA" if veredicto.upper().startswith("PASA") else "FALLA"
        pasa += estado == "PASA"
        print(f"[{estado}] {caso['pregunta']}\n        -> {veredicto}\n")

    print(f"Resultado: {pasa}/{len(casos)} casos superados.")


if __name__ == "__main__":
    main()
