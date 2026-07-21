"""Tests de la fusión RRF (función pura, sin Postgres ni modelo de embeddings)."""

from __future__ import annotations

import math

from search.fusion import fusionar, rrf


def test_documento_en_ambas_listas_supera_a_los_exclusivos():
    # 'b' aparece en las dos listas; debe quedar por delante de cualquiera que
    # solo aparezca en una, aunque no sea el primero de ninguna.
    lexica = ["a", "b", "c"]
    vectorial = ["d", "b", "e"]
    orden = [doc for doc, _ in fusionar([lexica, vectorial])]
    assert orden[0] == "b"


def test_score_es_suma_de_reciprocos():
    # 'x' primero en una lista (rango 1) y tercero en otra (rango 3).
    scores = rrf([["x"], ["y", "z", "x"]], k=60)
    assert scores["x"] == 1 / 61 + 1 / 63
    assert scores["y"] == 1 / 61
    assert math.isclose(scores["z"], 1 / 62)


def test_k_alto_aplana_la_ventaja_de_las_primeras_posiciones():
    # Con k grande, la diferencia entre rango 1 y rango 2 se atenúa.
    ventaja_k_bajo = rrf([["a", "b"]], k=1)["a"] - rrf([["a", "b"]], k=1)["b"]
    ventaja_k_alto = rrf([["a", "b"]], k=1000)["a"] - rrf([["a", "b"]], k=1000)["b"]
    assert ventaja_k_alto < ventaja_k_bajo


def test_empate_desempata_por_id_de_forma_determinista():
    # Dos documentos con idéntica contribución: orden estable y alfabético.
    orden = [doc for doc, _ in fusionar([["m"], ["n"]])]
    assert orden == ["m", "n"]


def test_limite_recorta_al_top_k():
    fusion = fusionar([["a", "b", "c", "d"]], limite=2)
    assert len(fusion) == 2
    assert [doc for doc, _ in fusion] == ["a", "b"]


def test_rankings_vacios_no_rompen():
    assert rrf([]) == {}
    assert fusionar([[], []]) == []
