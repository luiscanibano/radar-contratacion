import { lazy, Suspense } from "react";
import { useReducedMotion } from "framer-motion";

const ShaderScene = lazy(() => import("@/components/ShaderScene"));

/** Static, non-animated stand-in for prefers-reduced-motion — same brand
 * colors as the shader, just frozen (no canvas, no render loop), matching
 * the rest of the system's rule that reduced motion shows the final state
 * instead of nothing. */
function StaticFallback() {
  return (
    <div
      className="absolute inset-0"
      style={{
        background:
          "radial-gradient(60% 55% at 28% 35%, color-mix(in oklab, var(--primary) 45%, transparent), transparent 70%)," +
          "radial-gradient(55% 50% at 75% 55%, color-mix(in oklab, var(--accent) 40%, transparent), transparent 70%)",
      }}
    />
  );
}

/** WebGL shader background for the hero. Code-split (three/@react-three/fiber
 * are heavy) so it never blocks first paint of the hero text/CTAs. Under
 * prefers-reduced-motion it swaps to a static gradient (same colors, frozen)
 * instead of disappearing — the render loop is the only thing being skipped. */
export function ShaderBackground() {
  const reduced = useReducedMotion();

  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      {reduced ? (
        <StaticFallback />
      ) : (
        <Suspense fallback={<StaticFallback />}>
          <ShaderScene />
        </Suspense>
      )}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent from-75% to-background" />
    </div>
  );
}
