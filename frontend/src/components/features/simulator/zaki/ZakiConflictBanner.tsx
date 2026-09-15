"use client";

import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export interface ZakiConflictBannerProps {
  leadingHypothesis?: string;
  authoritativeDomain?: string;
  reasons?: string[];
  onRecompute?: () => void;
}

export function ZakiConflictBanner({
  leadingHypothesis = "Leading candidate cause",
  authoritativeDomain = "Primary domain",
  reasons = ["Attribution is inconsistent with the active hypothesis revision."],
  onRecompute,
}: ZakiConflictBannerProps) {
  return (
    <div
      className="m-3 p-3 rounded-lg bg-rose-950/40 border border-rose-500/50 text-rose-200 flex flex-col gap-2 shadow-lg shadow-rose-950/20"
      data-testid="zaki-conflict-banner"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-rose-400 font-bold text-xs tracking-wider uppercase">
          <AlertTriangle className="w-4 h-4 text-rose-400 animate-pulse" />
          <span>CONFLICT DETECTED</span>
        </div>
        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-rose-900/60 border border-rose-700/60 text-rose-300">
          Epistemic Inconsistency
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-900/60 p-2 rounded border border-rose-900/40">
        <div>
          <span className="text-[10px] text-slate-400 block font-mono uppercase">
            Leading Hypothesis
          </span>
          <span className="font-semibold text-slate-200">{leadingHypothesis}</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block font-mono uppercase">
            Domain Attribution
          </span>
          <span className="font-semibold text-rose-300">{authoritativeDomain}</span>
        </div>
      </div>

      <div className="text-[11px] text-rose-200/90 leading-snug">
        <p className="font-medium">
          {reasons[0] || "Current attribution conflicts with leading causal hypothesis."}
        </p>
      </div>

      <div className="flex items-center justify-between pt-1 border-t border-rose-900/40 text-[11px]">
        <span className="text-rose-300/80 italic">
          Recompute attribution before trusting domain ownership.
        </span>
        {onRecompute && (
          <button
            onClick={onRecompute}
            className="flex items-center gap-1 px-2 py-1 rounded bg-rose-900/80 hover:bg-rose-800 text-rose-100 font-mono text-[10px] transition border border-rose-700"
            data-testid="zaki-recompute-btn"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Recompute</span>
          </button>
        )}
      </div>
    </div>
  );
}
