"use client";

import React from "react";
import { Layers, ChevronRight } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";

const iconStroke = { strokeWidth: 1.5 } as const;

interface EmbedStageProps {
  tokenEstimate: number;
  maxSeqLen: number;
  provider: any;
  structuredPayload: string;
  runEmbed: () => void;
}

export function EmbedStage({
  tokenEstimate,
  maxSeqLen,
  provider,
  structuredPayload,
  runEmbed,
}: EmbedStageProps) {
  return (
    <GlassCard className="p-6 relative" hover={false}>
      <div className="absolute top-0 left-0 w-40 h-40 bg-fuchsia-500/5 blur-3xl rounded-full" />
      <div className="mb-6 flex items-center gap-3 z-10 relative">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-fuchsia-500/10 border border-fuchsia-500/20">
          <Layers className="h-5 w-5 text-fuchsia-400" {...iconStroke} />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Embed — Tokenization diagnostics</h3>
          <p className="text-xs text-neutral-400 mt-0.5">
            Calculate sequence packing and token alignments for base model fine-tuning constraints
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3 z-10 relative">
        <div className="rounded-xl border border-white/5 bg-black/30 p-4 hover:border-white/10 transition-all duration-300">
          <p className="text-xs text-neutral-400 uppercase tracking-wider font-semibold">Estimated tokens</p>
          <p className="mt-2 text-3xl font-bold text-white tracking-tight">{tokenEstimate.toLocaleString()}</p>
          <div className="h-1 w-full bg-neutral-800 rounded-full mt-3 overflow-hidden">
            <div className="h-full bg-fuchsia-500" style={{ width: `${Math.min(100, (tokenEstimate / 2048) * 100)}%` }} />
          </div>
        </div>
        <div className="rounded-xl border border-white/5 bg-black/30 p-4 hover:border-white/10 transition-all duration-300">
          <p className="text-xs text-neutral-400 uppercase tracking-wider font-semibold">Sequence chunks</p>
          <p className="mt-2 text-3xl font-bold text-white tracking-tight">
            {Math.max(1, Math.ceil(tokenEstimate / maxSeqLen))}
          </p>
          <p className="text-[10px] text-neutral-500 mt-3 font-mono">
            Packed with max_seq_length={maxSeqLen}
          </p>
        </div>
        <div className="rounded-xl border border-white/5 bg-black/30 p-4 hover:border-white/10 transition-all duration-300">
          <p className="text-xs text-neutral-400 uppercase tracking-wider font-semibold">Format protocol</p>
          <p className="mt-2.5 text-lg font-semibold text-cyan-400">
            {provider?.messageFormat}
          </p>
          <p className="text-[10px] text-neutral-500 mt-4">
            Masked output training sequence
          </p>
        </div>
      </div>

      <div className="mt-6 z-10 relative">
        <p className="text-xs font-semibold uppercase tracking-wider text-neutral-300 mb-2">
          Tokenized string buffer (Truncated view)
        </p>
        <pre className="max-h-40 overflow-auto rounded-xl border border-white/5 bg-black/50 p-4 font-mono text-xs text-neutral-300 whitespace-pre-wrap leading-relaxed">
          {structuredPayload.slice(0, 800)}
          {structuredPayload.length > 800 ? "\n\n[... Remaining data hidden for performance ...]" : ""}
        </pre>
      </div>

      <Button
        className="mt-6 gap-2 bg-gradient-to-r from-fuchsia-600 to-fuchsia-500 hover:from-fuchsia-500 hover:to-fuchsia-400 text-white relative z-10"
        onClick={runEmbed}
      >
        Complete Tokenization & continue to Fine-tune
        <ChevronRight className="h-4 w-4" {...iconStroke} />
      </Button>
    </GlassCard>
  );
}
