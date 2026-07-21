"""Tests de regresión del parser CODICE contra un fixture .atom real recortado.

El fixture (`fixtures/sample_placsp.atom`) contiene dos `<entry>` reales de PLACSP
—una adjudicada con lotes y otra en publicación— más un `<at:deleted-entry>`
(tombstone), extraídos de un feed de licitaciones 2025.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.codice import parse_atom_bytes

FIXTURE = Path(__file__).parent / "fixtures" / "sample_placsp.atom"


@pytest.fixture(scope="module")
def records() -> list[dict]:
    return parse_atom_bytes(FIXTURE.read_bytes())


def test_skips_tombstones_and_returns_two_entries(records):
    # El <at:deleted-entry> no es <entry>: no debe parsearse.
    assert len(records) == 2


def test_estado_extraido(records):
    # Regresión: 'estado' vive en cbc-place-ext, no en cbc (era 0% antes).
    assert all(r["estado"] for r in records)
    assert {r["estado"] for r in records} <= {
        "PUB",
        "EV",
        "ADJ",
        "RES",
        "PRE",
        "ANUL",
        "RESU",
        "DEF",
    }


def test_campos_cabecera_obligatorios(records):
    for r in records:
        assert r["entry_id"] and r["entry_id"].startswith("http")
        assert r["expediente"]
        assert r["objeto"]
        assert r["organo_contratacion"]
        assert r["organo_nif"]  # NIF del órgano siempre presente en la muestra


def test_importes_son_float(records):
    for r in records:
        for campo in (
            "valor_estimado",
            "presupuesto_sin_impuestos",
            "presupuesto_con_impuestos",
        ):
            assert r[campo] is None or isinstance(r[campo], float)


def test_entry_con_lotes_y_adjudicaciones():
    records = parse_atom_bytes(FIXTURE.read_bytes())
    adjudicada = next(r for r in records if r["estado"] in ("ADJ", "RES"))

    assert adjudicada["n_lotes"] == len(adjudicada["lotes"]) > 0
    lote = adjudicada["lotes"][0]
    assert lote["lote_id"]
    assert lote["objeto"]

    assert len(adjudicada["adjudicaciones"]) > 0
    adj = adjudicada["adjudicaciones"][0]
    assert adj["adjudicatario"]
    assert adj["adjudicatario_nif"]
    assert adj["importe_sin_impuestos"] is None or isinstance(adj["importe_sin_impuestos"], float)
    assert adj["n_ofertas"] is None or isinstance(adj["n_ofertas"], int)


def test_entry_sin_adjudicar_no_tiene_adjudicaciones():
    records = parse_atom_bytes(FIXTURE.read_bytes())
    sin_adj = [r for r in records if r["estado"] in ("PUB", "EV")]
    assert sin_adj, "el fixture debe incluir una licitación no adjudicada"
    assert all(r["adjudicaciones"] == [] for r in sin_adj)
