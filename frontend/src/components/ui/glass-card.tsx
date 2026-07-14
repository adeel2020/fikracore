import React, { createContext, useContext } from "react";
import { cn, glassSurfaceStatic } from "@/lib/utils";

type GlassCardProps = React.HTMLAttributes<HTMLDivElement> & {
  hover?: boolean;
};

export const GlassCardContext = createContext<{ isEditing?: boolean; isLight?: boolean }>({ isEditing: true, isLight: false });

export function GlassCard({
  className,
  hover = true,
  children,
  ...props
}: GlassCardProps) {
  const { isEditing, isLight } = useContext(GlassCardContext);
  const shouldHover = hover && isEditing !== false;

  return (
    <div
      className={cn(
        "glass-card",
        isLight
          ? "bg-slate-50/95 border border-slate-200 shadow-sm text-slate-800"
          : (isEditing !== false
              ? glassSurfaceStatic
              : "bg-[#131926] border border-transparent shadow-none text-white"),
        shouldHover &&
          (isLight 
            ? "hover:bg-slate-100/80 hover:border-cyan-400/35 transition-all duration-300"
            : "hover:bg-white/[0.08] hover:border-cyan-400/35 transition-all duration-300"),
        "rounded-2xl",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

