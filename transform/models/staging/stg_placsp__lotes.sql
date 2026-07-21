-- Lotes de cada expediente (ProcurementProjectLot).
-- Enlazan con stg_placsp__licitaciones por `_lic_dlt_id`. Los lotes de versiones
-- antiguas del expediente se descartan aguas abajo al hacer inner join con las
-- licitaciones deduplicadas.

with source as (
    select * from {{ source('raw', 'licitaciones__lotes') }}
)

select
    _dlt_parent_id                                    as _lic_dlt_id,
    lote_id,
    nullif(trim(objeto), '')                          as objeto_lote,
    cpv                                               as cpv_lote,
    cast(presupuesto_sin_impuestos as decimal(18, 2)) as presupuesto_sin_impuestos,
    cast(presupuesto_con_impuestos as decimal(18, 2)) as presupuesto_con_impuestos
from source
