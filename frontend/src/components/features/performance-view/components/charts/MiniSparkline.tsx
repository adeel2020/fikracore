import React from "react";
import { AreaChart, Area, YAxis, XAxis, ResponsiveContainer } from "recharts";
import { SparklineDataPoint } from "../../types/telemetry.types";

interface MiniSparklineProps {
  data: SparklineDataPoint[];
  color: string;
  height?: number;
}

export const MiniSparkline: React.FC<MiniSparklineProps> = React.memo(({
  data,
  color,
  height = 50,
}) => {
  const id = `spark-${color.replace("#", "")}`;

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.45} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <YAxis hide domain={[0, 100]} />
          <XAxis
            dataKey="d"
            tick={{
              fill: "#737373",
              fontSize: 9,
              fontFamily: "var(--font-geist-mono)",
            }}
            axisLine={false}
            tickLine={false}
            interval={0}
          />
          <Area
            type="monotone"
            dataKey="v"
            stroke={color}
            fill={`url(#${id})`}
            strokeWidth={1.5}
            dot={false}
            style={{ filter: `drop-shadow(0 0 3px ${color}80)` }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
});

MiniSparkline.displayName = "MiniSparkline";
