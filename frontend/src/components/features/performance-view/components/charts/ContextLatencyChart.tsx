import React from "react";
import { ResponsiveContainer, LineChart, Line, YAxis, XAxis, Area } from "recharts";
import { LatencyDataPoint, C } from "../../types/telemetry.types";

interface ContextLatencyChartProps {
  data: LatencyDataPoint[];
}

export const ContextLatencyChart: React.FC<ContextLatencyChartProps> = React.memo(({ data }) => {
  const currentVal = data[data.length - 1]?.v || 0;

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-neutral-400">
          Context Extraction Latency
        </div>
        <div
          className="text-xs font-bold"
          style={{ color: C.blue, textShadow: `0 0 6px ${C.blue}60` }}
        >
          {Math.round(currentVal)}
          <span className="ml-1 text-neutral-400">ms</span>
        </div>
      </div>
      <div className="h-12 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 2, right: 2, bottom: 0, left: 2 }}>
            <defs>
              <linearGradient id="ctx-latency-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.blue} stopOpacity={0.5} />
                <stop offset="100%" stopColor={C.blue} stopOpacity={0} />
              </linearGradient>
            </defs>
            <YAxis hide domain={[0, 120]} />
            <XAxis hide dataKey="t" />
            <Line
              type="monotone"
              dataKey="v"
              stroke={C.blue}
              strokeWidth={1.5}
              dot={false}
              style={{ filter: `drop-shadow(0 0 4px ${C.blue}80)` }}
            />
            <Area
              type="monotone"
              dataKey="v"
              fill="url(#ctx-latency-grad)"
              stroke="none"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});

ContextLatencyChart.displayName = "ContextLatencyChart";
