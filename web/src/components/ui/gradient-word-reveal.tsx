import { motion, useReducedMotion, type Variants } from "framer-motion";
import { cn } from "@/lib/utils";

interface GradientWordRevealProps {
  words: string[];
  className?: string;
  /** Cuando es false, las palabras se mantienen ocultas hasta que pase a true (disparado externamente, p. ej. por un ScrollTrigger de GSAP). */
  revealed?: boolean;
  /** Segundos de retraso entre la aparición de cada palabra sucesiva. */
  staggerDelay?: number;
}

export function GradientWordReveal({
  words,
  className,
  revealed = true,
  staggerDelay = 1,
}: GradientWordRevealProps) {
  const reduced = useReducedMotion();

  const variants: Variants = {
    hidden: { y: reduced ? 0 : "100%", opacity: reduced ? 1 : 0 },
    show: { y: 0, opacity: 1 },
  };

  return (
    <span className={cn("inline-flex flex-wrap", className)}>
      {words.map((word, i) => (
        <span key={word} className="mr-[0.28em] inline-block overflow-hidden py-[0.08em] last:mr-0">
          <motion.span
            className="inline-block bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent"
            variants={variants}
            initial="hidden"
            animate={reduced || revealed ? "show" : "hidden"}
            transition={{ type: "spring", stiffness: 60, damping: 14, delay: reduced ? 0 : i * staggerDelay }}
          >
            {word}
          </motion.span>
        </span>
      ))}
    </span>
  );
}
