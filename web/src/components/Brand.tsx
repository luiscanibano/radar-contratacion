import { Radar } from "lucide-react";
import { cn } from "@/lib/utils";

export function Brand({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <a
      href="/"
      className={cn("group inline-flex items-center gap-2 text-foreground no-underline", className)}
    >
      <span className="grid size-8 place-items-center rounded-xl bg-gradient-to-br from-primary to-accent text-primary-foreground shadow-sm">
        <Radar className="size-4.5" strokeWidth={2} />
      </span>
      <span className="font-semibold tracking-tight">
        {compact ? "Radar CP" : "Radar de Contratación Pública"}
      </span>
    </a>
  );
}
