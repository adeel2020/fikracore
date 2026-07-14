import React from "react";

export const CustomTooltip: React.FC<any> = React.memo(({ active, payload, label }) => {
  if (active && payload?.length) {
    return (
      <div className="rounded-lg border border-white/10 bg-black/85 px-3 py-2 text-xs backdrop-blur-md">
        <p className="text-neutral-400 mb-0.5">{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} className="font-semibold" style={{ color: p.color || p.stroke || p.fill }}>
            {p.name || p.dataKey}: {p.value.toLocaleString()}
          </p>
        ))}
      </div>
    );
  }
  return null;
});

CustomTooltip.displayName = "CustomTooltip";
