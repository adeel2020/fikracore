import React from "react";
import { Radar, Search, Database, Layers } from "lucide-react";
import { VectorDensityDataPoint, C } from "../types/telemetry.types";
import { VectorDensityChart } from "./charts/VectorDensityChart";
import { HitMissFallbackIndicator } from "./charts/HitMissFallbackIndicator";
import { EmbeddingLatencyPanel } from "./charts/EmbeddingLatencyPanel";
import { MetricBadge } from "./AIAgencyModule";

interface RAGSimilarityModuleProps {
  vectorData: VectorDensityDataPoint[];
  hit: number;
  miss: number;
  fallback: number;
  avgScore: number;
  latency: number;
  waveform: number[];
}

export const RAGSimilarityModule: React.FC<RAGSimilarityModuleProps> = React.memo(({
  vectorData,
  hit,
  miss,
  fallback,
  avgScore,
  latency,
  waveform,
}) => {
  return (
    <div className="flex flex-col gap-3">
      {/* Vector density chart with zone overlays */}
      <div>
        <div className="mb-1 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-neutral-400">
            <Radar className="h-3 w-3" />
            Embedding Cosine Similarity
          </div>
          <div
            className="text-[10px] font-mono"
            style={{ color: C.teal, textShadow: `0 0 4px ${C.teal}60` }}
          >
            μ={(avgScore / 100).toFixed(2)}
          </div>
        </div>
        <VectorDensityChart data={vectorData} />
      </div>

      {/* Hit/Miss/Fallback with precision metrics */}
      <HitMissFallbackIndicator data={[hit, miss, fallback]} />

      {/* Embedding latency with oscilloscope */}
      <EmbeddingLatencyPanel latency={latency} waveform={waveform} />

      {/* Compact stats matrix */}
      <div className="grid grid-cols-3 gap-2">
        <MetricBadge
          label="Avg Similarity"
          value={`${Math.round(avgScore)}%`}
          color={C.teal}
          icon={<Search className="h-3.5 w-3.5" />}
          trend="up"
        />
        <MetricBadge
          label="Index Size"
          value="12.4K"
          color={C.indigo}
          icon={<Database className="h-3.5 w-3.5" />}
        />
        <MetricBadge
          label="Chunk Count"
          value="3.2K"
          color={C.cyan}
          icon={<Layers className="h-3.5 w-3.5" />}
        />
      </div>
    </div>
  );
});

RAGSimilarityModule.displayName = "RAGSimilarityModule";
