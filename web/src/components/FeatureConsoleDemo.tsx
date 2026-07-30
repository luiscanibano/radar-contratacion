import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ConsolePanel } from "@/components/ConsolePanel";
import { cn } from "@/lib/utils";

function WindowChrome({ ruta }: { ruta: string }) {
  return (
    <div className="mb-4 flex items-center gap-3 border-b border-border pb-3 dark:border-white/10">
      <span className="flex shrink-0 gap-1.5">
        <span className="size-2.5 rounded-full bg-[#ff5f57]" />
        <span className="size-2.5 rounded-full bg-[#febc2e]" />
        <span className="size-2.5 rounded-full bg-[#28c840]" />
      </span>
      <span className="min-w-0 flex-1 truncate rounded-md bg-muted px-2.5 py-1 text-center text-[0.7rem] text-muted-foreground dark:bg-white/5 dark:text-slate-400">
        {ruta}
      </span>
      <span className="hidden shrink-0 text-[0.68rem] text-muted-foreground/70 sm:inline dark:text-slate-500">
        datos ilustrativos
      </span>
    </div>
  );
}

interface TableDemo {
  kind: "table";
  nota: string;
  filas: { entidad: string; contratos: string; importe: string }[];
}

interface LogLine {
  tiempo?: string;
  texto: string;
  tono?: "default" | "accent" | "success";
}

interface LogDemo {
  kind: "log";
  nota: string;
  lineas: LogLine[];
}

export type FeatureDemo = TableDemo | LogDemo;

const DOT_TONE: Record<NonNullable<LogLine["tono"]>, string> = {
  default: "bg-muted-foreground",
  accent: "bg-accent",
  success: "bg-success",
};

const TEXT_TONE: Record<NonNullable<LogLine["tono"]>, string> = {
  default: "text-foreground dark:text-[#e7ecf5]",
  accent: "text-accent",
  success: "text-foreground dark:text-[#e7ecf5]",
};

export function FeatureConsoleDemo({ query, demo }: { query: string; demo: FeatureDemo }) {
  const reduced = useReducedMotion();
  const [texto, setTexto] = useState(reduced ? query : "");
  const [terminado, setTerminado] = useState(!!reduced);

  useEffect(() => {
    setTexto(reduced ? query : "");
    setTerminado(!!reduced);
    if (reduced) return;
    let i = 0;
    let vivo = true;
    const inicio = setTimeout(function teclear() {
      if (!vivo) return;
      i += 1;
      setTexto(query.slice(0, i));
      if (i < query.length) {
        setTimeout(teclear, 22);
      } else {
        setTerminado(true);
      }
    }, 300);
    return () => {
      vivo = false;
      clearTimeout(inicio);
    };
  }, [query, reduced]);

  return (
    <ConsolePanel glow className="relative min-w-0">
      <WindowChrome ruta="radarcontratacion.com/preguntar" />
      <p className="min-h-[3em] font-medium text-foreground dark:text-white">
        <span className="text-muted-foreground dark:text-slate-400">{"› "}</span>
        {texto}
        {!terminado && (
          <span
            aria-hidden="true"
            className="ml-px inline-block h-[1.1em] w-[0.55em] translate-y-[0.15em] animate-pulse bg-foreground align-text-bottom dark:bg-white"
          />
        )}
      </p>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: terminado ? 1 : 0 }}
        transition={{ duration: 0.3 }}
        aria-hidden={!terminado}
      >
        {demo.kind === "table" && (
          <>
            <p className="mb-4 mt-2 text-[0.78rem] text-muted-foreground dark:text-slate-400">{demo.nota}</p>
            <table className="w-full border-collapse">
              <tbody>
                {demo.filas.map((fila, i) => (
                  <motion.tr
                    key={fila.entidad}
                    initial={{ opacity: 0, y: 6 }}
                    animate={terminado ? { opacity: 1, y: 0 } : { opacity: 0, y: 6 }}
                    transition={{ duration: 0.4, delay: reduced ? 0 : i * 0.09 }}
                    className="border-t border-border dark:border-white/10"
                  >
                    <td className="py-1 pr-4">{fila.entidad}</td>
                    <td className="py-1 text-right tabular-nums whitespace-nowrap">{fila.contratos}</td>
                    <td className="py-1 pl-4 text-right tabular-nums whitespace-nowrap">{fila.importe}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {demo.kind === "log" && (
          <>
            <p className="mb-3 mt-2 text-[0.78rem] text-muted-foreground dark:text-slate-400">{demo.nota}</p>
            <ul className="space-y-2">
              {demo.lineas.map((linea, i) => {
                const tono = linea.tono ?? "default";
                return (
                  <motion.li
                    key={linea.texto}
                    initial={{ opacity: 0, x: -6 }}
                    animate={terminado ? { opacity: 1, x: 0 } : { opacity: 0, x: -6 }}
                    transition={{ duration: 0.35, delay: reduced ? 0 : i * 0.14 }}
                    className="flex items-baseline gap-2.5 text-[0.82rem]"
                  >
                    <span className={cn("inline-block size-1.5 shrink-0 rounded-full", DOT_TONE[tono])} />
                    {linea.tiempo && (
                      <span className="shrink-0 tabular-nums text-muted-foreground dark:text-slate-500">
                        {linea.tiempo}
                      </span>
                    )}
                    <span className={TEXT_TONE[tono]}>{linea.texto}</span>
                  </motion.li>
                );
              })}
            </ul>
          </>
        )}
      </motion.div>
    </ConsolePanel>
  );
}
