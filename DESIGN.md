---
name: Radar de Contratación Pública
description: La contratación pública española, preguntable en castellano con cifras verificables.
colors:
  papel: "#f4f5f4"
  tinta: "#16181a"
  tinta-suave: "#575d61"
  regla: "#d8dbd9"
  acento: "#2647c1"
  acento-hover: "#1c37a0"
  consola: "#101315"
  consola-tinta: "#e9ebea"
  consola-suave: "#969ea3"
  consola-regla: "#272c2f"
  consola-ambar: "#f0b429"
  error: "#a83a31"
  exito: "#1e7d43"
typography:
  display:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(2rem, 4.2vw, 3.1rem)"
    fontWeight: 640
    lineHeight: 1.08
    letterSpacing: "-0.025em"
  titulo:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.45rem"
    fontWeight: 620
    lineHeight: 1.25
    letterSpacing: "-0.02em"
  rotulo-seccion:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 560
    lineHeight: 1.6
    letterSpacing: "normal"
  cuerpo:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "normal"
  dato:
    fontFamily: "JetBrains Mono, ui-monospace, Cascadia Mono, monospace"
    fontSize: "0.84rem"
    fontWeight: 400
    lineHeight: 1.75
    letterSpacing: "normal"
rounded:
  control: "6px"
  panel: "10px"
components:
  boton-primario:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.papel}"
    rounded: "{rounded.control}"
    padding: "0.65rem 1.25rem"
  boton-primario-hover:
    backgroundColor: "{colors.acento-hover}"
    textColor: "#ffffff"
  boton-secundario:
    backgroundColor: "transparent"
    textColor: "{colors.tinta}"
    rounded: "{rounded.control}"
    padding: "0.65rem 1.25rem"
  campo:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.control}"
    padding: "0.6rem 0.75rem"
  panel-tinta:
    backgroundColor: "{colors.consola}"
    textColor: "{colors.consola-tinta}"
    rounded: "{rounded.panel}"
    padding: "1.4rem 1.5rem"
---

# Design System: Radar de Contratación Pública

<!-- Documentado desde el código construido (api/static/*, 2026-07-27).
     Contrato de dirección: "La consola del analista", seed d8d987a9,
     aprobado por el usuario el 2026-07-27. La verdad es el código. -->

## Overview

**Creative North Star: "La consola del analista"**

Papel frío y tinta: la interfaz es un documento de trabajo, no un folleto SaaS.
El mundo tiene dos materiales y solo dos. El **papel** (`--papel`) es la
superficie de lectura: sobre él viven el texto, las reglas finas y los
controles. El **panel de tinta** (`--consola`) es la superficie del dato: una
consola oscura donde las cifras, las consultas y las respuestas del agente se
presentan en monoespaciada. Todo lo demás —tarjetas flotantes, degradados,
ilustraciones, hero centrado con tres columnas de features— queda fuera del
mundo.

El tono es sobrio y verificable, para una audiencia que lee BOE y PLACSP en
pantalla de oficina. La landing se comporta como el producto: el primer
viewport es una consulta resolviéndose, no un muro de claims. La densidad es
la de un libro de registro: filas separadas por reglas finas, columnas
alineadas, cifras tabulares.

**Key Characteristics:**
- Dos materiales: papel de lectura y panel de tinta para el dato.
- Reglas finas de 1px (`--regla`) en lugar de tarjetas.
- Un único acento (cobalto); el ámbar es exclusivamente semántico.
- Bimodal claro/oscuro vía `prefers-color-scheme`; el panel de tinta es
  idéntico en ambos temas.
- Un solo momento de motion con autor por superficie.
- HTML autocontenido, fuentes autohospedadas, sin framework ni build.

## Colors

Paleta de dos materiales con un solo acento cromático; los nombres de los
tokens están en castellano y son la nomenclatura obligatoria. El frontmatter
recoge los valores del tema claro (canónico); el tema oscuro redefine los
tokens indicados abajo dentro de `@media (prefers-color-scheme: dark)`.

### Primary
- **Cobalto** (`--acento`, #2647c1 claro / #93a7ff oscuro): el único acento.
  Términos del registro, enlaces de acción, plan destacado (inset de 2px),
  importe destacado y anillo de foco. Su escasez es deliberada.
- **Cobalto hundido** (`--acento-hover`, #1c37a0 claro / #b0bfff oscuro):
  exclusivamente el fondo de hover de los botones.

### Secondary
- **Ámbar de señal** (`--consola-ambar`, #f0b429 en ambos temas): reservado a
  las señales estadísticas de riesgo dentro del panel de tinta. Nunca
  decorativo, nunca sobre papel.

### Neutral
- **Papel frío** (`--papel`, #f4f5f4 claro / #121415 oscuro): fondo de página
  y texto de los botones primarios.
- **Tinta** (`--tinta`, #16181a claro / #e8eae9 oscuro): texto principal y
  fondo del botón primario.
- **Tinta suave** (`--tinta-suave`, #575d61 claro / #9aa1a5 oscuro): texto
  secundario, subtítulos, rótulos de sección, pie.
- **Regla** (`--regla`, #d8dbd9 claro / #272b2d oscuro): las líneas finas de
  1px que estructuran todo; también el borde de botones secundarios e inputs.
- **Consola** (`--consola`, #101315 claro / #0b0e10 oscuro): fondo del panel
  de tinta.
- **Tinta de consola** (`--consola-tinta`, #e9ebea): texto dentro del panel;
  no cambia con el tema.
- **Consola suave** (`--consola-suave`, #969ea3): texto secundario del panel
  (membrete, estados, prefijo `›`); no cambia con el tema.
- **Regla de consola** (`--consola-regla`, #272c2f claro / #23282b oscuro):
  hairlines internas del panel de tinta.

### Estado (solo superficies Operate)
- **Error** (`--error`, #a83a31 claro / #e08078 oscuro): mensajes de error del
  panel. Solo texto, nunca fondos.
- **Éxito** (`--exito`, #1e7d43 claro / #5fc98a oscuro): mensajes de éxito y
  el icono de suscripción completada. Solo texto e icono de trazo.

### Named Rules
**La Regla del Único Acento.** El cobalto es el único color de acento del
sistema. Si una superficie nueva necesita "otro color", la respuesta es tinta,
tinta suave o nada.

**La Regla del Ámbar Semántico.** El ámbar significa "señal estadística a
revisar" y nada más. Aparece solo dentro del panel de tinta, precedido del
marcador `■`. Usarlo como decoración rompe el contrato legal del producto.

**La Regla del Panel Invariante.** El panel de tinta es idéntico en tema claro
y oscuro: `--consola-tinta`, `--consola-suave` y `--consola-ambar` no se
redefinen en dark. El dato se lee igual a cualquier hora.

## Typography

**Display Font:** Archivo variable (`/static/fonts/archivo-vf.woff2`, ejes
100–900, con fallback `system-ui, sans-serif`)
**Body Font:** Archivo (la misma variable; el peso hace la jerarquía)
**Label/Mono Font:** JetBrains Mono variable
(`/static/fonts/jetbrains-mono-vf.woff2`, ejes 100–800, con fallback
`ui-monospace, "Cascadia Mono", monospace`)

**Character:** Una sola sans neogrotesca que trabaja por peso y tracking, sin
cambiar de voz, más una monoespaciada que marca inequívocamente "esto es
dato". Las fuentes son siempre autohospedadas (`font-display: swap`); nunca un
`<link>` a Google Fonts.

### Hierarchy
- **Display** (640, `clamp(2rem, 4.2vw, 3.1rem)`, 1.08, -0.025em): el h1 del
  héroe, con `text-wrap: balance`. Uno por página.
- **Título** (620, 1.45rem, 1.25, -0.02em): titulares de fila del registro y
  h1 de los avisos de billing.
- **Rótulo de sección** (560, 1.05rem, color tinta suave): los h2. Deliberadamente
  discretos: la sección la nombra un rótulo, no un titular.
- **Cuerpo** (400, 1rem, 1.6): texto corriente; el secundario en tinta suave
  con `text-wrap: pretty`. Subtítulo del héroe a 1.1rem, máx. 46ch.
- **Dato** (JetBrains Mono, 0.84rem en panel, 0.72–0.8rem en membretes,
  términos y metadatos, 1.7–1.75 de interlineado): consultas, cifras, precios,
  emails de sesión, términos del registro y bloques de código.
- **Marca** (680, 1rem, -0.01em): el nombre del producto en la cabecera.
- **Importe** (JetBrains Mono 560, 1.6rem, `tabular-nums`): precios de los
  planes.

### Named Rules
**La Regla del Dato Mono.** Toda cifra de negocio, consulta, precio,
identificador o metadato técnico se compone en JetBrains Mono; los importes y
tablas siempre con `font-variant-numeric: tabular-nums`. Si es verificable, es
mono.

**La Regla de los Pesos Intermedios.** Archivo es variable: los pesos del
sistema son 560 (controles y rótulos), 620 (títulos), 640 (display) y 680
(marca), con trackings negativos crecientes con el tamaño. No usar 400/700
genéricos para jerarquía de display.

## Layout

Columna única centrada con anchos por modo: **1080px** para persuadir
(landing), **720px** para operar (panel), **460px** para avisos (billing);
padding lateral de 1.5rem en todos.

La estructura es de **libro de registro**: secciones y filas separadas por
reglas de 1px (`--regla`), nunca por cajas. El registro de funciones es una
retícula de tres columnas (`9rem` término / `5fr` titular / `6fr` prosa) con
filas de 1.9rem de padding vertical. Las tablas de planes son retículas donde
los divisores son bordes compartidos (`border-left` entre planes,
`border-bottom` por fila), no tarjetas separadas. El héroe es un split
asimétrico `10fr / 9fr` con 3.5rem de separación: gancho y CTAs a la
izquierda, panel de tinta a la derecha.

Ritmo vertical: secciones a 4.5rem, cabecera a 1.1rem de padding, pie a
2.25rem. Breakpoints observados: **900px** (héroe y registro a una columna;
planes a 2×2), **620px** (la navegación textual desaparece, queda marca +
botón), **560px** (planes a una columna; panel de tinta compacto a 0.78rem).

## Elevation & Depth

Sistema plano. El papel no proyecta sombras: la profundidad la da el contraste
de material entre papel y panel de tinta. La única sombra del sistema es la
del panel de tinta flotando sobre el papel:
`box-shadow: 0 16px 40px rgb(9 11 12 / .22)` (la variante `.18` en el bloque
MCP). Los controles no tienen sombra en ningún estado.

### Named Rules
**La Regla de la Sombra Única.** Solo el panel de tinta proyecta sombra, y
solo cuando flota como pieza protagonista (héroe, bloque de código). La
respuesta del agente dentro del panel de la app no la lleva: allí el panel
está encastrado en el flujo, no flotando.

## Shapes

Dos radios y ninguno más: **6px** para controles (botones, inputs, anillo de
foco) y **10px** para paneles de tinta (consola, bloques `pre`, respuesta del
agente). Los bordes son siempre de 1px. Sin píldoras, sin círculos
decorativos, sin esquinas a 0.

El lenguaje de marcas es tipográfico: el prompt de consulta se prefija con
`› ` en consola suave, la señal de riesgo con un cuadrado `■ ` en ámbar. El
cursor de tecleo es un bloque sólido de 0.55em × 1.1em.

## Components

### Buttons
- **Carácter:** rotundos y silenciosos; la interacción se nota en la mano
  (transform), no en fuegos artificiales.
- **Shape:** radio de control (6px), sin borde el primario, `padding
  .65rem 1.25rem` (landing) / `.55rem 1.1rem` (app); variante `pequeno`
  a `.3rem .7rem` y .85rem.
- **Primario:** fondo tinta, texto papel, peso 560, .95rem.
- **Secundario:** fondo transparente, texto tinta, borde 1px regla; en hover
  solo el borde pasa a tinta suave.
- **Hover:** el primario pasa a cobalto hundido con texto blanco (en oscuro,
  texto `--consola`); siempre dentro de `@media (hover: hover) and (pointer:
  fine)`.
- **Active:** `transform: scale(0.97)` con transición de 160ms sobre
  `cubic-bezier(0.23, 1, 0.32, 1)`; el resto de propiedades a 160ms `ease`.
- **Disabled:** opacidad .55 y `cursor: wait`; los estados hover/active lo
  excluyen (`:not(:disabled)`).
- **Focus:** `outline: 2px solid var(--acento)` con offset de 2px.

### Inputs / Fields
- **Style:** fondo papel, borde 1px regla, radio 6px, `font: inherit`,
  padding `.6rem .75rem`; los textarea con `resize: vertical` y min-height
  5.5rem. Etiquetas encima, en .85rem tinta suave.
- **Focus:** `outline: 2px solid var(--acento)` con offset -1px y el borde
  también en acento; transición de borde a 150ms.
- **Error:** los errores no colorean el campo; aparecen como mensaje de texto
  debajo (ver Mensajes).

### Panel de tinta (componente firma)
El recipiente del dato: fondo `--consola`, texto `--consola-tinta`, borde 1px
`--consola-regla`, radio 10px, JetBrains Mono a 0.84rem con interlineado 1.75.
Variantes construidas: la consola del héroe (membrete de dos puntas en
0.72rem consola suave separado por hairline; pregunta con prefijo `›`; tabla
de resultados con hairlines internas `--consola-regla` y cifras tabulares
alineadas a la derecha; línea de señal en ámbar), el bloque de configuración
MCP (`pre` con scroll horizontal) y la respuesta del agente en la app
(`white-space: pre-wrap`, sin sombra). Los datos ilustrativos se etiquetan
como tales en el membrete: el mundo no presume cifras que no puede verificar.

### Registro / listas
Filas separadas por hairline `--regla`, sin fondo propio. En la landing:
término mono en cobalto + titular 620 + prosa en tinta suave. En la app las
alertas son filas flex (texto mono a 0.8rem + botón Borrar pequeño) y el
estado vacío es una fila más en tinta suave, no un empty-state ilustrado.

### Navigation
Cabecera de una línea: marca (680) a la izquierda, enlaces en tinta suave (a
tinta en hover, 150ms) y un botón secundario de sesión a la derecha; separada
del contenido por una hairline. En móvil (≤620px) los enlaces textuales
desaparecen y quedan marca y botón.

### Mensajes de estado
Texto plano de .95rem bajo el formulario que los provoca: `--error` o
`--exito` según el caso. Sin fondos, sin iconos, sin toasts. Solo existen en
las superficies Operate (app y billing).

### Iconografía
Tabler Icons (MIT), SVG inline de trazo (`stroke-width: 1.5`,
`stroke-linecap/linejoin: round`), 44px en los avisos de billing,
`aria-hidden="true"` y color por `currentColor` (éxito o tinta suave). Sin
fuentes de iconos ni emojis.

### Motion
- **Un momento con autor por superficie.** En la landing: la consulta del
  héroe se teclea una vez (26ms por carácter tras 350ms, cursor parpadeando a
  1.1s `steps(1)`) y los resultados se revelan escalonados: opacidad 400ms
  `cubic-bezier(0.23, 1, 0.32, 1)`, arrancando a 260ms y con escalón de 90ms
  por paso. Sin JS o con `prefers-reduced-motion`, todo el contenido queda
  visible en su estado final desde el primer render.
- **Micro-feedback:** solo el `scale(0.97)` de los botones (160ms, la misma
  curva) y transiciones de color de 150–160ms.
- **La Regla de la Curva Única.** Toda animación con desplazamiento u opacidad
  usa `cubic-bezier(0.23, 1, 0.32, 1)`; los cambios de color usan `ease`. No
  se introducen curvas nuevas.
- **La Regla del Respeto al Movimiento.** Todo hover vive tras `@media
  (hover: hover) and (pointer: fine)`; toda animación, tras
  `prefers-reduced-motion: no-preference` (o un early-return en JS). El estado
  final siempre es legible sin animación.

## Do's and Don'ts

### Do:
- **Do** separar contenido con hairlines de 1px `--regla`; la estructura del
  mundo es un libro de registro.
- **Do** poner todo dato verificable (cifras, consultas, precios, código) en
  JetBrains Mono, y las tablas de cifras con `tabular-nums` alineadas a la
  derecha.
- **Do** definir ambos temas por `prefers-color-scheme` en cada superficie
  nueva, manteniendo el panel de tinta idéntico en los dos.
- **Do** dar a todo elemento interactivo `:focus-visible` con `outline: 2px
  solid var(--acento)` y offset 2px (−1px en campos).
- **Do** etiquetar los datos de ejemplo como "datos ilustrativos" cuando no
  salgan del corpus real.
- **Do** mantener cada página autocontenida: CSS y JS inline, fuentes desde
  `/static/fonts/`, cero dependencias externas.

### Don't:
- **Don't** crear tarjetas con fondo y sombra sobre el papel; el único
  recipiente con fondo propio es el panel de tinta.
- **Don't** usar el ámbar fuera de una señal estadística, ni el error/éxito
  fuera de mensajes de estado en superficies Operate.
- **Don't** introducir un segundo color de acento, degradados o rellenos
  decorativos; el cobalto trabaja solo.
- **Don't** añadir animaciones ambientales, parallax o transiciones de
  entrada por sección: cada superficie tiene como mucho un momento de motion
  con autor.
- **Don't** enlazar fuentes ni scripts de terceros (Google Fonts, CDNs);
  rompe el compromiso de autocontención.
- **Don't** usar radios distintos de 6px (controles) y 10px (paneles), ni
  bordes de más de 1px.
