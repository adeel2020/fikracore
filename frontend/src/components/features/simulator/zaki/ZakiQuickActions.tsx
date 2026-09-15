"use client";

import React from "react";
import { Sparkles, ArrowRight, PlayCircle } from "lucide-react";
import type { ZakiSelectedContext } from "@/lib/simulation-store";

export interface ZakiQuickActionsProps {
  selectedContext?: ZakiSelectedContext | null;
  stageName?: string;
  suggestedActions?: Array<{
    action_id: string;
    display_name: string;
    action_type: string;
    enabled: boolean;
    target_id?: string;
  }>;
  onSelectPrompt: (prompt: string) => void;
  onExecuteAction?: (actionId: string) => void;
  disabled?: boolean;
}

export function ZakiQuickActions({
  selectedContext,
  stageName,
  suggestedActions = [],
  onSelectPrompt,
  onExecuteAction,
  disabled = false,
}: ZakiQuickActionsProps) {
  // Derive contextual quick prompts based on active selection
  const getContextPrompts = (): string[] => {
    if (!selectedContext) {
      const stage = (stageName || "").toUpperCase();
      if (stage === "TRIGGER" || stage === "STAGE_1") {
        return ["What triggered this incident?", "What initial evidence was admitted?"];
      }
      if (stage === "HYPOTHESIZE" || stage === "STAGE_2") {
        return ["Which hypotheses are active?", "Why is H1 the leading cause?"];
      }
      if (stage === "TEST" || stage === "STAGE_3") {
        return ["What evidence is missing?", "Are there knowledge gaps blocking progress?"];
      }
      if (stage === "VALIDATE" || stage === "STAGE_4") {
        return ["Is domain attribution ready?", "What confirms root cause?"];
      }
      return ["Explain current reasoning", "What is the primary domain?", "What happens next?"];
    }

    switch (selectedContext.context_type) {
      case "HYPOTHESIS":
        return [
          `Why is ${selectedContext.display_name} ranked here?`,
          `What evidence supports ${selectedContext.context_id}?`,
          `What contradicts ${selectedContext.context_id}?`,
        ];
      case "PATHWAY":
        return [
          `Explain pathway ${selectedContext.display_name}`,
          `What evidence feeds this pathway?`,
          `Which hypothesis does this pathway support?`,
        ];
      case "CONNECTION":
        return [
          `Why does this connection exist?`,
          `Is this relationship supporting or contradicting?`,
        ];
      case "KNOWLEDGE_GAP":
        return [
          `Why is ${selectedContext.display_name} a gap?`,
          `How can we close this gap?`,
          `Is this gap blocking validation?`,
        ];
      case "DOMAIN_ATTRIBUTION":
        return [
          `Why is ${selectedContext.display_name} assigned this role?`,
          `Is there an attribution conflict?`,
          `What evidence backs this domain attribution?`,
        ];
      case "STAGE":
        return [
          `What is the goal of ${selectedContext.display_name}?`,
          `What exit conditions are required?`,
          `Is this stage blocked?`,
        ];
      case "REASONING_CORE":
        return [
          "How is the reasoning core synthesizing evidence?",
          "What is the current epistemic status?",
          "Are all pathways converging?",
        ];
      default:
        return ["Explain selected object", "What supports this?"];
    }
  };

  const prompts = getContextPrompts();

  return (
    <div className="flex flex-col gap-2 px-3 py-2 border-t border-slate-800/80 bg-slate-900/30">
      {/* Context Prompts */}
      <div className="flex items-center gap-1.5 flex-wrap" data-testid="zaki-quick-prompts">
        <span className="text-[10px] uppercase font-mono text-slate-500 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-cyan-400" />
          Quick Ask:
        </span>
        {prompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(p)}
            disabled={disabled}
            className="text-[11px] px-2 py-1 rounded bg-slate-800/70 hover:bg-slate-700/80 text-slate-300 hover:text-cyan-300 border border-slate-700/60 hover:border-cyan-500/40 transition flex items-center gap-1 disabled:opacity-50"
            data-testid={`zaki-quick-prompt-${idx}`}
          >
            <span>{p}</span>
            <ArrowRight className="w-2.5 h-2.5 opacity-60" />
          </button>
        ))}
      </div>

      {/* Governed Suggested Actions from Backend */}
      {suggestedActions.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap pt-1 border-t border-slate-800/40" data-testid="zaki-suggested-actions">
          <span className="text-[10px] uppercase font-mono text-slate-500 flex items-center gap-1">
            <PlayCircle className="w-3 h-3 text-teal-400" />
            Actions:
          </span>
          {suggestedActions.map((act) => (
            <button
              key={act.action_id}
              onClick={() => onExecuteAction && onExecuteAction(act.action_id)}
              disabled={disabled || !act.enabled}
              className={`text-[11px] font-mono px-2 py-0.5 rounded border transition flex items-center gap-1 ${
                act.enabled
                  ? "bg-teal-950/40 hover:bg-teal-900/50 text-teal-300 border-teal-600/40 hover:border-teal-500"
                  : "bg-slate-900 text-slate-500 border-slate-800 cursor-not-allowed opacity-60"
              }`}
              data-testid={`zaki-suggested-action-${act.action_id}`}
            >
              <span>{act.display_name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
