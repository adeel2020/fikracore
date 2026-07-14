import React from "react";
import { C } from "../../types/telemetry.types";

interface EmbeddingLatencyPanelProps {
  latency: number;
  waveform: number[];
}

export const EmbeddingLatencyPanel: React.FC<EmbeddingLatencyPanelProps> = React.memo(({
  latency,
  waveform,
}) => {
  const maxWf = Math.max(...waveform, 1);

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-neutral-400">
            Embedding Latency
          </div>
          <div className="flex items-baseline gap-1">
            <div
              className="text-2xl font-bold"
              style={{
                color: C.purple,
                textShadow: `0 0 12px ${C.purple}80`,
              }}
            >
              {Math.round(latency)}
            </div>
            <span className="text-sm text-neutral-400">ms</span>
            <span className="ml-2 text-[10px] text-neutral-500">p50: {Math.round(latency * 0.85)}ms</span>
          </div>
        </div>
        {/* Oscilloscope waveform */}
        <div className="flex h-10 w-20 items-end gap-[1px]">
          {waveform.slice(0, 20).map((d, i) => {
            const h = Math.max(2, (d / maxWf) * 100);
            const isPeak = d > maxWf * 0.8;
            return (
              <div
                key={i}
                className="w-[3px] rounded-t transition-all duration-150"
                style={{
                  height: `${h}%`,
                  background: isPeak
                    ? `linear-gradient(to top, ${C.pink}, ${C.red})`
                    : `linear-gradient(to top, ${C.purple}, ${C.blue})`,
                  boxShadow: isPeak
                    ? `0 0 6px ${C.pink}80`
                    : `0 0 3px ${C.purple}60`,
                  opacity: 0.6 + (d / maxWf) * 0.4,
                }}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
});

EmbeddingLatencyPanel.displayName = "EmbeddingLatencyPanel";
