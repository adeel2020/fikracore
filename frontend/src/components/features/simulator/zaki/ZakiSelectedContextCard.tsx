"use client";

import React from "react";
import { X, Target, GitCommit, Network, AlertTriangle, Layers, Cpu, Globe } from "lucide-react";
import type { ZakiSelectedContext } from "@/lib/simulation-store";

export interface ZakiSelectedContextCardProps {
  context: ZakiSelectedContext;
  onClear: () => void;
}

export function ZakiSelectedContextCard({
  context,
  onClear,
}: ZakiSelectedContextCardProps) {
  const getContextIcon = () => {
    switch (context.context_type) {
      case "HYPOTHESIS":
        return <Target className="w-3.5 h-3.5 text-amber-400" />;
      case "PATHWAY":
        return <GitCommit className="w-3.5 h-3.5 text-cyan-400" />;
      case "CONNECTION":
        return <Network className="w-3.5 h-3.5 text-purple-400" />;
      case "KNOWLEDGE_GAP":
        return <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />;
      case "DOMAIN_ATTRIBUTION":
        return <Globe className="w-3.5 h-3.5 text-teal-400" />;
      case "STAGE":
        return <Layers className="w-3.5 h-3.5 text-blue-400" />;
      case "REASONING_CORE":
        return <Cpu className="w-3.5 h-3.5 text-fuchsia-400" />;
      default:
        return <Target className="w-3.5 h-3.5 text-cyan-400" />;
    }
  };

  const getContextBorderColor = () => {
    switch (context.context_type) {
      case "HYPOTHESIS":
        return "border-amber-500/30 bg-amber-950/20";
      case "PATHWAY":
        return "border-cyan-500/30 bg-cyan-950/20";
      case "CONNECTION":
        return "border-purple-500/30 bg-purple-950/20";
      case "KNOWLEDGE_GAP":
        return "border-rose-500/30 bg-rose-950/20";
      case "DOMAIN_ATTRIBUTION":
        return "border-teal-500/30 bg-teal-950/20";
      case "STAGE":
        return "border-blue-500/30 bg-blue-950/20";
      case "REASONING_CORE":
        return "border-fuchsia-500/30 bg-fuchsia-950/20";
      default:
        return "border-cyan-500/30 bg-cyan-950/20";
    }
  };

  return (
    <div
      className={`mx-3 my-2 p-2.5 rounded-lg border flex items-start justify-between gap-3 ${getContextBorderColor()}`}
      data-testid="zaki-selected-context-card"
    >
      <div className="flex items-start gap-2 min-w-0">
        <div className="mt-0.5 p-1 rounded bg-slate-900/60 border border-slate-700/50 shrink-0">
          {getContextIcon()}
        </div>
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] uppercase font-mono font-bold tracking-wider px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
              {context.context_type.replace(/_/g, " ")}
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              {context.context_id}
            </span>
            {context.status && (
              <span className="text-[9px] uppercase font-mono px-1 rounded bg-slate-900 text-cyan-400 border border-slate-700">
                {context.status}
              </span>
            )}
          </div>
          <p className="text-xs font-semibold text-slate-200 mt-1 truncate">
            {context.display_name}
          </p>
          {context.summary && (
            <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">
              {context.summary}
            </p>
          )}
        </div>
      </div>

      <button
        onClick={onClear}
        className="p-1 rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-800/80 transition shrink-0"
        title="Clear Selected Context"
        aria-label="Clear Selected Context"
        data-testid="zaki-clear-context-btn"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
