-- Licitaciones de PLACSP: una fila por expediente (entry_id).
--
-- PLACSP re-publica cada expediente al avanzar de estado (PUB -> EV -> ADJ -> RES),
-- así que en `raw` hay varias versiones del mismo `entry_id` (hasta 7). Aquí nos
-- quedamos con la MÁS RECIENTE (`updated` desc) = snapshot del estado actual.
-- Conservamos `_lic_dlt_id` para poder enlazar las tablas hijas (lotes,
-- adjudicaciones) de esa misma versión.

with source as (
    select * from {{ source('raw', 'licitaciones') }}
),

deduplicado as (
    select *
    from source
    qualify row_number() over (partition by entry_id order by updated desc) = 1
),

cleaned as (
    select
        -- identidad
        entry_id,
        expediente,
        nullif(trim(title), '')                                as title,
        link,
        _dlt_id                                                as _lic_dlt_id,

        -- estado y clasificación (códigos; las etiquetas se unen en marts)
        estado,
        nullif(trim(objeto), '')                               as objeto,
        tipo_contrato,
        subtipo_contrato,
        cpv,

        -- importes
        cast(valor_estimado as decimal(18, 2))                 as valor_estimado,
        cast(presupuesto_sin_impuestos as decimal(18, 2))      as presupuesto_sin_impuestos,
        cast(presupuesto_con_impuestos as decimal(18, 2))      as presupuesto_con_impuestos,

        -- órgano de contratación
        nullif(trim(organo_contratacion), '')                  as organo_contratacion,
        organo_nif,
        organo_dir3,

        -- lugar de ejecución
        nullif(trim(lugar_provincia), '')                      as lugar_provincia,
        lugar_nuts,
        nullif(trim(lugar_municipio), '')                      as lugar_municipio,

        -- proceso
        procedimiento,
        sistema_contratacion,
        urgencia,
        try_cast(plazo_presentacion as date)                   as plazo_presentacion,

        n_lotes,

        -- metadatos
        updated                                                as actualizado_en,
        _year                                                  as anio,
        _dataset                                               as dataset,
        _source_file                                           as fichero_origen
    from deduplicado
)

select * from cleaned
