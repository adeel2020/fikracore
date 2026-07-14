import React from "react";

interface GlassWidgetCardProps {
  title?: string;
  className?: string;
  children: React.ReactNode;
  rightSlot?: React.ReactNode;
  loading?: boolean;
}

export const GlassWidgetCard: React.FC<GlassWidgetCardProps> = React.memo(({
  title,
  className = "",
  children,
  rightSlot,
  loading = false,
}) => {
  return (
    <div
      className={`relative rounded-2xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl shadow-2xl transition-all duration-300 ${className}`}
    >
      {title && (
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-200">
            {title}
          </h3>
          {rightSlot}
        </div>
      )}
      {loading ? (
        <div className="space-y-3 animate-pulse py-2">
          <div className="h-4 bg-white/10 rounded w-3/4"></div>
          <div className="space-y-2">
            <div className="h-20 bg-white/5 rounded"></div>
            <div className="h-3 bg-white/10 rounded w-5/6"></div>
          </div>
        </div>
      ) : (
        children
      )}
    </div>
  );
});

GlassWidgetCard.displayName = "GlassWidgetCard";
