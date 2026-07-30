import type { HTMLProps, ReactNode } from "react";
import { cn } from "@/lib/utils";

interface AuroraBackgroundProps extends HTMLProps<HTMLDivElement> {
  children: ReactNode;
  showRadialGradient?: boolean;
}

export function AuroraBackground({
  className,
  children,
  showRadialGradient = true,
  ...props
}: AuroraBackgroundProps) {
  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center overflow-hidden bg-background text-foreground",
        className
      )}
      {...props}
    >
      <div className="absolute inset-0 overflow-hidden">
        <div
          className={cn(
            `
            [--white-gradient:repeating-linear-gradient(100deg,var(--aurora-white)_0%,var(--aurora-white)_7%,var(--aurora-transparent)_10%,var(--aurora-transparent)_12%,var(--aurora-white)_16%)]
            [--dark-gradient:repeating-linear-gradient(100deg,var(--aurora-black)_0%,var(--aurora-black)_7%,var(--aurora-transparent)_10%,var(--aurora-transparent)_12%,var(--aurora-black)_16%)]
            [--aurora:repeating-linear-gradient(100deg,var(--aurora-blue-500)_10%,var(--aurora-indigo-300)_15%,var(--aurora-blue-300)_20%,var(--aurora-violet-200)_25%,var(--aurora-blue-400)_30%)]
            [background-image:var(--white-gradient),var(--aurora)]
            dark:[background-image:var(--dark-gradient),var(--aurora)]
            [background-size:300%,_200%]
            [background-position:50%_50%,50%_50%]
            filter blur-[10px] invert dark:invert-0
            after:absolute after:inset-0 after:content-[""] after:[background-image:var(--white-gradient),var(--aurora)]
            after:dark:[background-image:var(--dark-gradient),var(--aurora)]
            after:[background-size:200%,_100%]
            after:[background-attachment:fixed] after:mix-blend-difference after:animate-aurora
            pointer-events-none absolute -inset-[10px] opacity-50 will-change-transform`,
            showRadialGradient &&
              `[mask-image:radial-gradient(ellipse_at_100%_0%,black_10%,var(--aurora-transparent)_70%)]`
          )}
        />
      </div>
      {children}
    </div>
  );
}
