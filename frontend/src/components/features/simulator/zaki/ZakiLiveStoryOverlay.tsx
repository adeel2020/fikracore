"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  ChevronUp,
  ChevronDown,
  Sparkles,
  AlertTriangle,
  Target,
  Activity,
  Layers,
  CheckCircle2,
  Play,
  Pause,
  RotateCcw,
  Radio,
  Network,
  Cpu,
  ShieldCheck,
  Server,
  HelpCircle,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { renderStyledMessage } from "@/app/simulator/investigate/lib";

export interface NocActivityItem {
  id?: string;
  timestamp?: string;
  agent: "IP_TRANSPORT" | "PS_CORE" | "RAN" | "ZAKI" | "OSS_MANAGEMENT" | "SECURITY" | "CLOUD_INFRA" | string;
  domain?: string;
  action: string;
  detail?: string;
  status?: "OBSERVED" | "ANALYZING" | "VALIDATED" | "EXECUTING" | "RESOLVED" | "BLOCKED" | string;
}

interface BlastRadiusEntity {
  entity?: string;
  role?: string;
  status?: string;
  impact_level?: string;
}

interface RootCauseInfo {
  entity?: string;
  condition?: string;
  confidence?: number;
  status?: string;
}

export interface ZakiLiveStoryOverlayProps {
  storyContext: Record<string, unknown> | null | undefined;
  currentStage?: string;
  stageIndex?: number;
  stageStatus?: string;
  isRunning?: boolean;
  terminalState?: string;
  runStatus?: string;
  onAdvanceStage?: () => Promise<void> | void;
  onExecuteAction?: (actionId: string) => Promise<void> | void;
  onQuestionClick?: (question: string) => void;
  className?: string;
}

export function ZakiLiveStoryOverlay({
  storyContext,
  currentStage = "UNKNOWN",
  stageIndex = 0,
  stageStatus = "RUNNING",
  isRunning = false,
  terminalState,
  runStatus,
  onAdvanceStage,
  onExecuteAction,
  onQuestionClick,
  className,
}: ZakiLiveStoryOverlayProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const [isExecutingAction, setIsExecutingAction] = useState(false);

  // Extract story context fields
  const summary = (storyContext?.executive_summary as string) || (storyContext?.title as string) || "";
  const rootCause = (storyContext?.root_cause as RootCauseInfo | undefined);
  const blastRadius = (storyContext?.blast_radius as BlastRadiusEntity[] | undefined) || [];
  const causalChain = (storyContext?.causal_chain as string[] | undefined) || [];
  const stage = (storyContext?.stage as string) || currentStage;
  const severity = (storyContext?.severity as string) || "INFO";

  const anchorQuestion = (storyContext?.anchor_question as string) || "";
  const suggestedQuestions = (storyContext?.suggested_questions as string[]) || [];

  // NOC Common Room multi-agent activity stream (100% Dynamic & Telemetry Derived)
  const rawActivities = (storyContext?.activity_stream || storyContext?.noc_activities || storyContext?.agent_activities) as NocActivityItem[] | undefined;
  const activityStream: NocActivityItem[] = rawActivities && rawActivities.length > 0 ? rawActivities : [];

  // Decoupled stage advancement: advances cleanly without artificial delays
  const handlePacedStageAdvance = async () => {
    if (isAdvancing) return;
    setIsAdvancing(true);
    console.log("[ZakiLiveStoryOverlay] Advancing stage...");
    try {
      if (onAdvanceStage) {
        await onAdvanceStage();
      }
    } catch (err) {
      console.warn("handlePacedStageAdvance error:", err);
    } finally {
      setIsAdvancing(false);
    }
  };

  // Audio and flash notifications are disabled while simulation is running.
  // Communication is handled exclusively by Zaki in operational context.
  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  }, [isRunning, stage]);

  // If there's no story context at all, hide
  if (!storyContext && !isRunning) {
    return null;
  }

  // -------------------------------------------------------------------------
  // Collapsed Pill View
  // -------------------------------------------------------------------------
  if (!isExpanded) {
    return (
      <div
        className={cn(
          "fixed bottom-6 right-60 z-40 transition-all duration-300",
          className
        )}
      >
        <button
          type="button"
          onClick={() => setIsExpanded(true)}
          className={cn(
            "flex items-center gap-2.5 rounded-full px-4 py-2 text-xs font-medium text-white shadow-xl backdrop-blur-xl border transition-all hover:scale-105",
            isRunning
              ? "border-cyan-400/40 bg-slate-900/90 shadow-cyan-500/20"
              : "border-white/15 bg-slate-900/80 shadow-black/40"
          )}
        >
          <div className="relative flex items-center justify-center">
            <Sparkles className="h-3.5 w-3.5 text-cyan-300" />
            {isRunning && (
              <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
              </span>
            )}
          </div>
          <span className="font-semibold text-neutral-100">Live Story</span>
          <span className="rounded-full bg-cyan-500/20 px-2 py-0.5 text-[10px] font-mono text-cyan-300 uppercase">
            {stage}
          </span>
          {stageStatus === "BLOCKED" && (
            <span className="rounded-full bg-amber-500/20 border border-amber-400/40 px-1.5 py-0.2 text-[9px] font-mono text-amber-300 font-bold animate-pulse">
              ACTION REQUIRED
            </span>
          )}
          <ChevronUp className="h-3.5 w-3.5 text-neutral-400 ml-1" />
        </button>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Expanded HUD Card View
  // -------------------------------------------------------------------------
  return (
    <div
      className={cn(
        "fixed bottom-6 right-60 z-40 w-96 max-h-[520px] rounded-2xl border border-white/15 bg-slate-950/90 shadow-2xl backdrop-blur-2xl text-xs text-neutral-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-200",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 bg-white/[0.03]">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-cyan-500/20 p-1.5 text-cyan-300">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h4 className="font-bold text-white tracking-wide">Live Incident Story</h4>
            <div className="flex items-center gap-1.5 text-[10px] text-neutral-400">
              <span>Stage:</span>
              <span className="font-mono font-semibold text-cyan-300 uppercase">{stage}</span>
              {severity && (
                <>
                  <span>•</span>
                  <span className={cn(
                    "font-semibold uppercase",
                    severity === "CRITICAL" ? "text-rose-400" : severity === "MAJOR" ? "text-amber-400" : "text-cyan-400"
                  )}>
                    {severity}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setIsExpanded(false)}
            className="rounded-lg p-1.5 text-neutral-400 hover:bg-white/10 hover:text-white transition-colors"
          >
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {/* Executive Summary Narrative */}
        {summary ? (
          <div className="rounded-xl border border-white/10 bg-slate-950/60 p-3">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5 select-none">
              Operational Narrative
            </div>
            <div className="leading-relaxed">
              {renderStyledMessage(summary, false)}
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 text-center text-neutral-400">
            <Activity className="h-5 w-5 mx-auto mb-2 text-cyan-400 animate-pulse" />
            <span>Awaiting simulation telemetry for this stage...</span>
          </div>
        )}

        {/* Contextual Guidance & Interrogative Drill-Down */}
        {(anchorQuestion || suggestedQuestions.length > 0) && (
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-indigo-300">
                <HelpCircle className="h-3.5 w-3.5 text-indigo-400" />
                Contextual Insight & Follow-up
              </span>
              <span className="text-[9px] font-mono text-indigo-300/80 bg-indigo-950/60 px-1.5 py-0.5 rounded border border-indigo-800/40">
                Guided Inquiry
              </span>
            </div>
            {anchorQuestion && (
              <p className="text-white text-xs font-medium leading-snug">
                {anchorQuestion}
              </p>
            )}
            {suggestedQuestions.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {suggestedQuestions.map((q, qIdx) => (
                  <button
                    key={qIdx}
                    type="button"
                    onClick={() => {
                      if (onQuestionClick) {
                        onQuestionClick(q);
                      }
                    }}
                    className="rounded-full border border-indigo-400/40 bg-indigo-500/10 hover:bg-indigo-500/25 px-2.5 py-1 text-[11px] text-indigo-200 hover:text-white transition-all text-left flex items-center gap-1 cursor-pointer"
                  >
                    <span>💬</span>
                    <span>{q}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* NOC Common Room Multi-Agent Activity Stream */}
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-cyan-400">
              <Network className="h-3 w-3 text-cyan-400" />
              NOC Common Room Activity
            </span>
            <span className="text-[9px] font-mono text-cyan-400/80 bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800/40">Multi-Agent SME Stream</span>
          </div>
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {activityStream.length === 0 ? (
              <div className="rounded-lg border border-white/5 bg-slate-900/40 p-2.5 text-center text-[11px] text-neutral-400">
                <span>Ingesting cross-domain operational telemetry...</span>
              </div>
            ) : (
              activityStream.map((act, idx) => {
                const badgeStyle =
                  act.agent === "IP_TRANSPORT"
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : act.agent === "PS_CORE"
                    ? "bg-blue-500/20 text-blue-300 border-blue-500/40"
                    : act.agent === "RAN"
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    : act.agent === "ZAKI"
                    ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40 font-bold"
                    : "bg-purple-500/20 text-purple-300 border-purple-500/40";

                return (
                  <div key={act.id || idx} className="rounded-lg border border-white/5 bg-slate-900/60 p-2 text-xs flex flex-col gap-1">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className={cn("px-1.5 py-0.5 rounded border font-mono text-[9px]", badgeStyle)}>
                        [{act.agent}]
                      </span>
                      <span className="text-neutral-400 font-mono text-[9px]">{act.timestamp}</span>
                    </div>
                    <div className="text-[11px] text-white font-medium flex items-center justify-between">
                      <span>{act.action}</span>
                      {act.status && (
                        <span className="text-[9px] font-mono text-cyan-300/80 uppercase">{act.status}</span>
                      )}
                    </div>
                    {act.detail && (
                      <p className="text-[10px] text-neutral-400 leading-snug">{act.detail}</p>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Root Cause Card if detected/confirmed */}
        {rootCause?.entity && (
          <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-3">
            <div className="flex items-center justify-between mb-1.5">
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-cyan-400">
                <Target className="h-3 w-3" />
                Root Cause Hypothesis
              </span>
              {rootCause.confidence !== undefined && (
                <span className="rounded-full bg-cyan-500/20 px-2 py-0.5 text-[10px] font-mono font-bold text-cyan-300">
                  {Math.round(rootCause.confidence * 100)}% Conf
                </span>
              )}
            </div>
            <div className="mt-1">
              <span className="[font-family:Consolas,Monaco,'Courier_New',monospace] text-xs font-semibold text-fuchsia-400 tracking-tight">
                {rootCause.entity}
              </span>
            </div>
            {rootCause.condition && (
              <p className="text-[11px] text-slate-300 mt-1 leading-snug">{rootCause.condition}</p>
            )}
          </div>
        )}

        {/* Causal Chain */}
        {causalChain.length > 0 && (
          <div className="rounded-xl border border-white/10 bg-slate-950/40 p-3 space-y-1.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 mb-1 select-none">
              Causal Propagation
            </div>
            {causalChain.map((step, idx) => (
              <div key={idx} className="flex items-start gap-2 text-[11px] text-slate-200">
                <span className="font-mono text-cyan-400 font-bold shrink-0">{idx + 1}.</span>
                <span className="flex-1 font-medium leading-relaxed">{renderStyledMessage(step, false)}</span>
              </div>
            ))}
          </div>
        )}

        {/* Blast Radius Pills */}
        {blastRadius.length > 0 && (
          <div className="space-y-1.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 select-none">
              Blast Radius ({blastRadius.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {blastRadius.map((br, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-slate-900/60 px-2 py-1 text-[10px]"
                >
                  <span className="[font-family:Consolas,Monaco,'Courier_New',monospace] text-[11px] font-semibold text-fuchsia-400 tracking-tight">
                    {br.entity}
                  </span>
                  <span className="text-slate-400 font-mono text-[9px]">({br.role || "AFFECTED"})</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info & Stage Progression */}
      <div className="border-t border-white/10 px-4 py-2.5 bg-white/[0.02] flex items-center justify-between text-[10px] text-neutral-400">
        <div className="flex items-center gap-1.5">
          <span>Source: story_context.json</span>
          <span>•</span>
          <span className="flex items-center gap-1 text-cyan-300 font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
            Zero Oracle Leakage
          </span>
        </div>
        {/* Stage gate actions or standard advance */}
        {(() => {
          const isBlocked = stageStatus === "BLOCKED";
          const isGapStage = stageIndex === 5 || stage.toUpperCase().includes("GAP");
          const isValidationStage = stageIndex === 6 || stage.toUpperCase().includes("VALIDATION");
          const isActionStage = stageIndex === 7 || stage.toUpperCase().includes("ACTION");
          const isResolved =
            terminalState === "RESOLVED" ||
            runStatus === "COMPLETED" ||
            stageStatus === "COMPLETE" ||
            stageStatus === "COMPLETED" ||
            (storyContext as { status?: string })?.status === "resolved" ||
            (storyContext as { terminal_state?: string })?.terminal_state === "RESOLVED";

          if (isBlocked && isGapStage && onExecuteAction) {
            return (
              <button
                type="button"
                onClick={async () => {
                  setIsExecutingAction(true);
                  try {
                    await onExecuteAction("NBA-001");
                  } finally {
                    setIsExecutingAction(false);
                  }
                }}
                disabled={isExecutingAction}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 disabled:opacity-50 text-white font-semibold transition text-[11px] shadow-lg shadow-cyan-500/20 cursor-pointer"
                title="Execute Next-Best Evidence action"
              >
                <Zap className={cn("h-3 w-3", isExecutingAction && "animate-spin")} />
                <span>{isExecutingAction ? "Requesting..." : "Request Evidence (NBA-001)"}</span>
              </button>
            );
          }

          if (isBlocked && isValidationStage && onExecuteAction) {
            return (
              <button
                type="button"
                onClick={async () => {
                  setIsExecutingAction(true);
                  try {
                    await onExecuteAction("HITL-001");
                  } finally {
                    setIsExecutingAction(false);
                  }
                }}
                disabled={isExecutingAction}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white font-semibold transition text-[11px] shadow-lg shadow-emerald-500/20 cursor-pointer"
                title="Approve Human-in-the-Loop Validation"
              >
                <ShieldCheck className={cn("h-3 w-3", isExecutingAction && "animate-spin")} />
                <span>{isExecutingAction ? "Validating..." : "Approve HITL Validation"}</span>
              </button>
            );
          }

          if (isActionStage) {
            if (isResolved) {
              return (
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 font-semibold text-[11px]">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Incident Resolved & Closed</span>
                </div>
              );
            }

            if (onExecuteAction) {
              return (
                <button
                  type="button"
                  onClick={async () => {
                    setIsExecutingAction(true);
                    try {
                      await onExecuteAction("ACT-001");
                    } finally {
                      setIsExecutingAction(false);
                    }
                  }}
                  disabled={isExecutingAction}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white font-semibold transition text-[11px] shadow-lg shadow-purple-500/20 cursor-pointer"
                  title="Execute Remediation Playbook (NBA)"
                >
                  <Zap className={cn("h-3 w-3", isExecutingAction && "animate-spin")} />
                  <span>{isExecutingAction ? "Executing..." : "Execute Remediation (ACT-001)"}</span>
                </button>
              );
            }
          }

          if (onAdvanceStage && stageIndex < 7 && !stage.toUpperCase().includes("ACTION")) {
            return (
              <button
                type="button"
                onClick={handlePacedStageAdvance}
                disabled={isAdvancing}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium transition text-[11px]"
                title="Advance simulation stage"
              >
                {isAdvancing ? <Pause className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
                <span>Advance Stage</span>
              </button>
            );
          }

          return null;
        })()}
      </div>
    </div>
  );
}

export default ZakiLiveStoryOverlay;
