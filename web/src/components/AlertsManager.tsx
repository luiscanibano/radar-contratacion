import { useEffect, useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ApiError,
  SesionCaducadaError,
  borrarAlerta,
  crearAlerta,
  listarAlertas,
  type Alerta,
} from "@/lib/api";

export function AlertsManager() {
  const [alertas, setAlertas] = useState<Alerta[] | null>(null);
  const [texto, setTexto] = useState("");
  const [error, setError] = useState("");

  async function cargar() {
    try {
      setAlertas(await listarAlertas());
    } catch (err) {
      if (err instanceof SesionCaducadaError) return;
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar las alertas.");
    }
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await crearAlerta(texto);
      setTexto("");
      cargar();
    } catch (err) {
      if (err instanceof SesionCaducadaError) return;
      setError(err instanceof ApiError ? err.message : "No se pudo crear la alerta.");
    }
  }

  async function onBorrar(id: number) {
    try {
      await borrarAlerta(id);
      cargar();
    } catch (err) {
      if (err instanceof SesionCaducadaError) return;
      setError(err instanceof ApiError ? err.message : "No se pudo borrar la alerta.");
    }
  }

  return (
    <section className="rounded-3xl border border-border bg-card p-6 shadow-sm">
      <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
        Alertas por email
      </h2>
      <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-3 sm:flex-row">
        <div className="flex-1 space-y-1.5">
          <Label htmlFor="alerta-texto" className="sr-only">
            Búsqueda a vigilar
          </Label>
          <Input
            id="alerta-texto"
            required
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="p. ej. obras de accesibilidad en Castilla y León"
          />
        </div>
        <Button type="submit" variant="outline" className="rounded-full sm:self-start">
          Crear alerta
        </Button>
      </form>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}

      <ul className="mt-4 divide-y divide-border">
        {alertas?.length === 0 && (
          <li className="py-2.5 text-sm text-muted-foreground">
            Sin alertas todavía. Crea la primera con el formulario de arriba.
          </li>
        )}
        <AnimatePresence initial={false}>
          {alertas?.map((alerta) => (
            <motion.li
              key={alerta.id}
              layout
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="flex items-center justify-between gap-4 py-2.5"
            >
              <span className="font-mono text-sm">{alerta.consulta_texto}</span>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label="Borrar alerta"
                onClick={() => onBorrar(alerta.id)}
                className="shrink-0 text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="size-4" />
              </Button>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </section>
  );
}
