import { useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ApiError, SesionCaducadaError, preguntar } from "@/lib/api";

export function AskAgent() {
  const [pregunta, setPregunta] = useState("");
  const [respuesta, setRespuesta] = useState("");
  const [error, setError] = useState("");
  const [pensando, setPensando] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setRespuesta("");
    setPensando(true);
    try {
      const texto = await preguntar(pregunta);
      setRespuesta(texto);
    } catch (err) {
      if (err instanceof SesionCaducadaError) return;
      setError(err instanceof ApiError ? err.message : "Error de red. Inténtalo de nuevo.");
    } finally {
      setPensando(false);
    }
  }

  return (
    <section className="rounded-3xl border border-border bg-card p-6 shadow-sm">
      <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
        Pregunta al agente
      </h2>
      <form onSubmit={onSubmit} className="mt-4 space-y-3">
        <div className="space-y-1.5">
          <Label htmlFor="pregunta" className="sr-only">
            Tu pregunta
          </Label>
          <textarea
            id="pregunta"
            required
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
            placeholder="p. ej. ¿Cuáles fueron las mayores adjudicaciones de obras en 2024?"
            className="min-h-28 w-full resize-y rounded-xl border border-input bg-background px-3.5 py-2.5 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          />
        </div>
        <Button type="submit" disabled={pensando} className="rounded-full">
          {pensando ? "Pensando…" : "Preguntar"}
        </Button>
      </form>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
      <AnimatePresence>
        {respuesta && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="mt-4 overflow-hidden"
          >
            <div className="whitespace-pre-wrap rounded-2xl border border-white/10 bg-[#0b1220] p-5 font-mono text-[0.84rem] leading-relaxed text-[#e7ecf5]">
              {respuesta}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
