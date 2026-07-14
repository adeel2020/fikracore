import React from "react";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer } from "recharts";
import { VectorDensityDataPoint, C } from "../../types/telemetry.types";

interface VectorDensityChartProps {
  data: VectorDensityDataPoint[];
}

export const VectorDensityChart: React.FC<VectorDensityChartProps> = React.memo(({ data }) => {
  const highConfCount = data.filter((d) => d.score >= 0.7).length;
  const lowConfCount = data.filter((d) => d.score >= 0.4 && d.score < 0.7).length;
  const fallbackCount = data.filter((d) => d.score < 0.4).length;

  return (
    <div>
      <div className="h-32 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 6, right: 4, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="vector-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.purple} stopOpacity={0.85} />
                <stop offset="30%" stopColor={C.blue} stopOpacity={0.55} />
                <stop offset="70%" stopColor={C.cyan} stopOpacity={0.25} />
                <stop offset="100%" stopColor={C.cyan} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="zone-high" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="rgba(0,255,135,0.08)" />
                <stop offset="100%" stopColor="rgba(0,255,135,0.02)" />
              </linearGradient>
              <linearGradient id="zone-mid" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="rgba(255,229,0,0.06)" />
                <stop offset="100%" stopColor="rgba(255,229,0,0.02)" />
              </linearGradient>
              <linearGradient id="zone-low" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="rgba(255,68,68,0.06)" />
                <stop offset="100%" stopColor="rgba(255,68,68,0.02)" />
              </linearGradient>
            </defs>
            <XAxis dataKey="index" hide axisLine={false} tickLine={false} />
            <YAxis hide domain={[0, 1]} axisLine={false} tickLine={false} />

            {/* Confetti scatter dots for higher realism */}
            {data.map((d, i) => (
              <circle
                key={i}
                cx={`${(d.index / data.length) * 100}%`}
                cy={`${(1 - d.score) * 100}%`}
                r={d.score > 0.7 ? 2 : d.score > 0.4 ? 1.2 : 0.8}
                fill={
                  d.score >= 0.7
                    ? C.green
                    : d.score >= 0.4
                    ? C.yellow
                    : C.red
                }
                fillOpacity={0.6}
                style={{
                  filter: `drop-shadow(0 0 ${
                    d.score >= 0.7 ? 4 : 2
                  }px ${
                    d.score >= 0.7
                      ? C.green
                      : d.score >= 0.4
                      ? C.yellow
                      : C.red
                  }80)`,
                }}
              />
            ))}

            {/* Zone fill: High confidence area (0.7 - 1.0) */}
            <Area
              type="monotone"
              dataKey={() => 1}
              stroke="none"
              fill="url(#zone-high)"
              stackId="zones"
            />
            <Area
              type="monotone"
              dataKey={() => 0.7}
              stroke="none"
              fill="url(#zone-high)"
              stackId="zones"
            />

            {/* Zone fill: Medium confidence area (0.4 - 0.7) */}
            <Area
              type="monotone"
              dataKey={() => 0.7}
              stroke="none"
              fill="url(#zone-mid)"
              stackId="zones"
            />
            <Area
              type="monotone"
              dataKey={() => 0.4}
              stroke="none"
              fill="url(#zone-mid)"
              stackId="zones"
            />

            {/* Zone fill: Low confidence area (0 - 0.4) */}
            <Area
              type="monotone"
              dataKey={() => 0.4}
              stroke="none"
              fill="url(#zone-low)"
              stackId="zones"
            />

            {/* Threshold lines */}
            <Area
              type="monotone"
              dataKey={() => 0.7}
              stroke={C.green}
              strokeWidth={1.2}
              strokeDasharray="4 3"
              fill="none"
              strokeOpacity={0.7}
            />
            <Area
              type="monotone"
              dataKey={() => 0.4}
              stroke={C.yellow}
              strokeWidth={0.8}
              strokeDasharray="3 3"
              fill="none"
              strokeOpacity={0.5}
            />

            {/* Main similarity curve */}
            <Area
              type="monotone"
              dataKey="score"
              stroke={C.purple}
              fill="url(#vector-grad)"
              strokeWidth={2}
              dot={false}
              style={{ filter: `drop-shadow(0 0 8px ${C.purple}80)` }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Embedded zone legend + counts */}
      <div className="mt-1 grid grid-cols-3 gap-1">
        <div className="rounded border border-green-500/20 bg-green-500/5 px-2 py-1 text-center">
          <div className="text-[9px] font-mono text-green-400">HIGH ≥0.70</div>
          <div className="text-xs font-bold text-green-300">{highConfCount}</div>
        </div>
        <div className="rounded border border-yellow-500/20 bg-yellow-500/5 px-2 py-1 text-center">
          <div className="text-[9px] font-mono text-yellow-400">MID 0.40–0.69</div>
          <div className="text-xs font-bold text-yellow-300">{lowConfCount}</div>
        </div>
        <div className="rounded border border-red-500/20 bg-red-500/5 px-2 py-1 text-center">
          <div className="text-[9px] font-mono text-red-400">LOW {"<"}0.40</div>
          <div className="text-xs font-bold text-red-300">{fallbackCount}</div>
        </div>
      </div>
    </div>
  );
});

VectorDensityChart.displayName = "VectorDensityChart";
