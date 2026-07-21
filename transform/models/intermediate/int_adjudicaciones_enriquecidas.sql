-- Cada adjudicación enriquecida con el contexto de su expediente y su lote.
--
-- Es la base de fct_adjudicaciones y de las dimensiones. Calcula la "baja"
-- (rebaja sobre el presupuesto): usa el presupuesto del LOTE cuando la
-- adjudicación es de un lote concreto, y si no el del expediente.

with adj as (
    select * from {{ ref('stg_placsp__adjudicaciones') }}
),

lic as (
    select * from {{ ref('stg_placsp__licitaciones') }}
),

lotes as (
    select * from {{ ref('stg_placsp__lotes') }}
),

joined as (
    select
        adj.adjudicacion_id,
        lic.entry_id,
        lic.expediente,

        -- contexto del órgano
        lic.organo_nif,
        lic.organo_contratacion,
        lic.organo_dir3,
        lic.lugar_provincia,

        -- contexto del objeto/proceso
        lic.cpv,
        left(lic.cpv, 2)                                   as cpv_division,
        lic.tipo_contrato,
        lic.procedimiento,
        lic.estado,
        lic.anio,

        -- resultado
        adj.lote_id,
        adj.fecha_adjudicacion,
        adj.importe_sin_impuestos,
        adj.importe_con_impuestos,
        adj.adjudicatario,
        adj.adjudicatario_nif,
        adj.n_adjudicatarios,
        adj.pyme_adjudicada,

        -- competencia
        adj.n_ofertas,
        adj.n_ofertas_pyme,

        -- presupuesto de referencia: el del lote si existe, si no el del expediente
        coalesce(
            lote.presupuesto_sin_impuestos,
            lic.presupuesto_sin_impuestos
        )                                                  as presupuesto_referencia

    from adj
    inner join lic
        on adj._lic_dlt_id = lic._lic_dlt_id
    left join lotes lote
        on adj._lic_dlt_id = lote._lic_dlt_id
        and adj.lote_id = lote.lote_id
),

final as (
    select
        *,
        -- baja (%): 1 - importe/presupuesto. Solo cuando ambos son positivos y el
        -- presupuesto es de referencia; en otro caso null (no se puede calcular).
        case
            when presupuesto_referencia > 0 and importe_sin_impuestos > 0
            then round(1 - importe_sin_impuestos / presupuesto_referencia, 4)
        end                                                as baja_pct,

        -- ratio de PYMEs entre las ofertas recibidas
        case
            when n_ofertas > 0
            then round(n_ofertas_pyme * 1.0 / n_ofertas, 4)
        end                                                as ratio_ofertas_pyme,

        -- señal de riesgo: única oferta recibida
        (n_ofertas = 1)                                    as oferta_unica
    from joined
)

select * from final
