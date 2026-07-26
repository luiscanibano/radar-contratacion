"""Tests del arnés de evaluación: métricas de recuperación, comprobación de
herramientas y agregación. Nada aquí llama a la API ni a Postgres."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from api.observabilidad import Traza, UsoTool
from evals.retrieval import mrr, ndcg_en_k, precision_en_k, recall_en_k
from evals.run import GOLDEN, Resultado, agregar, comprobar_tools

# --- golden set -------------------------------------------------------------


def _casos() -> list[dict]:
    return [json.loads(linea) for linea in GOLDEN.read_text(encoding="utf-8").splitlines() if linea]


def test_golden_set_bien_formado():
    casos = _casos()
    assert casos, "el golden set no puede estar vacío"
    ids = [c["id"] for c in casos]
    assert len(ids) == len(set(ids)), "hay ids duplicados en el golden set"
    for caso in casos:
        assert caso["pregunta"] and caso["criterio"]
        assert caso["categoria"]
        # Un caso que espera y prohíbe la misma tool es imposible de superar.
        solapan = set(caso.get("tools_esperadas", [])) & set(caso.get("tools_prohibidas", []))
        assert not solapan, f"{caso['id']}: {solapan} está esperada y prohibida a la vez"


# --- comprobación determinista de herramientas ------------------------------


def _traza_con(*nombres: str) -> Traza:
    traza = Traza(pregunta="p", modelo="claude-sonnet-5")
    traza.tools = [UsoTool(turno=1, nombre=n, entrada={}) for n in nombres]
    return traza


def test_tool_esperada_ausente_es_fallo():
    caso = {"tools_esperadas": ["consultar_datos"]}
    assert comprobar_tools(caso, _traza_con("buscar_licitaciones"))
    assert not comprobar_tools(caso, _traza_con("consultar_datos"))


def test_tool_prohibida_usada_es_fallo():
    # El caso clave de la semana 5: ante una pregunta ambigua el agente debe
    # pedir aclaración, no lanzarse a consultar.
    caso = {"tools_prohibidas": ["consultar_datos", "buscar_licitaciones"]}
    assert comprobar_tools(caso, _traza_con("consultar_datos"))
    assert not comprobar_tools(caso, _traza_con())


def test_caso_sin_restricciones_nunca_falla_por_tools():
    assert not comprobar_tools({}, _traza_con("consultar_datos", "buscar_licitaciones"))


# --- agregación -------------------------------------------------------------


def _resultado(id_: str, categoria="c", fallos=None, veredicto="PASA") -> Resultado:
    return Resultado(
        id=id_,
        categoria=categoria,
        pregunta="p",
        respuesta="r",
        tools_usadas=[],
        fallos_tools=fallos or [],
        veredicto_juez=veredicto,
        coste_usd=0.01,
        latencia_s=1.0,
    )


def test_un_fallo_de_tools_hace_fallar_el_caso_aunque_el_juez_apruebe():
    # Sin esto, el agente podría aprobar contestando bien "de memoria", sin
    # consultar los datos — justo lo que el proyecto no debe hacer.
    assert not _resultado("x", fallos=["no usó consultar_datos"]).pasa


def test_sin_juez_el_caso_pasa_con_las_deterministas_limpias():
    assert _resultado("x", veredicto=None).pasa


def test_errores_del_juez_no_cuentan_como_fallos_del_agente():
    resultados = [
        _resultado("a"),
        _resultado("b", veredicto="FALLA"),
        _resultado("c", veredicto="ERROR_JUEZ"),
    ]
    resumen = agregar(resultados)
    assert resumen["casos"] == 3
    assert resumen["evaluables"] == 2
    assert resumen["pasan"] == 1
    assert resumen["tasa_aprobados"] == pytest.approx(0.5)
    assert resumen["errores_juez"] == 1


def test_agregar_sin_resultados_no_revienta():
    resumen = agregar([])
    assert resumen["tasa_aprobados"] == 0.0
    assert resumen["latencia_media_s"] == 0.0


# --- métricas de recuperación ------------------------------------------------

RECUPERADOS = ["a", "b", "c", "d"]
RELEVANTES = {"c", "e"}


def test_recall_y_precision_en_k():
    assert recall_en_k(RECUPERADOS, RELEVANTES, 4) == pytest.approx(0.5)  # 1 de 2
    assert recall_en_k(RECUPERADOS, RELEVANTES, 2) == 0.0  # "c" está en 3ª posición
    assert precision_en_k(RECUPERADOS, RELEVANTES, 4) == pytest.approx(0.25)


def test_mrr_usa_la_primera_posicion_relevante():
    assert mrr(RECUPERADOS, RELEVANTES) == pytest.approx(1 / 3)
    assert mrr(["x", "y"], RELEVANTES) == 0.0


def test_ndcg_premia_los_aciertos_arriba():
    arriba = ndcg_en_k(["c", "e", "a"], RELEVANTES, 3)
    abajo = ndcg_en_k(["a", "c", "e"], RELEVANTES, 3)
    assert arriba == pytest.approx(1.0)
    assert abajo < arriba


def test_metricas_sin_relevantes_devuelven_cero_y_no_dividen_por_cero():
    assert recall_en_k(RECUPERADOS, set(), 4) == 0.0
    assert ndcg_en_k(RECUPERADOS, set(), 4) == 0.0
    assert precision_en_k(RECUPERADOS, RELEVANTES, 0) == 0.0


def test_conjunto_de_recuperacion_bien_formado():
    ruta = Path(__file__).parent / "retrieval_set.jsonl"
    casos = [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines() if linea]
    assert casos
    for caso in casos:
        assert caso["consulta"]
        assert isinstance(caso["relevantes"], list)
