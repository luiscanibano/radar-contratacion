import { motion, useMotionValueEvent, useScroll } from "framer-motion";
import { useState } from "react";
import { Brand } from "@/components/Brand";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";

export function LandingNav() {
  const { scrollY } = useScroll();
  const [scrolled, setScrolled] = useState(false);
  useMotionValueEvent(scrollY, "change", (y) => setScrolled(y > 24));

  return (
    <motion.header
      initial={{ y: -32, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="fixed inset-x-0 top-4 z-50 flex justify-center px-4"
    >
      <nav
        className={`flex w-full max-w-4xl items-center justify-between gap-4 rounded-full border px-4 py-2 transition-all duration-300 ${
          scrolled
            ? "border-border/60 bg-background/70 shadow-lg shadow-black/5 backdrop-blur-xl"
            : "border-transparent bg-background/0"
        }`}
      >
        <Brand compact />
        <div className="flex items-center gap-1">
          <Button asChild variant="ghost" size="sm" className="rounded-full text-muted-foreground">
            <a href="#precios">Precios</a>
          </Button>
          <Button asChild variant="ghost" size="sm" className="rounded-full text-muted-foreground">
            <a href="/docs">API</a>
          </Button>
        </div>
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <Button asChild size="sm" className="rounded-full">
            <a href="/app">Entrar</a>
          </Button>
        </div>
      </nav>
    </motion.header>
  );
}
