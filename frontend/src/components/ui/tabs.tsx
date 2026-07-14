"use client";

import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "@/lib/utils";

const Tabs = TabsPrimitive.Root;

const TabsList = ({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List>) => (
  <TabsPrimitive.List
    className={cn("flex gap-6 border-b border-white/10", className)}
    {...props}
  />
);

const TabsTrigger = ({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) => (
  <TabsPrimitive.Trigger
    className={cn(
      "relative pb-3 text-sm font-medium text-neutral-400 transition-colors data-[state=active]:text-white",
      "after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-full after:scale-x-0 after:bg-gradient-to-r after:from-cyan-500 after:to-blue-600 after:shadow-[0_0_12px_rgba(0,229,255,0.6)] after:transition-transform data-[state=active]:after:scale-x-100",
      className
    )}
    {...props}
  />
);

const TabsContent = ({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) => (
  <TabsPrimitive.Content className={cn("mt-6 outline-none", className)} {...props} />
);

export { Tabs, TabsList, TabsTrigger, TabsContent };
