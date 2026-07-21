-- Test duro: ningún importe de adjudicación puede ser negativo.
-- Devuelve filas que incumplen (el test falla si hay alguna).

select
    adjudicacion_id,
    importe_sin_impuestos
from {{ ref('fct_adjudicaciones') }}
where importe_sin_impuestos < 0
