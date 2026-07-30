import type { MouseEvent, ReactNode } from "react";
import { Check } from "lucide-react";
import { motion, useMotionTemplate, useMotionValue, type Variants } from "framer-motion";
import type { PricingPlan } from "@/components/PricingCard";
import { cn } from "@/lib/utils";

const NOISE_PATTERN =
  'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")';

const cardVariant: Variants = {
  hidden: { opacity: 0, y: 60, scale: 0.95 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring", stiffness: 300, damping: 24, staggerChildren: 0.1, delayChildren: 0.15 },
  },
};

const itemVariant: Variants = {
  hidden: { opacity: 0, y: 20, scale: 0.8 },
  show: { opacity: 1, y: 0, scale: 1, transition: { type: "spring", stiffness: 350, damping: 25 } },
};

export function PricingGlassCard({ plan, cta }: { plan: PricingPlan; cta: ReactNode }) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: MouseEvent<HTMLDivElement>) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  return (
    <motion.div
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.3 }}
      variants={cardVariant}
      className="h-full"
    >
      <div
        onMouseMove={handleMouseMove}
        className={cn(
          "group relative flex h-full flex-col overflow-hidden rounded-[28px] border p-7 backdrop-blur-2xl backdrop-saturate-150 transition-transform duration-500 md:p-9",
          "bg-[color-mix(in_oklab,var(--card)_45%,transparent)]",
          plan.destacado
            ? "border-[color-mix(in_oklab,var(--foreground)_18%,transparent)] shadow-[0_32px_64px_-16px_color-mix(in_oklab,var(--primary)_45%,transparent),inset_0_1px_1px_color-mix(in_oklab,var(--foreground)_15%,transparent)] md:-translate-y-4"
            : "border-[color-mix(in_oklab,var(--foreground)_10%,transparent)] shadow-[0_20px_40px_-18px_rgba(15,23,42,0.25)]",
        )}
      >
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-0 rounded-[28px] opacity-0 transition-opacity duration-500 group-hover:opacity-100"
          style={{
            background: useMotionTemplate`radial-gradient(500px at ${mouseX}px ${mouseY}px, color-mix(in oklab, var(--foreground) 10%, transparent), transparent)`,
          }}
        />

        {plan.destacado && (
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 z-0 rounded-[28px] p-px"
            style={{
              WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
              WebkitMaskComposite: "xor",
              maskComposite: "exclude",
            }}
          >
            <div
              className="absolute -inset-full animate-[spin_5s_linear_infinite]"
              style={{
                background:
                  "conic-gradient(from 0deg, transparent 70%, color-mix(in oklab, var(--primary) 80%, transparent) 100%)",
              }}
            />
          </div>
        )}

        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-0 opacity-[0.035] mix-blend-overlay"
          style={{ backgroundImage: NOISE_PATTERN }}
        />

        {plan.destacado && (
          <span className="absolute left-1/2 top-0 -translate-x-1/2 rounded-b-xl border-x border-b border-[color-mix(in_oklab,var(--foreground)_10%,transparent)] bg-[color-mix(in_oklab,var(--foreground)_8%,transparent)] px-4 py-1 text-xs font-medium text-foreground/90 backdrop-blur-md">
            Más elegido
          </span>
        )}

        <motion.div
          className="relative z-10 flex h-full flex-col"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.4 }}
          variants={{ hidden: {}, show: { transition: { staggerChildren: 0.07, delayChildren: 0.1 } } }}
        >
          <motion.p variants={itemVariant} className="text-xl font-semibold tracking-wide text-foreground/80">
            {plan.nombre}
          </motion.p>

          <motion.div variants={itemVariant} className="mt-5 flex items-baseline gap-1">
            <span className="whitespace-nowrap text-[38px] font-bold leading-none tracking-tight text-foreground md:text-[44px]">
              {plan.precio}
            </span>
            <span className="ml-1 shrink-0 text-base font-medium text-muted-foreground">/mes</span>
          </motion.div>

          <motion.p variants={itemVariant} className="mt-2 min-h-[2.5rem] text-base leading-relaxed text-muted-foreground">
            {plan.cuota}
          </motion.p>

          <motion.div variants={itemVariant} className="my-7 h-px w-full bg-[color-mix(in_oklab,var(--foreground)_10%,transparent)]" />

          <ul className="flex flex-1 flex-col gap-4">
            {plan.features.map((feature) => (
              <motion.li key={feature} variants={itemVariant} className="flex items-start gap-3">
                <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full border border-[color-mix(in_oklab,var(--primary)_25%,transparent)] bg-[color-mix(in_oklab,var(--primary)_12%,transparent)]">
                  <Check className="size-3.5 text-primary" strokeWidth={3} />
                </span>
                <span className="text-base font-medium leading-tight text-foreground/70">{feature}</span>
              </motion.li>
            ))}
          </ul>

          <motion.div variants={itemVariant} className="mt-6">
            {cta}
          </motion.div>
        </motion.div>
      </div>
    </motion.div>
  );
}
