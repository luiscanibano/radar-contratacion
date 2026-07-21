-- Tabla de hechos de licitaciones, lista para análisis y para el agente.
-- Deriva la familia CPV (2 primeros dígitos) y marca posibles señales.

with lic as (
    select * from {{ ref('stg_placsp__licitaciones') }}
)

select
    entry_id,
    expediente,
    objeto,
    organo_contratacion,
    estado,
    tipo_contrato,
    cpv,
    left(cpv, 2)                        as cpv_division,
    valor_estimado,
    presupuesto_sin_impuestos,
    anio,
    actualizado_en,
    -- Señal simple para el módulo de riesgo (se refina en analytics/):
    -- contrato menor si el presupuesto queda justo bajo el umbral de 15.000 €.
    case
        when presupuesto_sin_impuestos between 14000 and 15000 then true
        else false
    end                                 as cerca_umbral_menor
from lic
