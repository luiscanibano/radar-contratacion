import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function ConsolePanel({
  children,
  className,
  glow = false,
}: {
  children: ReactNode;
  className?: string;
  glow?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-card p-6 font-mono text-[0.84rem] leading-relaxed text-foreground",
        "dark:border-white/10 dark:bg-[#0b1220] dark:text-[#e7ecf5]",
        glow && "shadow-glow",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function ConsoleMembrete({ left, right }: { left: ReactNode; right: ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-4 border-b border-border pb-3 text-[0.72rem] text-muted-foreground dark:border-white/10 dark:text-slate-400">
      <span>{left}</span>
      <span>{right}</span>
    </div>
  );
}
