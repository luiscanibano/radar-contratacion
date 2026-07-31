import { motion, useReducedMotion } from "framer-motion";

/** Ambient background depth for the hero: two soft blurred blobs drifting
 * slowly. Purely decorative (aria-hidden), frozen under reduced-motion. */
export function GradientBlobs() {
  const reduced = useReducedMotion();

  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <motion.div
        className="absolute -left-32 -top-32 size-[36rem] rounded-full bg-primary/25 blur-[110px]"
        animate={reduced ? undefined : { x: [0, 40, -20, 0], y: [0, 30, -10, 0] }}
        transition={{ duration: 26, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -right-40 top-10 size-[30rem] rounded-full bg-accent/20 blur-[110px]"
        animate={reduced ? undefined : { x: [0, -30, 20, 0], y: [0, -20, 20, 0] }}
        transition={{ duration: 30, repeat: Infinity, ease: "easeInOut", delay: 2 }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/40 to-background" />
    </div>
  );
}
