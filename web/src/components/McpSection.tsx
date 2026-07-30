import { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import { Check, Copy } from "lucide-react";
import { Reveal } from "@/components/Reveal";
import { AuroraBackground } from "@/components/ui/aurora-background";
import { GradientWordReveal } from "@/components/ui/gradient-word-reveal";

gsap.registerPlugin(ScrollTrigger);

const CONFIG = `{
  "mcpServers": {
    "radar-contratacion": {
      "type": "http",
      "url": "https://radarcontratacion.com/mcp",
      "headers": { "Authorization": "Bearer <tu-token-JWT>" }
    }
  }
}`;

export function McpSection() {
  const [copiado, setCopiado] = useState(false);
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

  async function copiar() {
    try {
      await navigator.clipboard.writeText(CONFIG);
    } catch {
      return;
    }
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  }

  return (
    <AuroraBackground className="py-20">
      <div className="relative mx-auto w-full max-w-6xl px-6">
        <div ref={headingRef} className="mb-10 max-w-3xl">
          <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Para desarrolladores
          </p>
          <h2 className="mt-3 text-4xl font-medium leading-tight tracking-tight sm:text-5xl lg:text-6xl">
            <GradientWordReveal
              words={["El mismo agente.", "En tu terminal."]}
              revealed={headingRevealed}
              staggerDelay={0.15}
            />
          </h2>
          <p className="mt-3 text-pretty text-lg text-muted-foreground md:text-xl">
            Conecta Claude, u otro cliente MCP, directamente a los datos: las mismas herramientas del
            agente, desde tu propio asistente. También hay{" "}
            <a href="/docs" className="text-primary underline-offset-4 hover:underline">
              API REST documentada
            </a>
            .
          </p>
        </div>
        <Reveal>
          <div className="relative overflow-hidden rounded-2xl border border-border bg-white shadow-[0_30px_60px_-20px_rgba(30,64,175,0.4)] dark:border-white/10 dark:bg-[#0b1220]">
            <button
              type="button"
              onClick={copiar}
              aria-label="Copiar la configuración MCP"
              className="absolute right-4 top-4 inline-flex items-center gap-1.5 rounded-full border border-black/10 bg-black/5 px-3 py-1.5 font-mono text-xs text-slate-600 transition-colors hover:text-slate-900 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:text-white"
            >
              <AnimatePresence mode="wait" initial={false}>
                <motion.span
                  key={copiado ? "copiado" : "copiar"}
                  initial={{ opacity: 0, filter: "blur(2px)" }}
                  animate={{ opacity: 1, filter: "blur(0px)" }}
                  exit={{ opacity: 0, filter: "blur(2px)" }}
                  transition={{ duration: 0.18 }}
                  className="inline-flex items-center gap-1.5"
                >
                  {copiado ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
                  {copiado ? "copiado" : "copiar"}
                </motion.span>
              </AnimatePresence>
            </button>
            <pre className="overflow-x-auto p-6 font-mono text-[0.82rem] leading-relaxed text-slate-800 dark:text-[#e7ecf5]">
              <code>{CONFIG}</code>
            </pre>
          </div>
        </Reveal>
      </div>
    </AuroraBackground>
  );
}
