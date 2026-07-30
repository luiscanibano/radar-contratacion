import { useState } from "react";
import { Button } from "@/components/ui/button";
import { PricingCard, type PricingPlan } from "@/components/PricingCard";
import { RevealGroup } from "@/components/Reveal";
import { ApiError, SesionCaducadaError, crearCheckout } from "@/lib/api";

const PLANES: (PricingPlan & { slug: string })[] = [
  { slug: "basico", nombre: "Básico", precio: "4,99 €", cuota: "200 preguntas al mes", features: ["Alertas ilimitadas"] },
  {
    slug: "pro",
    nombre: "Pro",
    precio: "14,99 €",
    cuota: "1.000 preguntas al mes",
    destacado: true,
    features: ["Señales estadísticas de riesgo", "Acceso al servidor MCP"],
  },
  { slug: "ilimitado", nombre: "Ilimitado", precio: "29,99 €", cuota: "Sin límite de preguntas", features: ["Soporte prioritario"] },
];

export function PlanUpgrade() {
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState<string | null>(null);

  async function elegir(slug: string) {
    setError("");
    setCargando(slug);
    try {
      const url = await crearCheckout(slug);
      window.location.href = url;
    } catch (err) {
      if (err instanceof SesionCaducadaError) return;
      setError(err instanceof ApiError ? err.message : "Error de red. Inténtalo de nuevo.");
      setCargando(null);
    }
  }

  return (
    <section className="rounded-3xl border border-border bg-card p-6 shadow-sm">
      <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Ampliar plan</h2>
      <RevealGroup className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {PLANES.map((plan) => (
          <PricingCard
            key={plan.slug}
            plan={plan}
            compact
            cta={
              <Button
                type="button"
                onClick={() => elegir(plan.slug)}
                disabled={cargando !== null}
                variant={plan.destacado ? "secondary" : "outline"}
                className="w-full rounded-full"
              >
                {cargando === plan.slug ? "Redirigiendo…" : "Elegir"}
              </Button>
            }
          />
        ))}
      </RevealGroup>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
    </section>
  );
}
