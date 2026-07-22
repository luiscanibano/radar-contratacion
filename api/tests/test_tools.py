"""Tests de las herramientas del agente: guardrails de SQL y wrapper de búsqueda."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

from api.agent.tools import buscar_licitaciones, run_readonly_sql


def test_select_simple_funciona():
    resultado = run_readonly_sql("select 1 as uno")
    assert resultado == {"columns": ["uno"], "rows": [{"uno": 1}], "row_count": 1}


def test_with_cte_esta_permitido():
    resultado = run_readonly_sql("with t as (select 1 as uno) select * from t")
    assert resultado["row_count"] == 1


def test_bloquea_insert():
    resultado = run_readonly_sql("insert into fct_licitaciones values (1)")
    assert "error" in resultado


def test_bloquea_drop():
    resultado = run_readonly_sql("drop table fct_licitaciones")
    assert "error" in resultado


def test_bloquea_palabra_prohibida_dentro_de_un_select():
    # La keyword prohibida puede aparecer en cualquier parte de la sentencia,
    # no solo al principio (p. ej. un CTE o subconsulta con DDL/DML incrustado).
    resultado = run_readonly_sql("select 1; drop table fct_licitaciones")
    assert "error" in resultado


def test_exige_que_empiece_por_select_o_with():
    resultado = run_readonly_sql("explain select 1")
    assert "error" in resultado


def test_sql_invalido_devuelve_error_sin_reventar():
    resultado = run_readonly_sql("select * from tabla_que_no_existe")
    assert "error" in resultado


def test_buscar_licitaciones_sin_extra_search_da_error_claro():
    with patch.dict("sys.modules", {"search.hibrida": None}):
        resultado = buscar_licitaciones("asfaltado de carreteras")
    assert "error" in resultado
    assert "search" in resultado["error"]


def test_buscar_licitaciones_propaga_resultados_serializados():
    @dataclass
    class FakeResultado:
        entry_id: str

    fake_resultados = [FakeResultado("a"), FakeResultado("b")]

    with patch("search.hibrida.buscar", return_value=fake_resultados, create=True):
        resultado = buscar_licitaciones("asfaltado de carreteras", k=2)

    assert resultado["row_count"] == 2
    assert resultado["resultados"][0]["entry_id"] == "a"


def test_buscar_licitaciones_captura_excepciones_del_backend():
    def _raise(*_args, **_kwargs):
        raise RuntimeError("Postgres no disponible")

    with patch("search.hibrida.buscar", side_effect=_raise, create=True):
        resultado = buscar_licitaciones("asfaltado de carreteras")

    assert resultado == {"error": "Postgres no disponible"}
