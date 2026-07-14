import React from "react";
import { GraphHopsData } from "../../types/telemetry.types";

interface GraphHopsBarsProps {
  hops: GraphHopsData;
}

export const GraphHopsBars: React.FC<GraphHopsBarsProps> = React.memo(({ hops }) => {
  const maxVal = Math.max(hops["1-Hop"], hops["2-Hop"], hops["3-Hop"], 1);

  const items = [
    { key: "1-Hop", value: hops["1-Hop"], color: "#00FF87" },
    { key: "2-Hop", value: hops["2-Hop"], color: "#22D3EE" },
    { key: "3-Hop", value: hops["3-Hop"], color: "#A855F7" },
  ];

  return (
    <div className="space-y-1.5">
      <div className="text-[10px] uppercase tracking-wider text-neutral-400">
        Sub-Graph Depth
      </div>
      {items.map((item) => (
        <div key={item.key} className="flex items-center gap-2">
          <span className="w-10 text-[10px] font-mono text-neutral-300">
            {item.key}
          </span>
          <div className="h-3 flex-1 overflow-hidden rounded-full bg-white/5">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${(item.value / maxVal) * 100}%`,
                background: `linear-gradient(90deg, ${item.color}, ${item.color}cc)`,
                boxShadow: `0 0 6px ${item.color}60`,
              }}
            />
          </div>
          <span
            className="w-8 text-right text-[10px] font-mono"
            style={{ color: item.color, textShadow: `0 0 4px ${item.color}60` }}
          >
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
});

GraphHopsBars.displayName = "GraphHopsBars";
