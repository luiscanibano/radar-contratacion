import { useId } from "react";
import { cn } from "@/lib/utils";

// Marca propia: escudo (supervisión, confianza institucional) con ondas de
// señal emanando de un punto (vigilancia, detección) — "Vigila. Detecta."
// resuelto como icono, sin recurrir a un radar-plato genérico.
function RadarShieldMark({ className }: { className?: string }) {
  const uid = useId().replace(/:/g, "");
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <defs>
        <linearGradient id={`shield-${uid}`} x1="4" y1="3" x2="20" y2="21" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#1e40af" />
          <stop offset="1" stopColor="#0f172a" />
        </linearGradient>
      </defs>
      <path
        d="M12 3c-3.05 1.72-5.4 2.32-9 2.62.31 6.85 3.35 11.12 9 13.13 5.65-2.01 8.69-6.28 9-13.13-3.6-.3-5.95-.9-9-2.62Z"
        fill={`url(#shield-${uid})`}
      />
      <path d="M9.8 14.5a3.14 3.14 0 0 1 4.4 0" fill="none" stroke="white" strokeWidth="1.3" strokeLinecap="round" opacity="0.95" />
      <path d="M7.9 14.5a5.86 5.86 0 0 1 8.2 0" fill="none" stroke="white" strokeWidth="1.3" strokeLinecap="round" opacity="0.6" />
      <path d="M6.3 14.5a8.14 8.14 0 0 1 11.4 0" fill="none" stroke="white" strokeWidth="1.3" strokeLinecap="round" opacity="0.3" />
      <circle cx="12" cy="14.5" r="1.35" fill="white" />
      <circle cx="15.4" cy="8.3" r="0.9" fill="white" opacity="0.85" />
    </svg>
  );
}

export function Brand({
  className,
  compact = false,
  iconOnly = false,
  size = "md",
}: {
  className?: string;
  compact?: boolean;
  iconOnly?: boolean;
  size?: "md" | "lg";
}) {
  return (
    <a
      href="/"
      className={cn("group inline-flex items-center gap-2 text-foreground no-underline", className)}
      aria-label={iconOnly ? "Radar de Contratación Pública — inicio" : undefined}
    >
      <RadarShieldMark className={size === "lg" ? "size-9" : "size-7"} />
      {!iconOnly && (
        <span className="font-semibold tracking-tight">
          {compact ? "Radar CP" : "Radar de Contratación Pública"}
        </span>
      )}
    </a>
  );
}
