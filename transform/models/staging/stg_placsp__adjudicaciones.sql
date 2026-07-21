-- Adjudicaciones / resultados de licitación (TenderResult).
-- Grano: un resultado por lote (o por expediente si no hay lotes). Enlaza con
-- stg_placsp__licitaciones por `_lic_dlt_id`.

with source as (
    select * from {{ source('raw', 'licitaciones__adjudicaciones') }}
)

select
    _dlt_id                                        as adjudicacion_id,
    _dlt_parent_id                                 as _lic_dlt_id,

    result_code,
    nullif(trim(resultado), '')                    as resultado,
    try_cast(fecha_adjudicacion as date)           as fecha_adjudicacion,

    n_ofertas,
    n_ofertas_pyme,
    case lower(pyme_adjudicada)
        when 'true' then true
        when 'false' then false
    end                                            as pyme_adjudicada,

    lote_id,
    cast(importe_sin_impuestos as decimal(18, 2))  as importe_sin_impuestos,
    cast(importe_con_impuestos as decimal(18, 2))  as importe_con_impuestos,

    nullif(trim(adjudicatario), '')                as adjudicatario,
    adjudicatario_nif,
    n_adjudicatarios
from source
