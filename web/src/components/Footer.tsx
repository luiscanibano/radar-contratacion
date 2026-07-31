import { Brand } from "@/components/Brand";
import { RuixenGradientFooter } from "@/components/ui/ruixen-gradient-footer";

const PRODUCTO = [
  { label: "Precios", href: "#precios" },
  { label: "Documentación de la API", href: "/docs" },
];

const LEGAL = [
  { label: "Privacidad", href: "/legal#privacidad" },
  { label: "Términos de uso", href: "/legal#terminos" },
  { label: "Cookies", href: "/legal#cookies" },
];

// lucide-react no incluye logotipos de marca; icono mínimo propio.
function LinkedinIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden>
      <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.04-1.85-3.04-1.86 0-2.15 1.45-2.15 2.94v5.67H9.35V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.59 0 4.25 2.37 4.25 5.44v6.3ZM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12ZM7.12 20.45H3.56V9h3.56v11.45Z" />
    </svg>
  );
}

export function Footer() {
  return (
    <RuixenGradientFooter
      gradientHeight="26vh"
      className="relative border-t border-border"
    >
      <div className="mx-auto max-w-6xl px-6 pt-16">
        <div className="grid gap-10 border-b border-border/60 pb-10 sm:grid-cols-2 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <Brand iconOnly size="lg" />
            <p className="mt-4 max-w-sm text-sm text-pretty text-muted-foreground">
              Pregunta a las licitaciones públicas españolas y vigila el sector con alertas y
              señales de riesgo.
            </p>
          </div>

          <div>
            <h3 className="font-mono text-xs uppercase tracking-wider text-foreground">
              Producto
            </h3>
            <ul className="mt-4 flex flex-col gap-3 text-sm">
              {PRODUCTO.map((item) => (
                <li key={item.href}>
                  <a href={item.href} className="text-muted-foreground hover:text-foreground">
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-mono text-xs uppercase tracking-wider text-foreground">
              Legal
            </h3>
            <ul className="mt-4 flex flex-col gap-3 text-sm">
              {LEGAL.map((item) => (
                <li key={item.href}>
                  <a href={item.href} className="text-muted-foreground hover:text-foreground">
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-mono text-xs uppercase tracking-wider text-foreground">
              Conecta
            </h3>
            <ul className="mt-4 flex flex-col gap-3 text-sm">
              <li>
                <a
                  href="https://www.linkedin.com/in/luis-ca%C3%B1ibano-mateos-7a403139a/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground"
                >
                  <LinkedinIcon className="size-4" />
                  LinkedIn
                </a>
              </li>
            </ul>
          </div>
        </div>

        <p className="max-w-[75ch] text-pretty py-6 text-sm text-muted-foreground">
          <strong className="text-foreground">Aviso legal.</strong> Este servicio usa
          exclusivamente datos abiertos oficiales de la Plataforma de Contratación del Sector
          Público. El análisis se presenta de forma agregada y las señales de riesgo describen
          patrones estadísticos a revisar, nunca acusaciones. Cumplimiento RGPD por diseño.
        </p>

        <div className="flex flex-col items-center justify-between gap-3 pb-2 text-xs text-muted-foreground sm:flex-row">
          <span>© 2026 Radar de Contratación Pública</span>
        </div>
      </div>
    </RuixenGradientFooter>
  );
}
