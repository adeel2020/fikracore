"use client";

import React from "react";
import { FileCode2, Loader2, ChevronRight } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DEFAULT_LLM_TEMPLATES, LLM_PROVIDERS } from "@/lib/llm-templates";
import { SftDataset } from "@/lib/api/sft";

const iconStroke = { strokeWidth: 1.5 } as const;

interface PreprocessStageProps {
  loadingDatasets: boolean;
  datasets: SftDataset[];
  selectedDatasetId: string;
  setSelectedDatasetId: (id: string) => void;
  templateId: string;
  setTemplateId: (id: string) => void;
  provider: any;
  template: any;
  preprocessPreview: string;
  preprocessVars: Record<string, any>;
  applyPreprocess: () => void;
}

export function PreprocessStage({
  loadingDatasets,
  datasets,
  selectedDatasetId,
  setSelectedDatasetId,
  templateId,
  setTemplateId,
  provider,
  template,
  preprocessPreview,
  preprocessVars,
  applyPreprocess,
}: PreprocessStageProps) {
  return (
    <GlassCard className="p-6 relative" hover={false}>
      <div className="absolute top-0 left-0 w-40 h-40 bg-cyan-500/5 blur-3xl rounded-full" />
      <div className="mb-6 flex items-center gap-3 relative z-10">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/20">
          <FileCode2 className="h-5 w-5 text-cyan-400" {...iconStroke} />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Preprocess — Formatting Engine</h3>
          <p className="text-xs text-neutral-400 mt-0.5">
            Load local datasets and apply system instruction layouts for fine-tuning tokenization
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 relative z-10">
        <div>
          <label
            htmlFor="preprocess-dataset"
            className="mb-2 block text-xs font-semibold text-neutral-300 uppercase tracking-wider"
          >
            Source dataset (.jsonl)
          </label>
          {loadingDatasets ? (
            <div className="h-10 rounded-xl bg-white/5 border border-white/10 flex items-center px-3 gap-2">
              <Loader2 className="h-4 w-4 text-cyan-400 animate-spin" />
              <span className="text-xs text-neutral-400">Scanning workspace datasets...</span>
            </div>
          ) : (
            <select
              id="preprocess-dataset"
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-3 text-sm text-white focus:border-cyan-500/40 focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id} className="bg-neutral-900 text-neutral-200">
                  {d.name} ({d.rows.toLocaleString()} tickets · {d.size_kb ? `${d.size_kb} KB` : "Local"})
                </option>
              ))}
            </select>
          )}
        </div>
        <div>
          <label
            htmlFor="preprocess-template"
            className="mb-2 block text-xs font-semibold text-neutral-300 uppercase tracking-wider"
          >
            System Instruction Formatter
          </label>
          <select
            id="preprocess-template"
            value={templateId}
            onChange={(e) => setTemplateId(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-3 text-sm text-white focus:border-cyan-500/40 focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
          >
            {DEFAULT_LLM_TEMPLATES.map((t) => (
              <option key={t.id} value={t.id} className="bg-neutral-900 text-neutral-200">
                {LLM_PROVIDERS[t.providerId].name} — {t.filename}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 relative z-10">
        {provider && <Badge variant={provider.badgeVariant}>{provider.name}</Badge>}
        {provider && <Badge variant="muted" className="border border-white/10">{provider.messageFormat}</Badge>}
        <span className="text-xs text-neutral-400">{template.description}</span>
      </div>

      <div className="mt-6 relative z-10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-neutral-300">
            Rendered Structure Preview
          </span>
          <span className="text-[10px] text-neutral-500">Auto-generated via Jinja</span>
        </div>
        <pre className="max-h-56 overflow-auto rounded-xl border border-white/10 bg-black/60 p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap text-neutral-300 shadow-inner">
          {preprocessPreview}
        </pre>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 relative z-10">
        {Object.entries(preprocessVars).map(([key, value]) => (
          <span
            key={key}
            className="rounded-md border border-white/5 bg-white/5 px-2.5 py-1 text-[10px] text-neutral-400"
          >
            <span className="text-cyan-400 font-medium">{key}</span>=
            {typeof value === "string" && value.length > 40 ? `${value.slice(0, 40)}…` : String(value)}
          </span>
        ))}
      </div>

      <Button
        className="mt-6 gap-2 bg-gradient-to-r from-cyan-600 to-cyan-500 text-white hover:from-cyan-500 hover:to-cyan-400 shadow-md relative z-10"
        onClick={applyPreprocess}
      >
        Load structured payload into Tokenizer
        <ChevronRight className="h-4 w-4" {...iconStroke} />
      </Button>
    </GlassCard>
  );
}
