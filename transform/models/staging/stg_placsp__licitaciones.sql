-- Limpieza y tipado de las licitaciones crudas de PLACSP.
-- Normaliza importes (texto -> decimal) y fechas.

with source as (
    select * from {{ source('raw', 'licitaciones') }}
),

cleaned as (
    select
        entry_id,
        expediente,
        nullif(trim(objeto), '')                          as objeto,
        nullif(trim(organo_contratacion), '')             as organo_contratacion,
        estado,
        tipo_contrato,
        cpv,
        -- Los importes vienen como texto; DuckDB castea con seguridad vía try_cast
        try_cast(valor_estimado as decimal(18, 2))         as valor_estimado,
        try_cast(presupuesto_sin_impuestos as decimal(18, 2)) as presupuesto_sin_impuestos,
        try_cast(updated as timestamp)                     as actualizado_en,
        _year                                              as anio,
        _dataset                                           as dataset,
        _source_file                                       as fichero_origen
    from source
)

select * from cleaned
