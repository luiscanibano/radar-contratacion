"""Tests de la capa de trazas: coste, tokens, ratio de caché y robustez de la emisión."""

from __future__ import annotations

import json
from datetime import date

import pytest

from api.observabilidad import (
    LlamadaModelo,
    Traza,
    UsoTool,
    emitir,
    precios,
)


def test_precio_intro_de_sonnet5_caduca():
    # El precio de lanzamiento acaba el 31/08/2026: antes se aplica, después no.
    assert precios("claude-sonnet-5", date(2026, 7, 26)) == (2.00, 10.00)
    assert precios("claude-sonnet-5", date(2026, 9, 1)) == (3.00, 15.00)


def test_modelo_sin_precio_conocido_avisa():
    # Silenciar esto con un 0.0 haría que el coste pareciera gratis al cambiar
    # de modelo, que es justo cuando más importa mirarlo.
    with pytest.raises(KeyError, match="Modelo sin precio conocido"):
        precios("claude-modelo-inventado")


def test_coste_aplica_los_multiplicadores_de_cache():
    llamada = LlamadaModelo(
        turno=1,
        input_tokens=1_000_000,
        output_tokens=0,
        cache_read_input_tokens=1_000_000,
        cache_creation_input_tokens=1_000_000,
    )
    # 1M a precio pleno + 1M a 0,1x + 1M a 1,25x = 2,35M tokens equivalentes.
    coste = llamada.coste_usd("claude-sonnet-5", date(2026, 9, 1))
    assert coste == pytest.approx(2.35 * 3.00)


def test_ratio_cache_y_tokens_agregan_todas_las_llamadas():
    traza = Traza(pregunta="p", modelo="claude-sonnet-5")
    traza.llamadas = [
        LlamadaModelo(turno=1, input_tokens=100, output_tokens=10),
        LlamadaModelo(turno=2, input_tokens=100, output_tokens=20, cache_read_input_tokens=800),
    ]
    assert traza.turnos == 2
    assert traza.tokens_entrada == 1000
    assert traza.tokens_salida == 30
    assert traza.ratio_cache == pytest.approx(0.8)


def test_ratio_cache_sin_llamadas_no_divide_por_cero():
    assert Traza(pregunta="p", modelo="claude-sonnet-5").ratio_cache == 0.0


def test_tools_usadas_conserva_el_orden_y_deduplica():
    traza = Traza(pregunta="p", modelo="claude-sonnet-5")
    traza.tools = [
        UsoTool(turno=1, nombre="buscar_licitaciones", entrada={}),
        UsoTool(turno=2, nombre="consultar_datos", entrada={}),
        UsoTool(turno=3, nombre="buscar_licitaciones", entrada={}),
    ]
    assert traza.tools_usadas == ["buscar_licitaciones", "consultar_datos"]


def test_emitir_escribe_jsonl_y_no_llama_a_langfuse_sin_claves(tmp_path, monkeypatch):
    ruta = tmp_path / "trazas.jsonl"
    monkeypatch.setattr("api.observabilidad.RUTA_TRAZAS", ruta)
    monkeypatch.setattr("api.observabilidad.langfuse_configurado", lambda: False)

    traza = Traza(pregunta="¿cuántas?", modelo="claude-sonnet-5", respuesta="42")
    traza.llamadas = [LlamadaModelo(turno=1, input_tokens=10, output_tokens=5)]
    emitir(traza)

    registro = json.loads(ruta.read_text(encoding="utf-8").strip())
    assert registro["pregunta"] == "¿cuántas?"
    assert registro["turnos"] == 1
    assert registro["coste_usd"] > 0


def test_emitir_no_propaga_un_fallo_de_langfuse(tmp_path, monkeypatch):
    # La telemetría es best-effort: si Langfuse está caído, la respuesta ya se
    # le dio al usuario y no se puede perder por eso.
    monkeypatch.setattr("api.observabilidad.RUTA_TRAZAS", tmp_path / "trazas.jsonl")
    monkeypatch.setattr("api.observabilidad.langfuse_configurado", lambda: True)

    def _explota(_traza):
        raise ConnectionError("langfuse caído")

    monkeypatch.setattr("api.observabilidad._emitir_langfuse", _explota)
    emitir(Traza(pregunta="p", modelo="claude-sonnet-5"))  # no debe lanzar
