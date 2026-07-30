import { type CSSProperties, type ReactNode, useEffect, useRef } from "react";
import { GradientWave } from "@/components/ui/gradient-wave";
import { cn } from "@/lib/utils";

interface VerticalMarqueeProps {
  children: ReactNode;
  pauseOnHover?: boolean;
  reverse?: boolean;
  className?: string;
  speed?: number;
}

function VerticalMarquee({
  children,
  pauseOnHover = false,
  reverse = false,
  className,
  speed = 30,
}: VerticalMarqueeProps) {
  return (
    <div
      className={cn("group flex flex-col overflow-hidden", className)}
      style={{ "--duration": `${speed}s` } as CSSProperties}
    >
      <div
        className={cn(
          "flex shrink-0 flex-col animate-marquee-vertical",
          reverse && "[animation-direction:reverse]",
          pauseOnHover && "group-hover:[animation-play-state:paused]",
        )}
      >
        {children}
      </div>
      <div
        className={cn(
          "flex shrink-0 flex-col animate-marquee-vertical",
          reverse && "[animation-direction:reverse]",
          pauseOnHover && "group-hover:[animation-play-state:paused]",
        )}
        aria-hidden="true"
      >
        {children}
      </div>
    </div>
  );
}

const MARQUEE_ITEMS = [
  "Periodistas de datos",
  "Empresas licitadoras",
  "Investigadores",
  "Administraciones públicas",
  "Auditoría y compliance",
  "Ciudadanía",
];

export default function CTAWithVerticalMarquee() {
  const marqueeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const marqueeContainer = marqueeRef.current;
    if (!marqueeContainer) return;

    let frame: number;

    const updateOpacity = () => {
      const items = marqueeContainer.querySelectorAll(".marquee-item");
      const containerRect = marqueeContainer.getBoundingClientRect();
      const centerY = containerRect.top + containerRect.height / 2;

      items.forEach((item) => {
        const itemRect = item.getBoundingClientRect();
        const itemCenterY = itemRect.top + itemRect.height / 2;
        const distance = Math.abs(centerY - itemCenterY);
        const maxDistance = containerRect.height / 2;
        const normalizedDistance = Math.min(distance / maxDistance, 1);
        const opacity = 1 - normalizedDistance * 0.75;
        (item as HTMLElement).style.opacity = opacity.toString();
      });

      frame = requestAnimationFrame(updateOpacity);
    };

    frame = requestAnimationFrame(updateOpacity);
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <section className="relative flex min-h-screen w-full items-center overflow-hidden bg-[linear-gradient(to_bottom,color-mix(in_srgb,var(--background)_33%,var(--aurora-blue-500)_67%)_0%,var(--background)_45%)] px-6 py-16 text-foreground sm:py-24">
      <GradientWave className="opacity-30" />
      <div className="relative mx-auto w-full max-w-7xl">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2 lg:gap-24">
          <div className="max-w-xl space-y-8">
            <h2 className="animate-fade-in-up text-5xl font-medium leading-tight tracking-tight text-foreground [animation-delay:200ms] md:text-6xl lg:text-7xl">
              Hecho para quien vigila la contratación{" "}
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                pública
              </span>
            </h2>
            <p className="animate-fade-in-up text-lg leading-relaxed text-muted-foreground [animation-delay:400ms] md:text-xl">
              Desde una pregunta puntual hasta una vigilancia permanente: el mismo agente sirve a
              quien pregunta una vez y a quien revisa las licitaciones cada día.
            </p>
            <div className="animate-fade-in-up flex flex-wrap gap-4 [animation-delay:600ms]">
              <a
                href="/app#registro"
                className="group relative overflow-hidden rounded-md bg-foreground px-6 py-3 font-medium text-background transition-all duration-300 hover:scale-105 hover:shadow-lg"
              >
                <span className="relative z-10">CREAR CUENTA GRATIS</span>
                <div className="absolute inset-0 -translate-x-[200%] bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700 group-hover:translate-x-[200%]" />
              </a>
              <a
                href="/docs"
                className="group relative overflow-hidden rounded-md border border-border bg-secondary px-6 py-3 font-medium text-secondary-foreground transition-all duration-300 hover:scale-105 hover:shadow-lg"
              >
                <span className="relative z-10">VER DOCUMENTACIÓN</span>
                <div className="absolute inset-0 -translate-x-[200%] bg-gradient-to-r from-transparent via-foreground/10 to-transparent transition-transform duration-700 group-hover:translate-x-[200%]" />
              </a>
            </div>
          </div>

          <div
            ref={marqueeRef}
            className="animate-fade-in-up relative flex h-[600px] items-center justify-center [animation-delay:400ms] lg:h-[700px]"
          >
            <div
              className="relative h-full w-full"
              style={{
                maskImage:
                  "linear-gradient(to bottom, transparent 0%, black 18%, black 82%, transparent 100%)",
                WebkitMaskImage:
                  "linear-gradient(to bottom, transparent 0%, black 18%, black 82%, transparent 100%)",
              }}
            >
              <VerticalMarquee speed={20} className="h-full">
                {MARQUEE_ITEMS.map((item, idx) => (
                  <div
                    key={idx}
                    className="marquee-item py-8 text-4xl font-light tracking-tight md:text-5xl lg:text-6xl xl:text-7xl"
                  >
                    {item}
                  </div>
                ))}
              </VerticalMarquee>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
