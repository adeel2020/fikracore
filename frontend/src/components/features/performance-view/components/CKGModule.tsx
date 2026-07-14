import React from "react";
import { Share2, GitBranch } from "lucide-react";
import { ResponsiveContainer, BarChart, XAxis, YAxis, Bar, Cell } from "recharts";
import { GraphHopsData, LatencyDataPoint, C } from "../types/telemetry.types";
import { SubgraphVisualizer } from "./charts/SubgraphVisualizer";
import { GraphHopsBars } from "./charts/GraphHopsBars";
import { ContextLatencyChart } from "./charts/ContextLatencyChart";

interface CKGModuleProps {
  graphHops: GraphHopsData;
  weightData: { name: string; weight: number }[];
  latencyData: LatencyDataPoint[];
  enabled: boolean;
}

export const CKGModule: React.FC<CKGModuleProps> = React.memo(({
  graphHops,
  weightData,
  latencyData,
  enabled,
}) => {
  return (
    <div className="flex flex-col gap-4">
      {/* Subgraph visualization */}
      <div>
        <div className="mb-1 flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-neutral-400">
          <Share2 className="h-3 w-3" />
          Entity-Relation Subgraph
        </div>
        <SubgraphVisualizer enabled={enabled} />
      </div>

      {/* Graph hops */}
      <GraphHopsBars hops={graphHops} />

      {/* Context latency */}
      <ContextLatencyChart data={latencyData} />

      {/* Entity relation weights */}
      <div>
        <div className="mb-1 flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-neutral-400">
          <GitBranch className="h-3 w-3" />
          Relation Weight Distribution
        </div>
        <div className="h-14 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weightData} margin={{ top: 0, right: 2, bottom: 0, left: 0 }}>
              <XAxis
                dataKey="name"
                tick={{
                  fill: "#737373",
                  fontSize: 9,
                  fontFamily: "var(--font-geist-mono)",
                }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis hide domain={[0, 100]} />
              <Bar
                dataKey="weight"
                radius={[2, 2, 0, 0]}
                style={{ filter: `drop-shadow(0 0 4px ${C.cyan}60)` }}
              >
                {weightData.map((_, i) => (
                  <Cell
                    key={i}
                    fill={
                      [C.cyan, C.purple, C.green, C.orange, C.blue, C.pink][i % 6]
                    }
                    fillOpacity={0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-1 flex justify-between text-[9px] font-mono text-neutral-500">
          <span>Relation IDs</span>
          <span style={{ color: C.cyan, textShadow: `0 0 4px ${C.cyan}60` }}>
            Weights
          </span>
        </div>
      </div>
    </div>
  );
});

CKGModule.displayName = "CKGModule";
