-- Tabla de hechos de licitaciones: una fila por expediente, lista para análisis
-- y para el agente. Añade etiquetas legibles (desde los seeds de codelists),
-- la división CPV y señales simples para el módulo de riesgo.

with lic as (
    select * from {{ ref('stg_placsp__licitaciones') }}
)

select
    lic.entry_id,
    lic.expediente,
    lic.title,
    lic.link,
    lic.objeto,

    -- estado
    lic.estado,
    est.estado_desc,
    lic.estado in ('ADJ', 'RES')            as esta_adjudicada,

    -- clasificación
    lic.tipo_contrato,
    tip.tipo_contrato_desc,
    lic.subtipo_contrato,
    lic.cpv,
    left(lic.cpv, 2)                        as cpv_division,

    -- proceso
    lic.procedimiento,
    proc.procedimiento_desc,
    lic.sistema_contratacion,
    lic.urgencia,
    lic.plazo_presentacion,
    lic.n_lotes,

    -- importes
    lic.valor_estimado,
    lic.presupuesto_sin_impuestos,
    lic.presupuesto_con_impuestos,

    -- órgano y lugar
    lic.organo_nif,
    lic.organo_contratacion,
    lic.organo_dir3,
    lic.lugar_provincia,
    lic.lugar_nuts,
    lic.lugar_municipio,

    -- metadatos
    lic.anio,
    lic.actualizado_en,

    -- señal simple para el módulo de riesgo (se refina en analytics/):
    -- presupuesto justo bajo el umbral del contrato menor (15.000 € en servicios).
    (lic.presupuesto_sin_impuestos between 14000 and 15000) as cerca_umbral_menor

from lic
left join {{ ref('ref_estado_licitacion') }} est on lic.estado = est.codigo
left join {{ ref('ref_tipo_contrato') }}      tip on lic.tipo_contrato = tip.codigo
left join {{ ref('ref_procedimiento') }}      proc on lic.procedimiento = proc.codigo
