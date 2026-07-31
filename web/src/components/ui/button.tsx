import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

// Acabado "cristal": fondo translúcido + backdrop-blur para que se filtre lo
// que hay detrás, borde fino de brillo y una veladura superior — glassmorphism
// real, no solo brillo pintado. Adaptado a los tonos de marca (azul), no al
// negro fijo del componente de referencia. Variantes sin fondo (outline/ghost/
// link) se quedan planas — no hay superficie tras la que difuminar nada.
const GLASS = "relative isolate overflow-hidden backdrop-blur-md before:absolute before:inset-0 before:rounded-[inherit] before:bg-gradient-to-b before:from-white/40 before:via-white/5 before:to-transparent before:pointer-events-none before:transition-opacity before:duration-200 hover:before:from-white/55 active:before:opacity-60 active:not-aria-[haspopup]:translate-y-1 transition-[transform,box-shadow,background-color,backdrop-filter] duration-150";

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded-lg border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: `${GLASS} border border-white/15 bg-primary/75 text-primary-foreground shadow-[0_8px_30px_-10px_rgba(30,64,175,0.5),inset_0_1px_0_rgba(255,255,255,0.4),inset_0_-1px_0_rgba(255,255,255,0.08)] hover:border-white/25 hover:bg-primary/85 hover:shadow-[0_10px_36px_-8px_rgba(30,64,175,0.6),inset_0_1px_0_rgba(255,255,255,0.5),inset_0_-1px_0_rgba(255,255,255,0.12)] active:shadow-[inset_0_2px_5px_rgba(15,23,42,0.35)]`,
        outline:
          "border-border bg-background hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground",
        secondary: `${GLASS} border border-white/50 bg-secondary/55 text-secondary-foreground shadow-[0_6px_20px_-10px_rgba(30,58,138,0.3),inset_0_1px_0_rgba(255,255,255,0.65),inset_0_-1px_0_rgba(255,255,255,0.2)] hover:border-white/70 hover:bg-secondary/70 hover:shadow-[0_8px_24px_-8px_rgba(30,58,138,0.35),inset_0_1px_0_rgba(255,255,255,0.75)] active:shadow-[inset_0_2px_4px_rgba(30,58,138,0.2)] aria-expanded:bg-secondary/70 aria-expanded:text-secondary-foreground`,
        ghost:
          "hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground",
        destructive: `${GLASS} backdrop-blur-sm border border-destructive/20 bg-destructive/10 text-destructive shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] hover:border-destructive/30 hover:bg-destructive/20 hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.55)] active:shadow-[inset_0_1px_2px_rgba(220,38,38,0.25)] focus-visible:border-destructive/40 focus-visible:ring-destructive/20`,
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default:
          "h-8 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
        xs: "h-6 gap-1 rounded-[min(var(--radius-md),10px)] px-2 text-xs in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-7 gap-1 rounded-[min(var(--radius-md),12px)] px-2.5 text-[0.8rem] in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",
        lg: "h-9 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
        icon: "size-8",
        "icon-xs":
          "size-6 rounded-[min(var(--radius-md),10px)] in-data-[slot=button-group]:rounded-lg [&_svg:not([class*='size-'])]:size-3",
        "icon-sm":
          "size-7 rounded-[min(var(--radius-md),12px)] in-data-[slot=button-group]:rounded-lg",
        "icon-lg": "size-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
