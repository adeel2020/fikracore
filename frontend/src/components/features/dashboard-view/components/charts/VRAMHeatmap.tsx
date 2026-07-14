import React from "react";
import { heatmapData } from "../../types/dashboard.types";

export const VRAMHeatmap: React.FC = React.memo(() => {
  return (
    <div className="grid gap-[1.5px]" style={{ gridTemplateColumns: "repeat(16, 1fr)" }}>
      {heatmapData.map((row, ri) =>
        row.map((v, ci) => {
          const intensity = Math.floor(v * 255);
          const r = Math.min(255, intensity + 100);
          const g = Math.min(200, Math.floor(intensity * 0.6));
          const b = Math.max(0, 255 - intensity);
          return (
            <div
              key={`${ri}-${ci}`}
              className="aspect-square rounded-sm"
              style={{
                backgroundColor: `rgb(${r}, ${g}, ${b})`,
                opacity: 0.7 + v * 0.3,
              }}
            />
          );
        })
      )}
    </div>
  );
});

VRAMHeatmap.displayName = "VRAMHeatmap";
