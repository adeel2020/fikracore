"use client";

import React from "react";
import { Bot, Sparkles, AlertCircle } from "lucide-react";

export interface ZakiCompactOrbProps {
  isOpen: boolean;
  onToggle: () => void;
  copilotState?: string;
  isThinking?: boolean;
  hasConflict?: boolean;
  selectedContextName?: string;
}

export function ZakiCompactOrb({
  isOpen,
  onToggle,
  copilotState = "IDLE",
  isThinking = false,
  hasConflict = false,
  selectedContextName,
}: ZakiCompactOrbProps) {
  // Glow style based on visual semantics:
  // Cyan: operational structure / normal
  // Magenta: focus / attention / thinking
  // Turquoise: confirmed / ready
  // Amber / Rose: conflict
  const glowColor = hasConflict
    ? "from-amber-500/30 to-rose-500/40 border-rose-500/50 text-rose-400"
    : isThinking || copilotState === "NEEDS_EVIDENCE"
    ? "from-fuchsia-500/30 to-pink-500/40 border-fuchsia-500/50 text-fuchsia-400"
    : copilotState === "VALIDATION_REQUIRED" || copilotState === "RECOMMENDATION_READY"
    ? "from-teal-500/30 to-emerald-500/40 border-teal-500/50 text-teal-300"
    : "from-cyan-500/30 to-blue-500/40 border-cyan-500/50 text-cyan-300";

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onToggle();
      }}
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-3.5 py-2.5 rounded-full shadow-2xl backdrop-blur-xl border transition-all duration-300 group hover:scale-105 pointer-events-auto cursor-pointer ${
        isOpen
          ? "bg-slate-900/90 border-slate-700 text-slate-300"
          : `bg-gradient-to-r ${glowColor}`
      }`}
      aria-label="Toggle Zaki Copilot"
      data-testid="zaki-compact-orb"
    >
      <div className="relative flex items-center justify-center">
        {hasConflict ? (
          <AlertCircle className="w-5 h-5 text-rose-400 animate-pulse" />
        ) : isThinking ? (
          <Sparkles className="w-5 h-5 animate-spin text-fuchsia-400" />
        ) : (
          <Bot className="w-5 h-5 text-cyan-400 group-hover:text-cyan-300" />
        )}
        {!isOpen && (
          <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                hasConflict ? "bg-rose-400" : "bg-cyan-400"
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                hasConflict ? "bg-rose-500" : "bg-cyan-500"
              }`}
            />
          </span>
        )}
      </div>

      <div className="flex flex-col items-start pr-1">
        <span className="text-xs font-semibold tracking-wide flex items-center gap-1.5">
          ZAKI 2.0
          {copilotState && copilotState !== "IDLE" && (
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-400">
              {copilotState}
            </span>
          )}
        </span>
        {selectedContextName && !isOpen && (
          <span className="text-[10px] text-cyan-400/80 max-w-[140px] truncate font-mono">
            {selectedContextName}
          </span>
        )}
      </div>
    </button>
  );
}
