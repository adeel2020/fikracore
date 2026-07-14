"use client";

import * as SwitchPrimitive from "@radix-ui/react-switch";
import { cn } from "@/lib/utils";

export function Switch({
  className,
  ...props
}: React.ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      className={cn(
        "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border border-white/10 bg-white/5 transition-colors data-[state=checked]:border-cyan-500/50 data-[state=checked]:bg-cyan-500/20",
        className
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        className={cn(
          "pointer-events-none block h-5 w-5 translate-x-0.5 rounded-full bg-neutral-400 shadow-lg transition-transform data-[state=checked]:translate-x-[22px] data-[state=checked]:bg-cyan-400 data-[state=checked]:shadow-[0_0_12px_rgba(0,229,255,0.8)]"
        )}
      />
    </SwitchPrimitive.Root>
  );
}
