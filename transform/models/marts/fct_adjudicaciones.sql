-- Tabla de hechos de adjudicaciones: una fila por resultado de licitación,
-- con el contexto del expediente, la baja y las señales de competencia.
-- Es el grano fino para análisis de gasto, concentración y riesgo.

with adj as (
    select * from {{ ref('int_adjudicaciones_enriquecidas') }}
)

select
    adjudicacion_id,
    entry_id,
    expediente,

    -- órgano
    organo_nif,
    organo_contratacion,
    organo_dir3,
    lugar_provincia,

    -- objeto / proceso
    cpv,
    cpv_division,
    tipo_contrato,
    procedimiento,
    estado,
    anio,

    -- resultado
    lote_id,
    fecha_adjudicacion,
    adjudicatario,
    adjudicatario_nif,
    n_adjudicatarios,
    pyme_adjudicada,

    -- importes y baja
    presupuesto_referencia,
    importe_sin_impuestos,
    importe_con_impuestos,
    baja_pct,

    -- competencia
    n_ofertas,
    n_ofertas_pyme,
    ratio_ofertas_pyme,
    oferta_unica

from adj
