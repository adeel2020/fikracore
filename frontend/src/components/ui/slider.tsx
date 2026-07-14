"use client";

import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";

export function Slider({
  className,
  ...props
}: React.ComponentProps<typeof SliderPrimitive.Root>) {
  return (
    <SliderPrimitive.Root
      className={cn("relative flex w-full touch-none select-none items-center", className)}
      {...props}
    >
      <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-white/10">
        <SliderPrimitive.Range className="absolute h-full bg-gradient-to-r from-cyan-500 to-cyan-400 shadow-[0_0_8px_rgba(0,229,255,0.6)]" />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb className="block h-4 w-4 rounded-full border-2 border-cyan-400 bg-neutral-950 shadow-[0_0_12px_rgba(0,229,255,0.8)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50" />
    </SliderPrimitive.Root>
  );
}
