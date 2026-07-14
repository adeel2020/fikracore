import React from "react";
import { AreaChart, Area, ResponsiveContainer } from "recharts";
import { SparklinePoint } from "../../types/dashboard.types";

interface MiniSparklineProps {
  data: SparklinePoint[];
  color: string;
}

export const MiniSparkline: React.FC<MiniSparklineProps> = React.memo(({ data, color }) => {
  return (
    <ResponsiveContainer width="100%" height={32}>
      <AreaChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={`spark-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="v"
          stroke={color}
          fill={`url(#spark-${color})`}
          strokeWidth={1.5}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
});

MiniSparkline.displayName = "MiniSparkline";
