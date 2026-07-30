import { useEffect, useMemo, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { MoveRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AuroraBackground } from "@/components/ui/aurora-background";

const ROTATING_WORDS = ["preguntable", "auditable", "verificable", "instantánea"];

export function Hero() {
  const [wordIndex, setWordIndex] = useState(0);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) return;
    const timeoutId = setTimeout(() => {
      setWordIndex((current) => (current + 1) % ROTATING_WORDS.length);
    }, 2200);
    return () => clearTimeout(timeoutId);
  }, [wordIndex, reduced]);

  const activeWord = useMemo(
    () => (reduced ? ROTATING_WORDS[0] : ROTATING_WORDS[wordIndex]),
    [reduced, wordIndex]
  );

  return (
    <AuroraBackground className="min-h-screen">
      <div className="relative mx-auto flex max-w-4xl flex-col items-center gap-10 px-6 text-center">
        <h1 className="text-balance text-5xl font-bold leading-[1.08] tracking-tight text-foreground sm:text-6xl lg:text-7xl">
          <span className="block">La contratación pública,</span>
          <span className="relative mt-1 flex h-[1.2em] w-full items-center justify-center overflow-hidden">
            {ROTATING_WORDS.map((word, index) => (
              <motion.span
                key={word}
                className="absolute inset-x-0 flex justify-center bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent"
                initial={{ opacity: 0, y: reduced ? 0 : "100%" }}
                animate={
                  word === activeWord
                    ? { y: 0, opacity: 1 }
                    : { y: reduced ? 0 : index < wordIndex ? "-100%" : "100%", opacity: 0 }
                }
                transition={{ type: "spring", stiffness: 60, damping: 14 }}
              >
                {word}
              </motion.span>
            ))}
          </span>
        </h1>

        <p className="max-w-[50ch] text-pretty text-xl text-muted-foreground">
          Licitaciones y adjudicaciones del sector público español, listas para responder en
          castellano con cifras verificables. Sin SQL, sin ficheros de 2&nbsp;GB.
        </p>

        <div className="flex flex-wrap justify-center gap-3">
          <Button asChild size="lg" className="h-12 gap-2 rounded-full px-7 text-base">
            <a href="/app#registro">
              Crear cuenta gratis <MoveRight className="size-4" />
            </a>
          </Button>
          <Button asChild size="lg" variant="outline" className="h-12 rounded-full px-7 text-base">
            <a href="#precios">Ver precios</a>
          </Button>
        </div>

        <p className="font-mono text-xs text-muted-foreground">
          fuente: datos abiertos oficiales de la Plataforma de Contratación del Sector Público
        </p>
      </div>
    </AuroraBackground>
  );
}
