-- Dimensión de órganos de contratación. Grano: un órgano por NIF.
-- Combina el volumen de expedientes convocados con lo efectivamente adjudicado.

with lic as (
    select * from {{ ref('stg_placsp__licitaciones') }}
),

adj as (
    select * from {{ ref('int_adjudicaciones_enriquecidas') }}
),

expedientes as (
    select
        organo_nif,
        mode(organo_contratacion)               as organo_contratacion,
        mode(organo_dir3)                        as organo_dir3,
        mode(lugar_provincia)                    as lugar_provincia,
        count(distinct entry_id)                 as n_expedientes,
        sum(presupuesto_sin_impuestos)           as presupuesto_total_licitado
    from lic
    group by organo_nif
),

adjudicado as (
    select
        organo_nif,
        count(*)                                 as n_adjudicaciones,
        count(distinct adjudicatario_nif)        as n_adjudicatarios_distintos,
        sum(importe_sin_impuestos)               as importe_total_adjudicado,
        avg(baja_pct)                            as baja_media,
        count(*) filter (where oferta_unica)     as n_adjudicaciones_oferta_unica
    from adj
    group by organo_nif
)

select
    e.organo_nif,
    e.organo_contratacion,
    e.organo_dir3,
    e.lugar_provincia,
    e.n_expedientes,
    e.presupuesto_total_licitado,
    coalesce(a.n_adjudicaciones, 0)                  as n_adjudicaciones,
    coalesce(a.n_adjudicatarios_distintos, 0)        as n_adjudicatarios_distintos,
    a.importe_total_adjudicado,
    a.baja_media,
    coalesce(a.n_adjudicaciones_oferta_unica, 0)     as n_adjudicaciones_oferta_unica
from expedientes e
left join adjudicado a on e.organo_nif = a.organo_nif
