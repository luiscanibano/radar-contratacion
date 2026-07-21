-- Test de completitud (warn): un expediente en estado adjudicado/resuelto
-- debería tener al menos una adjudicación registrada. Los que no la tienen
-- señalan huecos en la fuente, no un error del pipeline.

{{ config(severity = 'warn') }}

select l.entry_id
from {{ ref('fct_licitaciones') }} l
where l.estado in ('ADJ', 'RES')
  and not exists (
      select 1
      from {{ ref('fct_adjudicaciones') }} a
      where a.entry_id = l.entry_id
  )
