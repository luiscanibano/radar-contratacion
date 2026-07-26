"""Tests del bucle del agente (api/agent/graph.py), centrados en edge cases:
agotar max_turns, tool_use mal formado y fallos de la API de Anthropic."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import httpx
from anthropic import APIConnectionError

from api.agent.graph import answer, responder


def _texto(texto: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=texto)


def _tool_use(name: str, input_: dict, id_: str = "toolu_1") -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", name=name, input=input_, id=id_)


def _respuesta(stop_reason: str, content: list) -> SimpleNamespace:
    return SimpleNamespace(stop_reason=stop_reason, content=content)


def test_respuesta_directa_sin_tool_use():
    respuesta = _respuesta("end_turn", [_texto("Hola, ¿en qué te ayudo?")])
    with patch("api.agent.graph.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.messages.create.return_value = respuesta
        assert answer("hola") == "Hola, ¿en qué te ayudo?"


def test_agota_max_turns_devuelve_mensaje_generico():
    # El modelo insiste en llamar a una tool desconocida en cada turno: el bucle
    # nunca ve stop_reason distinto de "tool_use" y debe cortar por max_turns
    # en vez de colgarse.
    respuesta = _respuesta("tool_use", [_tool_use("tool_inexistente", {})])
    with patch("api.agent.graph.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.messages.create.return_value = respuesta
        resultado = answer("pregunta imposible", max_turns=2)
    assert resultado == "No he podido resolver la consulta en el número de pasos permitido."
    assert mock_anthropic.return_value.messages.create.call_count == 2


def test_tool_use_con_input_incompleto_no_revienta():
    # "query" es obligatorio en el schema, pero un tool_use truncado o
    # alucinado podría no incluirlo: no debe tumbar el agente con un KeyError.
    llamada_mal_formada = _respuesta("tool_use", [_tool_use("consultar_datos", {})])
    respuesta_final = _respuesta("end_turn", [_texto("No pude completar la consulta.")])
    with patch("api.agent.graph.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.messages.create.side_effect = [
            llamada_mal_formada,
            respuesta_final,
        ]
        resultado = answer("pregunta rara")
    assert resultado == "No pude completar la consulta."


def test_ambas_tools_fallan_el_agente_sigue_respondiendo():
    llamada = _respuesta(
        "tool_use",
        [
            _tool_use("consultar_datos", {"query": "select * from tabla_inexistente"}, "toolu_1"),
            _tool_use("buscar_licitaciones", {"consulta": "asfaltado"}, "toolu_2"),
        ],
    )
    respuesta_final = _respuesta("end_turn", [_texto("No encontré datos con ninguna herramienta.")])
    with (
        patch("api.agent.graph.Anthropic") as mock_anthropic,
        patch("api.agent.graph.run_readonly_sql", return_value={"error": "tabla no existe"}),
        patch(
            "api.agent.graph.buscar_licitaciones",
            return_value={"error": "backend no disponible"},
        ),
    ):
        mock_anthropic.return_value.messages.create.side_effect = [llamada, respuesta_final]
        resultado = answer("pregunta sin datos")
    assert resultado == "No encontré datos con ninguna herramienta."


def test_error_de_conexion_con_la_api_da_respuesta_amigable():
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    error = APIConnectionError(request=request)
    with patch("api.agent.graph.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.messages.create.side_effect = error
        resultado = answer("hola")
    assert "No he podido contactar con el modelo" in resultado


# --- traza (semana 6) --------------------------------------------------------


def test_la_traza_registra_turnos_tools_y_tokens():
    uso = SimpleNamespace(
        input_tokens=100,
        output_tokens=20,
        cache_read_input_tokens=900,
        cache_creation_input_tokens=0,
    )
    llamada = _respuesta("tool_use", [_tool_use("consultar_datos", {"query": "select 1"})])
    llamada.usage = uso
    final = _respuesta("end_turn", [_texto("Hay 42 licitaciones.")])
    final.usage = uso

    with (
        patch("api.agent.graph.Anthropic") as mock_anthropic,
        patch("api.agent.graph.run_readonly_sql", return_value={"row_count": 42, "rows": []}),
    ):
        mock_anthropic.return_value.messages.create.side_effect = [llamada, final]
        texto, traza = responder("¿cuántas licitaciones?")

    assert texto == "Hay 42 licitaciones."
    assert traza.turnos == 2
    assert traza.tools_usadas == ["consultar_datos"]
    assert traza.tools[0].ok and traza.tools[0].filas == 42
    assert traza.tokens_entrada == 2000  # (100 + 900) x 2 llamadas
    assert traza.ratio_cache == 0.9
    assert traza.coste_usd > 0
    assert traza.error is None


def test_la_traza_marca_la_tool_fallida_y_el_error_de_api():
    llamada = _respuesta(
        "tool_use", [_tool_use("consultar_datos", {"query": "select * from nope"})]
    )
    final = _respuesta("end_turn", [_texto("No pude consultar.")])
    with (
        patch("api.agent.graph.Anthropic") as mock_anthropic,
        patch("api.agent.graph.run_readonly_sql", return_value={"error": "tabla no existe"}),
    ):
        mock_anthropic.return_value.messages.create.side_effect = [llamada, final]
        _, traza = responder("pregunta mala")
    assert traza.tools[0].ok is False
    assert traza.tools[0].error == "tabla no existe"


def test_la_traza_registra_el_agotamiento_de_max_turns():
    respuesta = _respuesta("tool_use", [_tool_use("tool_inexistente", {})])
    with patch("api.agent.graph.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.messages.create.return_value = respuesta
        _, traza = responder("imposible", max_turns=2)
    assert traza.turnos == 2
    assert "max_turns" in (traza.error or "")


def test_responder_no_persiste_nada_por_su_cuenta():
    # Emitir la traza es del que llama (api/main.py, evals/run.py): así los
    # tests no escriben en disco ni intentan hablar con Langfuse.
    final = _respuesta("end_turn", [_texto("hola")])
    with (
        patch("api.agent.graph.Anthropic") as mock_anthropic,
        patch("api.observabilidad.emitir") as mock_emitir,
    ):
        mock_anthropic.return_value.messages.create.return_value = final
        responder("hola")
    mock_emitir.assert_not_called()
