# web

Interfaz web del Radar de Contratación Pública. Vite + React + TypeScript +
Tailwind CSS v4 + shadcn/ui + Framer Motion. Ver `../DESIGN.md` para el
sistema de diseño y `../.claude/launch.json` para los comandos de desarrollo.

App multi-página (sin router de cliente), una entrada por ruta de la API:

| Ruta                 | Entry                            |
| --------------------- | --------------------------------- |
| `/`                   | `index.html`                      |
| `/app`                | `app/index.html`                  |
| `/billing/exito`      | `billing/exito/index.html`        |
| `/billing/cancelado`  | `billing/cancelado/index.html`    |

```bash
npm install
npm run dev    # servidor de desarrollo (proxy a la API en :8000, ver vite.config.ts)
npm run build  # build de producción -> dist/ (lo copia api/Dockerfile a api/static)
```
