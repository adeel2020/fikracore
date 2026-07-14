import React from "react";
import { BarChart, Bar, ResponsiveContainer } from "recharts";
import { CHART_COLORS } from "@/lib/chart-colors";
import { latencyBarData } from "../../types/dashboard.types";

export const LatencyBarChart: React.FC = React.memo(() => {
  return (
    <ResponsiveContainer width="100%" height={40}>
      <BarChart data={latencyBarData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <Bar dataKey="v" fill={CHART_COLORS.neonGreen} opacity={0.8} radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
});

LatencyBarChart.displayName = "LatencyBarChart";
