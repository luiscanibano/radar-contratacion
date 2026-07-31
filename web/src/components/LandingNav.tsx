import { motion, useMotionValueEvent, useScroll } from "framer-motion";
import { useState } from "react";
import { Brand } from "@/components/Brand";
import { Button } from "@/components/ui/button";

export function LandingNav() {
  const { scrollY } = useScroll();
  const [visible, setVisible] = useState(false);
  useMotionValueEvent(scrollY, "change", (y) => setVisible(y > 24));

  return (
    <motion.header
      initial={false}
      animate={visible ? { y: 0, opacity: 1 } : { y: -32, opacity: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      style={{ pointerEvents: visible ? "auto" : "none" }}
      className="fixed inset-x-0 top-4 z-50 flex justify-center px-4"
    >
      <nav className="flex w-full max-w-4xl items-center justify-between gap-4 rounded-full border border-border/60 bg-background/70 px-4 py-2 shadow-lg shadow-black/5 backdrop-blur-xl">
        <Brand iconOnly />
        <div className="flex items-center gap-1">
          <Button asChild variant="ghost" size="sm" className="rounded-full text-muted-foreground">
            <a href="#precios">Precios</a>
          </Button>
          <Button asChild variant="ghost" size="sm" className="rounded-full text-muted-foreground">
            <a href="/docs">API</a>
          </Button>
        </div>
        <div className="flex items-center gap-1">
          <Button asChild size="sm" className="rounded-full">
            <a href="/app">Entrar</a>
          </Button>
        </div>
      </nav>
    </motion.header>
  );
}
