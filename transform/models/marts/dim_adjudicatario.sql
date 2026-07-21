-- Dimensión de adjudicatarios (empresas). Grano: un adjudicatario por NIF.
-- Solo se incluyen adjudicaciones con NIF identificado (~13 % vienen sin NIF y
-- no son atribuibles de forma fiable a una empresa concreta).

with adj as (
    select *
    from {{ ref('int_adjudicaciones_enriquecidas') }}
    where adjudicatario_nif is not null
)

select
    adjudicatario_nif,
    mode(adjudicatario)                        as adjudicatario,
    count(*)                                   as n_adjudicaciones,
    count(distinct organo_nif)                 as n_organos_distintos,
    sum(importe_sin_impuestos)                 as importe_total_adjudicado,
    avg(importe_sin_impuestos)                 as importe_medio_adjudicado,
    avg(baja_pct)                              as baja_media,
    bool_or(pyme_adjudicada)                   as es_pyme,
    count(*) filter (where oferta_unica)       as n_adjudicaciones_oferta_unica
from adj
group by adjudicatario_nif
