"""Parser de entradas ATOM/CODICE 2.07 de PLACSP.

Cada fichero `.atom` es un feed con múltiples `<entry>`; cada entry envuelve un
bloque `<cac-place-ext:ContractFolderStatus>` con toda la información CODICE de un
expediente de contratación. Extraemos aquí un **registro anidado** por expediente:

    {cabecera...,
     "lotes": [ {...}, ... ],            # ProcurementProjectLot
     "adjudicaciones": [ {...}, ... ]}   # TenderResult

dlt normaliza `lotes` y `adjudicaciones` en tablas hijas (`..._lotes`,
`..._adjudicaciones`) con clave foránea al padre — de ahí sale el modelo
relacional. La limpieza fina y el tipado canónico se hacen luego en dbt.

Rutas validadas contra ficheros reales de `licitacionesPerfilesContratanteCompleto3`
(sindicación 643, 2025). Dos trampas de namespace comprobadas:
  * `ContractFolderStatusCode` vive en `cbc-place-ext`, NO en `cbc`.
  * Presupuesto y CPV se repiten dentro de cada lote; anclamos las rutas de
    cabecera al `ContractFolderStatus` directo para no coger las de los lotes.
"""

from __future__ import annotations

from typing import Any

from lxml import etree

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "at": "http://purl.org/atompub/tombstones/1.0",
    "cbc": "urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2",
    "cbc-place-ext": ("urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2"),
    "cac-place-ext": (
        "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2"
    ),
}


def _text(node: etree._Element | None, path: str) -> str | None:
    if node is None:
        return None
    found = node.find(path, namespaces=NS)
    return found.text.strip() if found is not None and found.text else None


def _float(node: etree._Element | None, path: str) -> float | None:
    raw = _text(node, path)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _int(node: etree._Element | None, path: str) -> int | None:
    raw = _text(node, path)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _party_id(party: etree._Element | None, scheme: str) -> str | None:
    """Devuelve el `cbc:ID` de una Party cuyo schemeName coincide (NIF, DIR3...)."""
    if party is None:
        return None
    node = party.find(f"cac:PartyIdentification/cbc:ID[@schemeName='{scheme}']", namespaces=NS)
    return node.text.strip() if node is not None and node.text else None


def _parse_lote(lot: etree._Element) -> dict[str, Any]:
    """Un `ProcurementProjectLot` → dict. El proyecto del lote cuelga dentro."""
    proj = "cac:ProcurementProject"
    return {
        "lote_id": _text(lot, "cbc:ID"),
        "objeto": _text(lot, f"{proj}/cbc:Name"),
        "cpv": _text(
            lot,
            f"{proj}/cac:RequiredCommodityClassification/cbc:ItemClassificationCode",
        ),
        "presupuesto_sin_impuestos": _float(lot, f"{proj}/cac:BudgetAmount/cbc:TaxExclusiveAmount"),
        "presupuesto_con_impuestos": _float(lot, f"{proj}/cac:BudgetAmount/cbc:TotalAmount"),
    }


def _parse_adjudicacion(tr: etree._Element) -> dict[str, Any]:
    """Un `TenderResult` → dict. Toma el primer adjudicatario (las UTE traen
    varios `WinningParty`); guardamos también cuántos hay."""
    winners = tr.findall("cac:WinningParty", namespaces=NS)
    first = winners[0] if winners else None
    awarded = "cac:AwardedTenderedProject"
    return {
        "result_code": _text(tr, "cbc:ResultCode"),
        "resultado": _text(tr, "cbc:Description"),
        "fecha_adjudicacion": _text(tr, "cbc:AwardDate"),
        "n_ofertas": _int(tr, "cbc:ReceivedTenderQuantity"),
        "n_ofertas_pyme": _int(tr, "cbc:SMEsReceivedTenderQuantity"),
        "pyme_adjudicada": _text(tr, "cbc:SMEAwardedIndicator"),
        "lote_id": _text(tr, f"{awarded}/cbc:ProcurementProjectLotID"),
        "importe_sin_impuestos": _float(
            tr, f"{awarded}/cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount"
        ),
        "importe_con_impuestos": _float(tr, f"{awarded}/cac:LegalMonetaryTotal/cbc:PayableAmount"),
        "adjudicatario": _text(first, "cac:PartyName/cbc:Name"),
        "adjudicatario_nif": _party_id(first, "NIF"),
        "n_adjudicatarios": len(winners),
    }


def parse_entry(entry: etree._Element) -> dict[str, Any] | None:
    """Extrae un registro anidado de una `<entry>` de PLACSP.

    Devuelve None si la entry no trae `ContractFolderStatus` (feeds excepcionales).
    """
    cfs = entry.find("cac-place-ext:ContractFolderStatus", namespaces=NS)
    if cfs is None:
        return None

    # Órgano de contratación (Party dentro de LocatedContractingParty).
    party = cfs.find("cac-place-ext:LocatedContractingParty/cac:Party", namespaces=NS)
    # Proyecto principal (directo del CFS; NO los de los lotes).
    proj = cfs.find("cac:ProcurementProject", namespaces=NS)
    loc = "cac:RealizedLocation"
    proc = "cac:TenderingProcess"

    record: dict[str, Any] = {
        # --- Atom / identidad ---
        "entry_id": _text(entry, "atom:id"),
        "title": _text(entry, "atom:title"),
        "updated": _text(entry, "atom:updated"),
        "link": (
            entry.find("atom:link", namespaces=NS).get("href")
            if entry.find("atom:link", namespaces=NS) is not None
            else None
        ),
        # --- Expediente ---
        "expediente": _text(cfs, "cbc:ContractFolderID"),
        "estado": _text(cfs, "cbc-place-ext:ContractFolderStatusCode"),
        # --- Objeto y clasificación ---
        "objeto": _text(proj, "cbc:Name"),
        "tipo_contrato": _text(proj, "cbc:TypeCode"),
        "subtipo_contrato": _text(proj, "cbc:SubTypeCode"),
        "cpv": _text(
            proj,
            "cac:RequiredCommodityClassification/cbc:ItemClassificationCode",
        ),
        # --- Importes de licitación ---
        "valor_estimado": _float(proj, "cac:BudgetAmount/cbc:EstimatedOverallContractAmount"),
        "presupuesto_sin_impuestos": _float(proj, "cac:BudgetAmount/cbc:TaxExclusiveAmount"),
        "presupuesto_con_impuestos": _float(proj, "cac:BudgetAmount/cbc:TotalAmount"),
        # --- Órgano de contratación ---
        "organo_contratacion": _text(party, "cac:PartyName/cbc:Name"),
        "organo_nif": _party_id(party, "NIF"),
        "organo_dir3": _party_id(party, "DIR3"),
        # --- Lugar de ejecución (NUTS) ---
        "lugar_provincia": _text(proj, f"{loc}/cbc:CountrySubentity"),
        "lugar_nuts": _text(proj, f"{loc}/cbc:CountrySubentityCode"),
        "lugar_municipio": _text(proj, f"{loc}/cac:Address/cbc:CityName"),
        # --- Proceso ---
        "procedimiento": _text(cfs, f"{proc}/cbc:ProcedureCode"),
        "sistema_contratacion": _text(cfs, f"{proc}/cbc:ContractingSystemCode"),
        "urgencia": _text(cfs, f"{proc}/cbc:UrgencyCode"),
        "plazo_presentacion": _text(cfs, f"{proc}/cac:TenderSubmissionDeadlinePeriod/cbc:EndDate"),
        # --- Hijos (dlt los normaliza en tablas relacionadas) ---
        "lotes": [
            _parse_lote(lot) for lot in cfs.findall("cac:ProcurementProjectLot", namespaces=NS)
        ],
        "adjudicaciones": [
            _parse_adjudicacion(tr) for tr in cfs.findall("cac:TenderResult", namespaces=NS)
        ],
    }
    record["n_lotes"] = len(record["lotes"])
    return record


def parse_atom_bytes(content: bytes) -> list[dict[str, Any]]:
    """Parsea un fichero `.atom` completo y devuelve la lista de registros.

    Ignora `<at:deleted-entry>` (expedientes anulados; tombstones ATOM) y las
    entries sin `ContractFolderStatus`.
    """
    root = etree.fromstring(content)
    records = []
    for e in root.findall("atom:entry", namespaces=NS):
        rec = parse_entry(e)
        if rec is not None:
            records.append(rec)
    return records
