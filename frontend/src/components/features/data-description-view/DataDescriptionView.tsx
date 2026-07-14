"use client";

import React from "react";
import { Database } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { useDataDescription } from "./useDataDescription";

export function DataDescriptionView() {
  const {
    dataset,
    filledCount,
    descriptions,
    generatingColumn,
    generatingAll,
    updateDescription,
    generateOne,
    generateAll,
  } = useDataDescription();

  if (!dataset) {
    return (
      <GlassCard className="p-4" hover={false}>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Database className="h-8 w-8 text-neutral-600 mb-2" />
          <p className="text-sm text-neutral-400 font-semibold">No dataset loaded</p>
          <p className="text-xs text-neutral-500 mt-1">Upload a dataset in the Data Loader to describe its columns.</p>
        </div>
      </GlassCard>
    );
  }

  return (
    <div className="space-y-4">
      <GlassCard className="p-4" hover={false}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10">
              <Database className="h-4 w-4 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-sm font-medium text-white">Column Descriptions</h2>
              <p className="text-xs text-neutral-400">
                {filledCount} of {dataset.columns.length} described ·{" "}
                {dataset.rows.toLocaleString()} rows
              </p>
            </div>
          </div>
        </div>
      </GlassCard>

      <div className="space-y-3">
        {dataset.columns.map((col: any) => {
          const isGenerating = generatingColumn === col.name;
          const hasDescription = Boolean(descriptions[col.name]?.trim());

          return (
            <GlassCard key={col.name} className="p-0 overflow-hidden" hover={false}>
              <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-start">
                <div className="shrink-0 sm:w-44">
                  <div className="flex flex-wrap items-center gap-2">
                    <code className="text-sm font-medium text-white">{col.name}</code>
                  </div>
                </div>

                <div className="min-w-0 flex-1">
                  <textarea
                    value={descriptions[col.name] ?? ""}
                    onChange={(e) => updateDescription(col.name, e.target.value)}
                    placeholder={`Describe what "${col.name}" represents in ${dataset.name}…`}
                    rows={2}
                    className="w-full resize-y rounded-xl border border-white/10 bg-black/30 px-3 py-2.5 text-sm leading-relaxed text-neutral-200 placeholder:text-neutral-600 focus:border-cyan-500/40 focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
                    aria-label={`Description for ${col.name}`}
                  />
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}
