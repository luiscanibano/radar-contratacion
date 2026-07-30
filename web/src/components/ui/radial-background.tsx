import { cn } from "@/lib/utils";

interface RadialBackgroundProps {
  className?: string;
}

export function RadialBackground({ className }: RadialBackgroundProps) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 -z-10 size-full",
        "[background:radial-gradient(125%_125%_at_50%_0%,var(--background)_40%,var(--aurora-blue-500)_100%)]",
        className,
      )}
    />
  );
}
