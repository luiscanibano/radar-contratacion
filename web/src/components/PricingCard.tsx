import type { ReactNode } from "react";
import { Check } from "lucide-react";
import { motion } from "framer-motion";
import { RevealItem } from "@/components/Reveal";
import { cn } from "@/lib/utils";

export interface PricingPlan {
  nombre: string;
  precio: string;
  cuota: string;
  features: string[];
  destacado?: boolean;
}

export function PricingCard({ plan, cta, compact = false }: { plan: PricingPlan; cta: ReactNode; compact?: boolean }) {
  return (
    <RevealItem className="h-full">
      <motion.div
        whileHover={{ y: -4 }}
        transition={{ type: "spring", stiffness: 300, damping: 24 }}
        className={cn(
          "relative flex h-full flex-col rounded-3xl border p-6",
          plan.destacado
            ? "border-transparent bg-gradient-to-b from-primary to-primary/80 text-primary-foreground shadow-xl shadow-primary/25"
            : "border-border bg-card",
          compact && "p-5",
        )}
      >
        {plan.destacado && (
          <span className="absolute -top-3 left-6 rounded-full bg-accent px-3 py-1 text-xs font-semibold text-accent-foreground shadow-sm">
            Más elegido
          </span>
        )}
        <p className={cn("font-semibold", plan.destacado ? "text-primary-foreground" : "text-foreground")}>
          {plan.nombre}
        </p>
        <p className="mt-3 font-mono text-2xl font-semibold tabular-nums">
          {plan.precio}
          <span
            className={cn(
              "ml-1 text-sm font-normal",
              plan.destacado ? "text-primary-foreground/75" : "text-muted-foreground",
            )}
          >
            /mes
          </span>
        </p>
        <p className={cn("mt-1 text-sm", plan.destacado ? "text-primary-foreground/80" : "text-muted-foreground")}>
          {plan.cuota}
        </p>
        <ul className="mt-5 flex-1 space-y-2.5">
          {plan.features.map((feature) => (
            <li key={feature} className="flex items-start gap-2 text-sm">
              <Check
                className={cn(
                  "mt-0.5 size-4 shrink-0",
                  plan.destacado ? "text-primary-foreground" : "text-primary",
                )}
              />
              <span className={plan.destacado ? "text-primary-foreground/90" : "text-muted-foreground"}>
                {feature}
              </span>
            </li>
          ))}
        </ul>
        <div className="mt-6">{cta}</div>
      </motion.div>
    </RevealItem>
  );
}
