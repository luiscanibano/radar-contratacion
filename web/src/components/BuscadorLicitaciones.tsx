import { useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  ApiError,
  SesionCaducadaError,
  buscarLicitaciones,
  type ResultadoBusqueda,
} from "@/lib/api";

const formatoEuros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });

export function BuscadorLicitaciones() {
  const [q, setQ] = useState("");
  const [resultados, setResultados] = useState<ResultadoBusqueda[] | null>(null);
  const [error, setError] = useState("");
  const [buscando, setBuscando] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBuscando(true);
    try {
      setResultados(await buscarLicitaciones(q));
    } catch (err) {
      if (err instanceof SesionCaducadaError) return;
      setError(err instanceof ApiError ? err.message : "Error de red. Inténtalo de nuevo.");
    } finally {
      setBuscando(false);
    }
  }

  return (
    <section className="rounded-3xl border border-border bg-card p-6 shadow-sm">
      <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
        Buscar licitaciones
      </h2>
      <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-3 sm:flex-row">
        <div className="flex-1 space-y-1.5">
          <Label htmlFor="buscar-q" className="sr-only">
            Qué buscar
          </Label>
          <Input
            id="buscar-q"
            required
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="p. ej. obras de accesibilidad en Castilla y León"
          />
        </div>
        <Button type="submit" disabled={buscando} className="rounded-full sm:self-start">
          {buscando ? "Buscando…" : "Buscar"}
        </Button>
      </form>
      <p className="mt-2 text-xs text-muted-foreground">
        La primera búsqueda puede tardar unos segundos mientras se carga el modelo.
      </p>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}

      <AnimatePresence initial={false}>
        {resultados && (
          <motion.ul
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="mt-4 overflow-hidden"
          >
            {resultados.length === 0 && (
              <li className="py-2.5 text-sm text-muted-foreground">
                Sin resultados para esa búsqueda.
              </li>
            )}
            {resultados.map((r, i) => (
              <li key={r.entry_id}>
                {i > 0 && <Separator className="mb-3" />}
                <div className={`space-y-1.5 ${i > 0 ? "" : "pb-3"}`}>
                  <p className="text-sm font-medium">{r.objeto ?? "Sin objeto descrito"}</p>
                  <p className="text-sm text-muted-foreground">
                    {r.organo ?? "Órgano no disponible"}
                  </p>
                  <div className="flex flex-wrap items-center gap-2">
                    {r.expediente && <Badge variant="outline">{r.expediente}</Badge>}
                    {r.anio && <Badge variant="outline">{r.anio}</Badge>}
                    {r.presupuesto != null && (
                      <span className="font-mono text-xs text-muted-foreground">
                        {formatoEuros.format(r.presupuesto)}
                      </span>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </section>
  );
}
