"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Mic,
  Volume2,
  VolumeX,
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { jarvisVoice } from "@/lib/voice";
import { MarkVoiceNarrator } from "./MarkVoiceNarrator";

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

export interface FlashNarrationItem {
  time: string;
  phase: string;
  spoken: string;
  text?: string;
}

export interface ZakiLiveStoryOverlayProps {
  storyContext: Record<string, unknown> | null | undefined;
  currentStage?: string;
  isRunning?: boolean;
  className?: string;
}

export function ZakiLiveStoryOverlay({
  storyContext,
  currentStage = "UNKNOWN",
  isRunning = false,
  className,
}: ZakiLiveStoryOverlayProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [autoNarrate, setAutoNarrate] = useState(true);
  const lastNarratedStageRef = useRef<string | null>(null);

  // Extract story context fields
  const summary = (storyContext?.executive_summary as string) || (storyContext?.title as string) || "";
  const rootCause = (storyContext?.root_cause as RootCauseInfo | undefined);
  const blastRadius = (storyContext?.blast_radius as BlastRadiusEntity[] | undefined) || [];
  const causalChain = (storyContext?.causal_chain as string[] | undefined) || [];
  const stage = (storyContext?.stage as string) || currentStage;
  const severity = (storyContext?.severity as string) || "INFO";
  const flashNarration = (storyContext?.flash_narration as FlashNarrationItem | undefined);
  const flashHistory = (storyContext?.flash_history as FlashNarrationItem[] | undefined) || (
    flashNarration ? [flashNarration] : []
  );

  // Auto-narration trigger when flash narration advances a stage
  useEffect(() => {
    if (!autoNarrate || typeof window === "undefined" || !("speechSynthesis" in window)) {
      return;
    }
    const textToSpeak = flashNarration?.spoken || summary;
    if (!textToSpeak) return;

    const currentKey = `${stage}:${textToSpeak.slice(0, 50)}`;
    if (lastNarratedStageRef.current === currentKey) {
      return;
    }
    lastNarratedStageRef.current = currentKey;

    try {
      jarvisVoice.speak(textToSpeak);
    } catch (err) {
      console.warn("Auto-narration failed:", err);
    }
  }, [autoNarrate, stage, flashNarration, summary]);

  // Clean up speech on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

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
          {flashNarration && (
            <span className="hidden sm:inline-block max-w-[200px] truncate text-[11px] text-cyan-200/90 font-mono">
              🎙️ {flashNarration.phase}
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
            onClick={() => setAutoNarrate(!autoNarrate)}
            title={autoNarrate ? "Disable auto-narration" : "Enable auto-narration on stage advance"}
            className={cn(
              "rounded-lg p-1.5 transition-colors border",
              autoNarrate
                ? "border-cyan-400/40 bg-cyan-500/20 text-cyan-300"
                : "border-white/5 bg-white/5 text-neutral-400 hover:text-white"
            )}
          >
            {autoNarrate ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
          </button>
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
        {/* Live Flash Narration Unsolicited Feed */}
        {flashHistory.length > 0 && (
          <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-3 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-cyan-300">
                <Sparkles className="h-3 w-3 text-cyan-400" />
                Live Flash Narration
              </span>
              <span className="text-[10px] font-mono text-cyan-400/80">Unsolicited Push</span>
            </div>
            <div className="space-y-2">
              {flashHistory.map((item, idx) => {
                const isLatest = idx === flashHistory.length - 1;
                return (
                  <div
                    key={idx}
                    className={cn(
                      "rounded-lg p-2.5 transition-all border text-xs",
                      isLatest
                        ? "border-cyan-400/50 bg-cyan-500/10 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                        : "border-white/10 bg-white/[0.02] text-neutral-300 opacity-80 hover:opacity-100"
                    )}
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono text-neutral-400 mb-1">
                      <span className="font-semibold text-cyan-300">
                        At {item.time} ({item.phase})
                      </span>
                      <button
                        type="button"
                        onClick={() => jarvisVoice.speak(item.spoken)}
                        className="flex items-center gap-1 text-[10px] text-cyan-400 hover:text-cyan-200 transition-colors cursor-pointer"
                        title="Play flash narration"
                      >
                        <Volume2 className="h-3 w-3" /> Play
                      </button>
                    </div>
                    <p className="text-white font-medium flex items-start gap-1.5 leading-snug">
                      <span className="shrink-0 text-cyan-400">🎙️</span>
                      <span>"{item.spoken}"</span>
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Voice Narrator Bar */}
        {summary && (
          <MarkVoiceNarrator spokenText={flashNarration?.spoken || summary} />
        )}

        {/* Executive Summary Narrative */}
        {summary ? (
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
            <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1.5">
              Executive Narrative Beat
            </div>
            <p className="text-neutral-200 leading-relaxed text-xs">
              {summary}
            </p>
          </div>
        ) : (
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 text-center text-neutral-400">
            <Activity className="h-5 w-5 mx-auto mb-2 text-cyan-400 animate-pulse" />
            <span>Awaiting simulation telemetry for this stage...</span>
          </div>
        )}

        {/* Root Cause Card if detected/confirmed */}
        {rootCause?.entity && (
          <div className="rounded-xl border border-teal-500/30 bg-teal-950/30 p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-teal-300">
                <Target className="h-3 w-3" />
                Root Cause Hypothesis
              </span>
              {rootCause.confidence !== undefined && (
                <span className="rounded-full bg-teal-500/20 px-2 py-0.5 text-[10px] font-mono font-bold text-teal-200">
                  {Math.round(rootCause.confidence * 100)}% Conf
                </span>
              )}
            </div>
            <p className="font-semibold text-white text-xs">{rootCause.entity}</p>
            {rootCause.condition && (
              <p className="text-[11px] text-teal-200/80 mt-0.5">{rootCause.condition}</p>
            )}
          </div>
        )}

        {/* Causal Chain */}
        {causalChain.length > 0 && (
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 space-y-1.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">
              Causal Propagation
            </div>
            {causalChain.map((step, idx) => (
              <div key={idx} className="flex items-start gap-2 text-[11px] text-neutral-300">
                <span className="font-mono text-cyan-400 shrink-0">{idx + 1}.</span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        )}

        {/* Blast Radius Pills */}
        {blastRadius.length > 0 && (
          <div className="space-y-1.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
              Blast Radius ({blastRadius.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {blastRadius.map((br, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-[10px] font-mono text-neutral-300"
                >
                  <span className="font-semibold text-white">{br.entity}</span>
                  <span className="text-neutral-400">({br.role || "AFFECTED"})</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="border-t border-white/10 px-4 py-2 bg-white/[0.02] flex items-center justify-between text-[10px] text-neutral-400">
        <span>Source: operational/story_context.json</span>
        <span className="flex items-center gap-1 text-cyan-300 font-mono">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
          Zero Oracle Leakage
        </span>
      </div>
    </div>
  );
}

export default ZakiLiveStoryOverlay;
