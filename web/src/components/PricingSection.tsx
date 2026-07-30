import { useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import { Button } from "@/components/ui/button";
import type { PricingPlan } from "@/components/PricingCard";
import { PricingGlassCard } from "@/components/ui/pricing-glass-card";
import { RadialBackground } from "@/components/ui/radial-background";
import { VerticalCutReveal } from "@/components/ui/vertical-cut-reveal";

gsap.registerPlugin(ScrollTrigger);

const PLANES: (PricingPlan & { slug: string })[] = [
  {
    slug: "gratis",
    nombre: "Gratis",
    precio: "0 €",
    cuota: "10 preguntas al mes",
    features: ["Agente de preguntas en castellano", "1 alerta por email"],
  },
  {
    slug: "basico",
    nombre: "Básico",
    precio: "4,99 €",
    cuota: "200 preguntas al mes",
    features: ["Todo lo de Gratis", "Alertas ilimitadas"],
  },
  {
    slug: "pro",
    nombre: "Pro",
    precio: "14,99 €",
    cuota: "1.000 preguntas al mes",
    destacado: true,
    features: ["Todo lo de Básico", "Señales estadísticas de riesgo", "Acceso al servidor MCP"],
  },
  {
    slug: "ilimitado",
    nombre: "Ilimitado",
    precio: "29,99 €",
    cuota: "Sin límite de preguntas",
    features: ["Todo lo de Pro", "Sin límite de preguntas", "Soporte prioritario"],
  },
];

export function PricingSection() {
  const [headingRevealed, setHeadingRevealed] = useState(false);
  const headingRef = useRef<HTMLDivElement>(null);

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

  return (
    <section id="precios" className="relative flex min-h-screen flex-col justify-center overflow-hidden py-20 md:py-28">
      <RadialBackground />
      <div aria-hidden className="pointer-events-none absolute inset-x-0 bottom-0 -z-10 h-48 bg-gradient-to-b from-transparent to-background" />
      <div className="mx-auto max-w-7xl px-6">
        <div ref={headingRef} className="mb-12 max-w-3xl lg:mb-16">
          <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Precios</p>
          <h2 className="mt-3 text-3xl font-medium leading-[1.05] tracking-tight text-foreground md:text-4xl lg:text-5xl xl:text-6xl">
            <VerticalCutReveal
              splitBy="words"
              staggerDuration={0.06}
              staggerFrom="first"
              autoStart={headingRevealed}
              transition={{ type: "spring", stiffness: 200, damping: 24 }}
              wordLevelClassName="pb-[0.2em]"
            >
              {"Empieza gratis. Crece si lo"}
            </VerticalCutReveal>{" "}
            <VerticalCutReveal
              splitBy="words"
              staggerDuration={0.06}
              staggerFrom="first"
              autoStart={headingRevealed}
              transition={{ type: "spring", stiffness: 200, damping: 24, delay: 0.3 }}
              elementLevelClassName="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent"
              wordLevelClassName="pb-[0.2em]"
            >
              {"necesitas."}
            </VerticalCutReveal>
          </h2>
          <p className="mt-4 text-pretty text-lg text-muted-foreground md:text-xl">
            Sin permanencia ni letra pequeña: cambia o cancela tu plan cuando quieras desde tu cuenta.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {PLANES.map((plan) => (
            <PricingGlassCard
              key={plan.nombre}
              plan={plan}
              cta={
                <Button
                  asChild
                  className="w-full rounded-full"
                  variant={plan.destacado ? "secondary" : "outline"}
                  size="lg"
                >
                  <a href={plan.slug === "gratis" ? "/app#registro" : `/app?plan=${plan.slug}`}>
                    {plan.slug === "gratis" ? "Crear cuenta gratis" : "Suscribirse"}
                  </a>
                </Button>
              }
            />
          ))}
        </div>
      </div>
    </section>
  );
}
