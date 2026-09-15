"use client";

import React from "react";

export type ZakiResponseLevel = "executive" | "operator" | "engineer" | "deep";

export interface ZakiResponseLevelSwitcherProps {
  currentLevel: ZakiResponseLevel;
  onChange: (level: ZakiResponseLevel) => void;
  disabled?: boolean;
}

export function ZakiResponseLevelSwitcher({
  currentLevel,
  onChange,
  disabled = false,
}: ZakiResponseLevelSwitcherProps) {
  const levels: Array<{ id: ZakiResponseLevel; label: string; tooltip: string }> = [
    { id: "executive", label: "Executive", tooltip: "High-level service impact and domain summary" },
    { id: "operator", label: "Operator", tooltip: "Immediate next actions and mitigation posture" },
    { id: "engineer", label: "Engineer", tooltip: "Detailed causal explanations and evidence grounding" },
    { id: "deep", label: "Deep Tech", tooltip: "Protocol-level, telemetry invariants and guardrail checks" },
  ];

  return (
    <div
      className="flex items-center gap-1 p-0.5 rounded-lg bg-slate-900 border border-slate-800"
      role="radiogroup"
      aria-label="Response Level Switcher"
      data-testid="zaki-response-level-switcher"
    >
      {levels.map((lvl) => {
        const active = currentLevel.toLowerCase() === lvl.id;
        return (
          <button
            key={lvl.id}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={disabled}
            onClick={() => onChange(lvl.id)}
            title={lvl.tooltip}
            className={`px-2 py-1 text-[10px] font-medium font-mono rounded transition-all ${
              active
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent"
            } disabled:opacity-50`}
            data-testid={`zaki-level-btn-${lvl.id}`}
          >
            {lvl.label}
          </button>
        );
      })}
    </div>
  );
}
