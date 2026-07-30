import { motion } from "framer-motion";
import { CircleCheck, Undo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GradientBlobs } from "@/components/GradientBlobs";

const CONTENIDO = {
  exito: {
    icon: CircleCheck,
    color: "text-success",
    titulo: "Suscripción completada",
    texto:
      "El pago se ha procesado correctamente. Tu nueva cuota estará activa en unos segundos, en cuanto Stripe nos confirme la suscripción.",
  },
  cancelado: {
    icon: Undo2,
    color: "text-muted-foreground",
    titulo: "Pago cancelado",
    texto: "No se ha realizado ningún cargo. Puedes volver al panel y suscribirte cuando quieras. Tu plan actual sigue activo.",
  },
} as const;

export function BillingResult({ variante }: { variante: keyof typeof CONTENIDO }) {
  const { icon: Icon, color, titulo, texto } = CONTENIDO[variante];

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-6">
      <GradientBlobs />
      <motion.div
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md rounded-3xl border border-border bg-card/90 p-8 text-center shadow-xl shadow-black/5 backdrop-blur-sm"
      >
        <motion.div
          initial={{ scale: 0, rotate: -20 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 260, damping: 18, delay: 0.15 }}
          className="mx-auto mb-4 inline-flex"
        >
          <Icon className={`size-11 ${color}`} strokeWidth={1.5} aria-hidden="true" />
        </motion.div>
        <h1 className="text-xl font-semibold tracking-tight">{titulo}</h1>
        <p className="mt-2 text-pretty text-muted-foreground">{texto}</p>
        <Button asChild className="mt-6 rounded-full">
          <a href="/app">Volver al panel</a>
        </Button>
      </motion.div>
    </div>
  );
}
