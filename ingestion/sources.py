"""Catálogo de fuentes de datos abiertos de contratación pública.

URLs oficiales verificadas (2026-07). PLACSP publica ZIP anuales que contienen
feeds ATOM paginados (máx. 500 entradas por fichero .atom) en formato CODICE 2.07.

Patrón:
    https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_{ID}/{fichero}_{AÑO}.zip
"""

from __future__ import annotations

from dataclasses import dataclass

PLACSP_BASE = "https://contrataciondelsectorpublico.gob.es/sindicacion"


@dataclass(frozen=True)
class PlacspDataset:
    """Un conjunto de datos abiertos de PLACSP."""

    key: str
    sindicacion_id: int
    file_prefix: str
    first_year: int
    description: str

    def zip_url(self, year: int) -> str:
        return f"{PLACSP_BASE}/sindicacion_{self.sindicacion_id}/{self.file_prefix}_{year}.zip"


# Los cinco conjuntos nacionales de PLACSP.
PLACSP_DATASETS: dict[str, PlacspDataset] = {
    "licitaciones": PlacspDataset(
        key="licitaciones",
        sindicacion_id=643,
        file_prefix="licitacionesPerfilesContratanteCompleto3",
        first_year=2012,
        description="Licitaciones publicadas en perfiles del contratante (excluye contratos menores).",
    ),
    "contratos_menores": PlacspDataset(
        key="contratos_menores",
        sindicacion_id=1143,
        file_prefix="contratosMenoresPerfilesContratantes",
        first_year=2018,
        description="Contratos menores publicados en perfiles del contratante.",
    ),
    "agregadas": PlacspDataset(
        key="agregadas",
        sindicacion_id=1044,
        file_prefix="PlataformasAgregadasSinMenores",
        first_year=2016,
        description="Licitaciones publicadas vía mecanismos de agregación (excluye menores).",
    ),
    "encargos_medios_propios": PlacspDataset(
        key="encargos_medios_propios",
        sindicacion_id=1383,
        file_prefix="EMP_SectorPublico",
        first_year=2022,
        description="Encargos a medios propios.",
    ),
    "consultas_mercado": PlacspDataset(
        key="consultas_mercado",
        sindicacion_id=1403,
        file_prefix="CPM_SectorPublico",
        first_year=2022,
        description="Consultas preliminares de mercado.",
    ),
}


# TED (UE) — paquetes bulk sin autenticación (XML eForms).
TED_MONTHLY = "https://ted.europa.eu/packages/monthly/{year}-{month}"  # p.ej. 2025-6
TED_DAILY = "https://ted.europa.eu/packages/daily/{yyyynnnnn}"        # p.ej. 202500123
