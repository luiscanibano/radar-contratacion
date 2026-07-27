# PRODUCT.md — Radar de Contratación Pública

## Qué es

Servicio web que ingiere los datos abiertos oficiales de la Plataforma de
Contratación del Sector Público (PLACSP) y permite preguntarles en lenguaje
natural: un agente traduce la pregunta a consultas sobre los datos reales
(text-to-SQL + búsqueda híbrida semántica/texto) y contesta con cifras
verificables. Incluye alertas por email sobre búsquedas guardadas, señales
estadísticas de adjudicaciones atípicas y un servidor MCP remoto.

**Mecanismo único en una frase**: convierte el corpus completo de la
contratación pública española en algo a lo que se le puede preguntar en
castellano y que responde con cifras verificables y señales de anomalía.

## Audiencia (confirmada por el usuario, 2026-07-27)

Prioridad de conversión, por este orden y a partes casi iguales:

1. **Empresas que licitan** (pymes/consultoras): buscan oportunidades y
   quieren alertas de licitaciones nuevas que encajen con lo suyo.
2. **Analistas y consultores** de compras públicas: hoy pelean con ficheros
   y descargas de PLACSP; quieren respuestas sin SQL.
3. **Periodistas y transparencia**: les interesan las señales de riesgo
   (bajas temerarias, concentración de adjudicatarios).

Los desarrolladores (MCP/API) son audiencia secundaria: sección propia, no
protagonista.

**Escena real**: pantalla de oficina, horario laboral, luz ambiente normal;
gente que lee BOE/PLACSP, prensa económica y piezas de periodismo de datos.

## Verdades comerciales y factuales (INVENTAR NADA DE ESTO)

- Planes: Gratis 0 €/mes (10 preguntas), Básico 4,99 €/mes (200), Pro
  14,99 €/mes (1.000), Ilimitado 29,99 €/mes (sin límite).
- Fuente de datos: exclusivamente datos abiertos oficiales de PLACSP.
- Las señales de riesgo son patrones estadísticos a revisar, **nunca
  acusaciones** (lenguaje legal obligatorio; RGPD por diseño).
- Rutas estables: `/` (landing), `/app` (panel), `/docs` (API),
  `/billing/exito`, `/billing/cancelado`, `/mcp` (servidor MCP).
- Dominio: radarcontratacion.com.
- No hay métricas públicas de corpus verificadas para usar en marketing
  (número exacto de licitaciones, etc.): no inventarlas.

## Compromisos de marca

- **Color**: libertad total de paleta (confirmado 2026-07-27); el teal
  anterior (#0d5c63) NO es un compromiso de marca.
- **Intocable**: datos factuales, precios, aviso legal y rutas. El copy de
  marketing puede reescribirse.
- Los tests `api/tests/test_web.py` anclan estos marcadores de texto:
  "Radar de" (landing), "Pregunta al agente" (panel), "Suscripción
  completada", "Pago cancelado", y los `href="/app"` / `href="/docs"` en la
  landing.

## Superficies

- `api/static/index.html` — landing (modo **Persuade**).
- `api/static/app.html` — panel de producto (modo **Operate**): login,
  preguntar al agente, alertas, upgrade de plan. HTML autocontenido + JS
  vanilla, sin framework ni build.
- `api/static/billing_*.html` — retornos de Stripe (Operate).
- Restricción técnica: páginas estáticas autocontenidas servidas por
  FastAPI; sin bundler. Fuentes solo autohospedadas (nada de <link> a
  Google Fonts).

## Suposiciones etiquetadas

- (Suposición) El tono debe ser sobrio y verificable, sin hype: audiencia
  regulada/institucional. Confirmado indirectamente por el aviso legal y la
  petición de "super profesional, minimalista".
