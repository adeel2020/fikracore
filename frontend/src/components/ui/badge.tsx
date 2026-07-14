import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "neon" | "alert" | "muted";
};

export function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variant === "default" &&
          "border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 shadow-[0_0_12px_rgba(0,229,255,0.25)]",
        variant === "neon" &&
          "border border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-400",
        variant === "alert" &&
          "border border-lime-400/30 bg-lime-400/10 text-lime-300 shadow-[0_0_12px_rgba(204,255,0,0.2)]",
        variant === "muted" &&
          "border border-white/10 bg-white/5 text-neutral-400",
        className
      )}
      {...props}
    />
  );
}
