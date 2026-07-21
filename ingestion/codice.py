"""Parser pragmático de entradas ATOM/CODICE 2.07 de PLACSP.

Cada fichero .atom contiene <entry> con un bloque CODICE embebido. Extraemos
aquí los campos clave a un dict plano; el modelado fino se hace luego en dbt.

Nota: los espacios de nombres y rutas CODICE son estables pero verbosos. Este
extractor cubre los campos de alto valor; amplíalo contra ficheros reales
(descarga un ZIP con `make ingest` y explora un .atom).
"""

from __future__ import annotations

from typing import Any

from lxml import etree

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "cbc": "urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2",
    "cac-place-ext": (
        "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2"
    ),
}


def _text(node: etree._Element, path: str) -> str | None:
    found = node.find(path, namespaces=NS)
    return found.text.strip() if found is not None and found.text else None


def parse_entry(entry: etree._Element) -> dict[str, Any]:
    """Extrae los campos de alto valor de una <entry> ATOM de PLACSP."""
    return {
        "entry_id": _text(entry, "atom:id"),
        "title": _text(entry, "atom:title"),
        "updated": _text(entry, "atom:updated"),
        # Identificador del expediente
        "expediente": _text(
            entry, ".//cac-place-ext:ContractFolderStatus/cbc:ContractFolderID"
        ),
        "estado": _text(
            entry,
            ".//cac-place-ext:ContractFolderStatus/cbc:ContractFolderStatusCode",
        ),
        # Objeto y tipo del contrato
        "objeto": _text(entry, ".//cac:ProcurementProject/cbc:Name"),
        "tipo_contrato": _text(
            entry, ".//cac:ProcurementProject/cbc:TypeCode"
        ),
        "cpv": _text(
            entry,
            ".//cac:ProcurementProject/cac:RequiredCommodityClassification/cbc:ItemClassificationCode",
        ),
        # Importes
        "valor_estimado": _text(
            entry,
            ".//cac:ProcurementProject/cac:BudgetAmount/cbc:EstimatedOverallContractAmount",
        ),
        "presupuesto_sin_impuestos": _text(
            entry,
            ".//cac:ProcurementProject/cac:BudgetAmount/cbc:TaxExclusiveAmount",
        ),
        # Órgano de contratación
        "organo_contratacion": _text(
            entry,
            ".//cac-place-ext:LocatedContractingParty/cac:Party/cac:PartyName/cbc:Name",
        ),
    }


def parse_atom_bytes(content: bytes) -> list[dict[str, Any]]:
    """Parsea el contenido de un fichero .atom y devuelve una lista de dicts."""
    root = etree.fromstring(content)
    entries = root.findall("atom:entry", namespaces=NS)
    return [parse_entry(e) for e in entries]
