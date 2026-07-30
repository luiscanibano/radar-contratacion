import { useCallback, useRef, useState, type KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import { BellRing, MessagesSquare, TriangleAlert, type LucideIcon } from "lucide-react";
import { FeatureConsoleDemo, type FeatureDemo } from "@/components/FeatureConsoleDemo";
import { GradientWordReveal } from "@/components/ui/gradient-word-reveal";
import { RadialBackground } from "@/components/ui/radial-background";
import { cn } from "@/lib/utils";

gsap.registerPlugin(ScrollTrigger);

interface Feature {
  icon: LucideIcon;
  titulo: string;
  resumen: string;
  texto: string;
  query: string;
  demo: FeatureDemo;
}

const FUNCIONES: Feature[] = [
  {
    icon: MessagesSquare,
    titulo: "Un agente que contesta en castellano",
    resumen: "Preguntas en lenguaje natural, respuestas con cifras verificables.",
    texto:
      "Text-to-SQL y búsqueda híbrida (semántica y texto) sobre el corpus completo de licitaciones, adjudicatarios, importes y plazos. Cada respuesta, con cifras verificables.",
    query: "¿cuánto adjudicó mi ayuntamiento este año y a quién?",
    demo: {
      kind: "table",
      nota: "sql generado y ejecutado sobre el corpus completo",
      filas: [
        { entidad: "Ayto. de Madrid", contratos: "214 contratos", importe: "312,4 M€" },
        { entidad: "Ayto. de Barcelona", contratos: "187 contratos", importe: "248,9 M€" },
        { entidad: "Ayto. de Valencia", contratos: "112 contratos", importe: "131,7 M€" },
      ],
    },
  },
  {
    icon: BellRing,
    titulo: "Alertas cuando se publica lo tuyo",
    resumen: "Guarda una búsqueda y te avisamos por email.",
    texto:
      "Guarda una búsqueda («obras de accesibilidad en Castilla y León») y recibe un email cuando entren licitaciones nuevas que encajen.",
    query: "obras de accesibilidad en Castilla y León",
    demo: {
      kind: "log",
      nota: "búsqueda guardada — se te avisará por email",
      lineas: [
        { tiempo: "14:02", texto: "centros educativos, Junta de Castilla y León", tono: "success" },
        { tiempo: "09:41", texto: "edificio consistorial, Ayto. de León", tono: "success" },
        { tiempo: "ayer", texto: "itinerario peatonal, Diputación de Salamanca", tono: "success" },
      ],
    },
  },
  {
    icon: TriangleAlert,
    titulo: "Anomalías estadísticas, marcadas",
    resumen: "Señales a revisar, nunca acusaciones.",
    texto:
      "Bajas temerarias, importes fuera de rango, concentración de adjudicatarios. Señales a revisar, nunca acusaciones.",
    query: "bajas temerarias en obras de pavimentación, 2024",
    demo: {
      kind: "log",
      nota: "análisis estadístico sobre el corpus completo",
      lineas: [
        { texto: "38 adjudicaciones revisadas", tono: "default" },
        { texto: "baja atípica respecto al presupuesto de licitación (ejemplo)", tono: "accent" },
      ],
    },
  },
];

export function FeaturesShowcase() {
  const [active, setActive] = useState(0);
  const [headingRevealed, setHeadingRevealed] = useState(false);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const feature = FUNCIONES[active];

  useGSAP(
    () => {
      if (!headingRef.current) return;
      const trigger = ScrollTrigger.create({
        trigger: headingRef.current,
        start: "top 85%",
        once: true,
        onEnter: () => setHeadingRevealed(true),
      });
      return () => trigger.kill();
    },
    { scope: headingRef },
  );

  const onKeyDown = useCallback((e: KeyboardEvent<HTMLUListElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(FUNCIONES.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(0, i - 1));
    }
  }, []);

  return (
    <section id="funciones" className="relative flex flex-col justify-center pb-40 pt-6">
      <RadialBackground />
      <div className="mx-auto w-full max-w-6xl px-6">
        <div className="mb-12 max-w-3xl lg:mb-16">
          <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Qué hace</p>
          <h2
            ref={headingRef}
            className="mt-3 text-4xl font-medium leading-tight tracking-tight sm:text-5xl lg:text-6xl"
          >
            <GradientWordReveal words={["Pregunta.", "Vigila.", "Detecta."]} revealed={headingRevealed} />
          </h2>
          <p className="mt-4 text-pretty text-lg text-muted-foreground md:text-xl">
            Un mismo agente para las tres cosas: resuelve una duda puntual, guarda una vigilancia
            permanente o te avisa cuando algo se sale de lo normal.
          </p>
        </div>

        <div className="grid gap-10 lg:grid-cols-2 lg:gap-16">
          <div className="relative">
            <div aria-hidden className="absolute bottom-2 left-3 top-2 w-px bg-border/40" />
            <ul
              className="space-y-1 pl-8"
              role="tablist"
              aria-label="Funciones del agente"
              onKeyDown={onKeyDown}
            >
              {FUNCIONES.map((f, i) => {
                const isActive = i === active;
                return (
                  <li key={f.titulo} className="relative">
                    <button
                      type="button"
                      role="tab"
                      aria-selected={isActive}
                      onClick={() => setActive(i)}
                      className="group relative w-full rounded-md py-3 pl-4 pr-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                    >
                      {isActive && (
                        <motion.span
                          layoutId="funcion-indicador"
                          className="absolute -left-5 top-1 bottom-1 w-[3px] rounded-full bg-gradient-to-b from-primary to-accent"
                          transition={{ type: "spring", bounce: 0.2, duration: 0.45 }}
                        />
                      )}
                      <span
                        className={cn(
                          "flex items-center gap-2 text-base font-medium transition-colors",
                          isActive ? "text-foreground" : "text-muted-foreground/70 group-hover:text-foreground",
                        )}
                      >
                        <f.icon
                          className={cn(
                            "size-4 shrink-0 transition-colors",
                            isActive ? "text-primary" : "text-muted-foreground/50",
                          )}
                        />
                        {f.titulo}
                      </span>
                      <span
                        className={cn(
                          "mt-0.5 block text-sm transition-colors",
                          isActive ? "text-muted-foreground" : "text-muted-foreground/40",
                        )}
                      >
                        {f.resumen}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>

          <div role="tabpanel" aria-live="polite" aria-label={`Detalle: ${feature.titulo}`}>
            <motion.div
              key={feature.titulo}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
            >
              <p className="min-h-[3.5rem] text-pretty text-muted-foreground lg:min-h-[5.5rem]">
                {feature.texto}
              </p>
              <div className="mt-6">
                <FeatureConsoleDemo query={feature.query} demo={feature.demo} />
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
