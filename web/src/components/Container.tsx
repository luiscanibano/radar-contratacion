import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Container({ children, className, size = "default" }: { children: ReactNode; className?: string; size?: "default" | "narrow" | "tight" }) {
  return (
    <div
      className={cn(
        "mx-auto w-full px-6",
        size === "default" && "max-w-6xl",
        size === "narrow" && "max-w-3xl",
        size === "tight" && "max-w-xl",
        className,
      )}
    >
      {children}
    </div>
  );
}
