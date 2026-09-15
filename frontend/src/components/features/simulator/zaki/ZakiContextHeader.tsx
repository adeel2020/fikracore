"use client";

import React from "react";
import { Radio, Activity, Minus, X } from "lucide-react";

export interface ZakiContextHeaderProps {
  sourceMode?: "SIMULATION" | "LIVE_INTENT";
  runId?: string;
  stageName?: string;
  revision?: number;
  copilotState?: string;
  onMinimize?: () => void;
  onClose?: () => void;
}

export function ZakiContextHeader({
  sourceMode = "SIMULATION",
  runId,
  stageName,
  revision,
  copilotState = "IDLE",
  onMinimize,
  onClose,
}: ZakiContextHeaderProps) {
  const isLive = sourceMode === "LIVE_INTENT";

  const stateBadgeColor =
    copilotState === "CONFLICT_DETECTED"
      ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
      : copilotState === "VALIDATION_REQUIRED" || copilotState === "RECOMMENDATION_READY"
      ? "bg-teal-500/20 text-teal-300 border-teal-500/40"
      : copilotState === "NEEDS_EVIDENCE"
      ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
      : copilotState === "REPLAY"
      ? "bg-purple-500/20 text-purple-300 border-purple-500/40"
      : "bg-cyan-500/20 text-cyan-300 border-cyan-500/40";

  return (
    <div
      className="flex items-center justify-between px-4 py-3 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur"
      data-testid="zaki-context-header"
    >
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1.5 font-bold text-sm text-slate-100">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span>ZAKI COPILOT</span>
        </div>

        {/* Source Mode Badge */}
        <div
          className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border ${
            isLive
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
              : "bg-blue-500/10 text-blue-400 border-blue-500/30"
          }`}
          data-testid="zaki-source-mode-badge"
        >
          <Radio className="w-3 h-3" />
          <span>{isLive ? "LIVE INTENT" : "SIMULATION"}</span>
        </div>

        {/* Run Scope */}
        {runId && (
          <span
            className="text-[11px] font-mono text-slate-400 bg-slate-800/60 px-1.5 py-0.5 rounded border border-slate-700/50"
            data-testid="zaki-run-id-badge"
          >
            {runId}
          </span>
        )}

        {/* Stage Scope */}
        {stageName && (
          <span
            className="text-[11px] font-mono text-cyan-400/90 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-800/40"
            data-testid="zaki-stage-badge"
          >
            {stageName}
          </span>
        )}

        {/* Revision */}
        {revision !== undefined && (
          <span
            className="text-[10px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded"
            data-testid="zaki-revision-badge"
          >
            r{revision}
          </span>
        )}

        {/* Copilot State */}
        {copilotState && (
          <span
            className={`text-[10px] uppercase font-mono font-semibold px-2 py-0.5 rounded border ${stateBadgeColor}`}
            data-testid="zaki-state-badge"
          >
            {copilotState}
          </span>
        )}
      </div>

      <div className="flex items-center gap-1">
        {onMinimize && (
          <button
            onClick={onMinimize}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
            aria-label="Minimize"
          >
            <Minus className="w-4 h-4" />
          </button>
        )}
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
