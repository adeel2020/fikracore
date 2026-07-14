import React from "react";
import { TrendingUp } from "lucide-react";
import { C } from "../../types/telemetry.types";

interface HitMissFallbackIndicatorProps {
  data: number[]; // [hit, miss, fallback]
}

export const HitMissFallbackIndicator: React.FC<HitMissFallbackIndicatorProps> = React.memo(({ data }) => {
  const [hit, miss, fallback] = data;
  const total = hit + miss + fallback || 1;
  const hitPct = (hit / total) * 100;
  const missPct = (miss / total) * 100;
  const fbPct = (fallback / total) * 100;

  const precision = Math.round((hit / (hit + miss || 1)) * 100);
  const recall = Math.round((hit / (hit + fallback || 1)) * 100);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-neutral-400">
          Retrieval Precision
        </div>
        <div className="flex gap-2 text-[10px] font-mono">
          <span style={{ color: C.green, textShadow: `0 0 4px ${C.green}60` }}>
            P:{precision}%
          </span>
          <span style={{ color: C.blue, textShadow: `0 0 4px ${C.blue}60` }}>
            R:{recall}%
          </span>
        </div>
      </div>

      {/* Segmented bar with labels */}
      <div className="relative h-7 w-full">
        <div className="flex h-full w-full overflow-hidden rounded-lg border border-white/5 bg-white/[0.02]">
          <div
            className="flex items-center justify-center text-[9px] font-bold text-black transition-all duration-500"
            style={{
              width: `${hitPct}%`,
              background: `linear-gradient(135deg, #00FF87, #2DD4BF)`,
              boxShadow: `inset 0 0 12px ${C.green}40, 0 0 8px ${C.green}60`,
            }}
          >
            {hitPct > 12 ? `${Math.round(hitPct)}%` : ""}
          </div>
          <div
            className="flex items-center justify-center text-[9px] font-bold text-black transition-all duration-500"
            style={{
              width: `${missPct}%`,
              background: `linear-gradient(135deg, #FB923C, #FF6B35)`,
              boxShadow: `inset 0 0 12px ${C.orange}40`,
            }}
          >
            {missPct > 12 ? `${Math.round(missPct)}%` : ""}
          </div>
          <div
            className="flex items-center justify-center text-[9px] font-bold text-white transition-all duration-500"
            style={{
              width: `${fbPct}%`,
              background: `linear-gradient(135deg, #FF4444, #F43F5E)`,
              boxShadow: `inset 0 0 12px ${C.red}40`,
            }}
          >
            {fbPct > 12 ? `${Math.round(fbPct)}%` : ""}
          </div>
        </div>

        {/* Micro tick markers on bar */}
        {[25, 50, 75].map((tick) => (
          <div
            key={tick}
            className="absolute top-0 h-full w-px bg-white/10"
            style={{ left: `${tick}%` }}
          />
        ))}
      </div>

      {/* Compact legend */}
      <div className="flex justify-between text-[9px]">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ background: C.green, boxShadow: `0 0 4px ${C.green}` }} />
          <span className="text-green-400">Top-K Hit ({Math.round(hitPct)}%)</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ background: C.orange, boxShadow: `0 0 4px ${C.orange}` }} />
          <span className="text-orange-400">Low Conf. ({Math.round(missPct)}%)</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ background: C.red, boxShadow: `0 0 4px ${C.red}` }} />
          <span className="text-red-400">Fallback ({Math.round(fbPct)}%)</span>
        </span>
      </div>
    </div>
  );
});

HitMissFallbackIndicator.displayName = "HitMissFallbackIndicator";
