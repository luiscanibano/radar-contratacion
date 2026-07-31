---
name: Radar de Contratación Pública
description: La contratación pública española, preguntable en castellano con cifras verificables.
colors:
  background: "#f8fafc"
  foreground: "#0f172a"
  card: "#ffffff"
  primary: "#1e40af"
  secondary: "#eef2ff"
  muted: "#f1f5f9"
  accent: "#d97706"
  success: "#16a34a"
  destructive: "#dc2626"
  border: "#e2e8f0"
typography:
  sans:
    fontFamily: "IBM Plex Sans Variable, system-ui, sans-serif"
  mono:
    fontFamily: "JetBrains Mono Variable, ui-monospace, Cascadia Mono, monospace"
rounded:
  control: "0.6rem (radius-sm)"
  card: "1rem (radius-lg)"
  panel: "1.4rem (radius-xl)"
  hero: "1.8rem (radius-2xl)"
stack:
  framework: "Vite + React 18 + TypeScript"
  styling: "Tailwind CSS v4 + shadcn/ui (preset Nova, base Radix)"
  motion: "Framer Motion"
  shaders: "Three.js + @react-three/fiber (fondo del héroe, code-split)"
  icons: "lucide-react"
---

# Design System: Radar de Contratación Pública

<!-- Documentado desde el código construido (web/src/**, 2026-07-28).
     Reemplaza por completo el contrato anterior ("la consola del analista",
     seed d8d987a9): pivote consciente hacia una estética SaaS moderna,
     decidido por el usuario el 2026-07-28 al redisñar la interfaz con
     ui-ux-pro-max + MCP 21st.dev. La verdad es el código en web/. -->

## Overview

**Creative North Star: "Radar SaaS"**

La interfaz dejó de ser un documento de trabajo minimalista para ser un producto
SaaS de IA con vocación comercial: profundidad (glass, sombra, degradado
contenido), una paleta de dos acentos (índigo + ámbar) y movimiento real
(Framer Motion) en vez de transiciones CSS aisladas. El objetivo es transmitir
"herramienta profesional impresionante", no "libro de registro austero" — pero
sigue siendo una herramienta de datos legales: nada de gráficos falsos, nada de
cifras no etiquetadas como ilustrativas, nada de iconos-emoji.

**Key characteristics:**
- Dos acentos con roles fijos: **índigo** (`--primary`) es la acción principal
  y la identidad de marca; **ámbar** (`--accent`) es CTA secundario y señal de
  riesgo estadístico (hereda el rol semántico del sistema anterior).
- Superficies con profundidad: tarjetas (`--card`) con sombra suave, nav y
  paneles de billing con `backdrop-blur`, plan destacado con degradado
  `primary → primary/80`.
- El panel de dato (consola oscura `#0b1220` / `#e7ecf5`) se conserva como
  firma visual para consultas, respuestas del agente y ejemplos de features —
  es el hilo de continuidad con la identidad anterior.
- Modo claro/oscuro vía clase `.dark` en `<html>` (no solo `prefers-color-scheme`):
  se resuelve una vez al cargar (`src/lib/theme.ts:themeInitScript`, inline en
  el `<head>` de cada página para evitar parpadeo) y es conmutable a mano
  (`ThemeToggle`, persistido en `localStorage`).
- Motion real con Framer Motion: entradas escalonadas, hover con spring,
  scroll-linked parallax en la sección de features. El héroe lleva además un
  fondo WebGL (Three.js/React Three Fiber, shader propio) con dos planos de
  ruido animado en índigo/ámbar y un anillo girando; en el resto de superficies
  (billing) el fondo es `GradientBlobs`, blobs CSS con deriva lenta. Ambos son
  bucles continuos — las únicas animaciones en bucle del sistema — y ambos se
  desactivan por completo con `prefers-reduced-motion`.

## Stack

- **Vite + React 18 + TypeScript**, app multi-página (no SPA-router): 4
  entries independientes que se corresponden 1:1 con las rutas de FastAPI —
  `web/index.html` (`/`), `web/app/index.html` (`/app`),
  `web/billing/exito/index.html` y `web/billing/cancelado/index.html`.
  Configurado en `web/vite.config.ts:build.rollupOptions.input`.
- **Tailwind CSS v4** vía `@tailwindcss/vite`, sin `tailwind.config.js` — los
  tokens viven como variables CSS en `web/src/index.css` bajo `@theme inline`
  + `:root` / `.dark`.
- **shadcn/ui** (preset Nova, base Radix) para primitivas accesibles (`Button`,
  `Card`, `Input`, `Textarea`, `Label`, `Badge`, `Separator`) — instalado con
  `npx shadcn@latest add <componente>` desde `web/`.
- **Framer Motion** para toda la animación (`web/src/components/Reveal.tsx` son
  los helpers de entrada por scroll reutilizados en toda la landing).
- **Three.js + @react-three/fiber** solo para el fondo del héroe
  (`ShaderScene.tsx` / `components/ui/background-paper-shaders.tsx`) — cargado
  con `React.lazy`/`Suspense` (`ShaderBackground.tsx`) para no bloquear el
  primer render del texto/CTA, y omitido del todo con `prefers-reduced-motion`.
- **lucide-react** para iconos (reemplaza los SVG inline de Tabler Icons del
  sistema anterior).
- **Fontsource** (`@fontsource-variable/ibm-plex-sans`,
  `@fontsource-variable/jetbrains-mono`) autohospedadas vía npm/Vite — sin
  `<link>` a Google Fonts en runtime.
- Despliegue: `api/Dockerfile` construye `web/` en una etapa Node y copia
  `web/dist` a `api/static`; `api/main.py` sirve las 4 páginas con
  `FileResponse` y monta `/assets` para los JS/CSS/fuentes con hash.

## Colors

Dos acentos con roles fijos (a diferencia del "único acento" del sistema
anterior), sobre una base neutra fría. Valores en `web/src/index.css`.

### Primary — índigo
`--primary` (#1e40af claro / #7c93f5 oscuro): marca, CTA principal, enlaces,
anillo de foco, plan destacado. Es la acción por defecto.

### Accent — ámbar
`--accent` (#d97706 claro / #f59e0b oscuro): CTA secundario destacado (badge
"Más elegido" en precios) y color de señal estadística de riesgo dentro del
panel de dato — mismo rol semántico que el `--consola-ambar` del sistema
anterior, ahora también reutilizado como acento visual, no solo semántico.

### Success / Destructive
`--success` (#16a34a / #4ade80) y `--destructive` (#dc2626 / #f87171): estados
de formulario (error de auth/alertas/billing, icono de éxito en
`/billing/exito`).

### Neutrales
`--background` / `--foreground` (papel frío #f8fafc / carbón #0b1220 —
oscuro no es negro puro, para que el glass tenga profundidad), `--card`
(superficie elevada, blanco puro en claro / #111a2e en oscuro), `--muted`,
`--secondary`, `--border`.

### Panel de dato (heredado, sin cambios de rol)
Fondo `#0b1220`, texto `#e7ecf5`, hairlines internas `white/10` — **no cambia
entre tema claro y oscuro** (mismo principio que la "Regla del Panel
Invariante" anterior): el dato se lee igual a cualquier hora. Vive en
`ConsolePanel.tsx`, reutilizado en el hero, en cada feature y en la respuesta
del agente.

## Typography

**Sans:** IBM Plex Sans Variable — titulares y cuerpo. Elegida por su
asociación con herramientas de datos/dev (IBM Plex es la familia de referencia
de paneles técnicos) y por transmitir seriedad profesional sin ser fría.

**Mono:** JetBrains Mono Variable — todo dato verificable (consultas, cifras,
precios, ejemplos de features, respuesta del agente). Se conserva del sistema
anterior: sigue siendo la señal tipográfica de "esto es dato, no marketing".

Ambas autohospedadas vía Fontsource (`web/src/index.css`), eje de peso
variable únicamente (sin cursiva ni ancho, no se necesitan).

## Shapes

Radios ampliados frente al sistema anterior (6/10px): escala derivada de
`--radius: 1rem` en `web/src/index.css` — `sm` 0.6rem (controles), `lg` 1rem
(tarjetas), `xl` 1.4rem (paneles de dato, feature cards), `2xl` 1.8rem
(hero/CTA cards). Bordes de 1px; el plan destacado en precios usa un borde con
degradado en vez de hairline.

## Elevation & Depth

A diferencia del "sistema plano" anterior, aquí la profundidad es una
herramienta expresiva: `shadow-sm`/`shadow-xl` en tarjetas, `shadow-glow`
(`--shadow-glow` en `index.css`) para paneles de dato flotantes (héroe, MCP),
`backdrop-blur` en el nav sticky y en las tarjetas de auth/billing. El botón
primario y las tarjetas de precio no destacadas se mantienen sin sombra para
que la jerarquía de atención no se sature.

## Components

Componentes reutilizables en `web/src/components/`:

- **`ConsolePanel` / `ConsoleMembrete`** — el panel de dato (firma visual
  heredada). Usado en `HeroConsoleDemo`, `ParallaxFeatures`, `AskAgent` y
  `McpSection`.
- **`Reveal` / `RevealGroup` / `RevealItem`** — entrada por scroll
  (`whileInView`, una vez, `useReducedMotion` respetado) para toda la landing.
- **`ParallaxFeatures`** — sección "Qué hace": 3 bloques a pantalla parcial con
  parallax real (`useScroll` + `useTransform` por sección, clip-path +
  opacidad + traslación), alternando lado texto/panel.
- **`ShaderBackground` / `ShaderScene`** — fondo del héroe: dos planos con
  shader de ruido animado (`ui/background-paper-shaders.tsx`, índigo/ámbar) y
  un anillo girando, sobre WebGL (Three.js/React Three Fiber). Bucle continuo,
  code-split y ausente del todo con `prefers-reduced-motion`.
- **`GradientBlobs`** — el mismo concepto de fondo pero en CSS puro (sin
  WebGL), usado en las páginas de billing: dos blobs de degradado
  (`primary`/`accent`) con blur y deriva lenta en bucle.
- **`PricingCard`** — tarjeta de plan reutilizada en la landing (4 planes,
  enlaces) y en `PlanUpgrade` del panel (3 planes, botones de checkout); el
  plan `destacado` lleva degradado `primary→primary/80` y badge ámbar.
- **`AuthCard` / `AskAgent` / `AlertsManager` / `PlanUpgrade`** — superficies
  "Operate" del panel `/app`, todas con estado de carga/error inline (sin
  toasts, igual que el sistema anterior) y animación de entrada/salida con
  `AnimatePresence` en listas (alertas) y paneles de respuesta.
- **`LandingNav` / `AppTopBar`** — cabeceras; `LandingNav` es un pill flotante
  con blur que se intensifica al hacer scroll (`useScroll` + `useMotionValueEvent`,
  no un listener de scroll a mano).
- **`ThemeToggle`** — conmuta `.dark` en `<html>` y persiste en
  `localStorage` (`web/src/lib/theme.ts`).

## Motion

- **Entrada por scroll:** fade + slide 24px, 0.6s, ease `[0.22,1,0.36,1]`, una
  sola vez (`whileInView`, `viewport.once`). Grupos con
  `staggerChildren` (0.07–0.08s).
- **Parallax de features:** progreso de scroll por sección
  (`useScroll({target, offset:["start end","center center"]})`) controla
  opacidad, `clip-path` y traslación vertical del panel de ejemplo.
- **Hover:** spring (`stiffness: 300, damping: 22–24`) con `y: -4` y ligera
  escala en tarjetas; `whileTap` con `scale: 0.96` en botones si aplica.
- **Listas (alertas, respuesta del agente):** `AnimatePresence` +
  `layout`, entrada/salida por altura y opacidad.
- **Fondo:** blobs con deriva continua (`repeat: Infinity`, 26–30s,
  `easeInOut`) — el único movimiento en bucle del sistema.
- **Accesibilidad:** todo lo anterior respeta `useReducedMotion()` de Framer
  Motion — con movimiento reducido, los elementos aparecen en su estado final
  sin animar (nunca se ocultan permanentemente ni dependen del JS para ser
  legibles).

## Do's and Don'ts

### Do:
- **Do** usar el panel de dato (`ConsolePanel`) para toda cifra, consulta o
  respuesta del agente — sigue siendo la señal de "esto es dato real o
  ilustrativo etiquetado", no marketing.
- **Do** reservar el ámbar para CTA secundario destacado o señal de riesgo;
  el índigo es la acción por defecto.
- **Do** etiquetar los datos de ejemplo como "datos ilustrativos" cuando no
  salgan del corpus real (se mantiene del sistema anterior).
- **Do** respetar `prefers-reduced-motion` en cualquier animación nueva.

### Don't:
- **Don't** añadir un tercer acento de color; índigo + ámbar + neutros +
  éxito/error ya cubren toda la jerarquía semántica necesaria.
- **Don't** usar emojis como iconos — solo `lucide-react`.
- **Don't** introducir animaciones en bucle nuevas fuera de `ShaderBackground`/
  `GradientBlobs`; el resto del movimiento se dispara una vez.
- **Don't** enlazar fuentes o scripts de terceros en runtime (Google Fonts,
  CDNs) — todo autohospedado vía npm/Vite.
