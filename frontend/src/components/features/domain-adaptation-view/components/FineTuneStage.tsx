"use client";

import React from "react";
import {
  Sparkles,
  Sliders,
  Loader2,
  Play,
  Terminal,
  Check,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, glassSurfaceStatic } from "@/lib/utils";
import { SftTrainStatus } from "@/lib/api/sft";
import { METHODS } from "../types/domain-adaptation.types";

const iconStroke = { strokeWidth: 1.5 } as const;

interface FineTuneStageProps {
  activeMethod: "corda" | "pissa";
  setActiveMethod: (method: "corda" | "pissa") => void;
  lr: number;
  setLr: (lr: number) => void;
  epochs: number;
  setEpochs: (epochs: number) => void;
  microBatchSize: number;
  setMicroBatchSize: (size: number) => void;
  gradAccum: number;
  setGradAccum: (steps: number) => void;
  loraR: number;
  setLoraR: (r: number) => void;
  loraAlpha: number;
  setLoraAlpha: (alpha: number) => void;
  maxSeqLen: number;
  setMaxSeqLen: (len: number) => void;
  loadingConfig: boolean;
  submittingConfig: boolean;
  handleSaveConfig: () => void;
  trainStatus: SftTrainStatus | null;
  stoppingTraining: boolean;
  handleStopTraining: () => void;
  logConsoleRef: React.RefObject<HTMLPreElement | null>;
  copiedLogs: boolean;
  handleCopyLogs: () => void;
  startingTraining: boolean;
  handleStartTraining: () => void;
}

export function FineTuneStage({
  activeMethod,
  setActiveMethod,
  lr,
  setLr,
  epochs,
  setEpochs,
  microBatchSize,
  setMicroBatchSize,
  gradAccum,
  setGradAccum,
  loraR,
  setLoraR,
  loraAlpha,
  setLoraAlpha,
  maxSeqLen,
  setMaxSeqLen,
  loadingConfig,
  submittingConfig,
  handleSaveConfig,
  trainStatus,
  stoppingTraining,
  handleStopTraining,
  logConsoleRef,
  copiedLogs,
  handleCopyLogs,
  startingTraining,
  handleStartTraining,
}: FineTuneStageProps) {
  // Duration parser
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}m ${s}s`;
  };

  return (
    <div className="space-y-6">
      {/* Method Comparison Cards */}
      <GlassCard className="p-6" hover={false}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Fine-tune</h3>
            <p className="text-xs text-neutral-400 mt-0.5">
              Select a domain adaptation mathematical method for training
            </p>
          </div>
          <Badge variant="default" className="font-mono">
            TinyLlama-1.1B Base Model
          </Badge>
        </div>

        <div className="grid gap-4 md:grid-cols-2 mt-6">
          {METHODS.map((method) => {
            const active = activeMethod === method.id;
            const Icon = method.icon;
            const isCorda = method.id === "corda";
            return (
              <button
                key={method.id}
                type="button"
                onClick={() => setActiveMethod(method.id as "corda" | "pissa")}
                className={cn(
                  glassSurfaceStatic,
                  "rounded-2xl p-6 text-left transition-all duration-300 border border-white/5 relative overflow-hidden group",
                  active
                    ? isCorda
                      ? "border-cyan-500/50 shadow-[0_0_24px_rgba(0,229,255,0.12)] bg-cyan-500/[0.02]"
                      : "border-fuchsia-500/50 shadow-[0_0_24px_rgba(240,46,170,0.12)] bg-fuchsia-500/[0.02]"
                    : "hover:border-white/10 hover:bg-white/[0.01]"
                )}
              >
                <div
                  className={cn(
                    "absolute top-0 right-0 w-24 h-24 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-2xl",
                    isCorda ? "from-cyan-500/10" : "from-fuchsia-500/10"
                  )}
                />
                <div className="flex items-start justify-between gap-3 relative z-10">
                  <div
                    className={cn(
                      "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-black/40",
                      active &&
                        (isCorda
                          ? "border-cyan-500/30 text-cyan-400"
                          : "border-fuchsia-500/30 text-fuchsia-400")
                    )}
                  >
                    <Icon
                      className={cn("h-5 w-5", active ? "" : "text-neutral-400")}
                      {...iconStroke}
                    />
                  </div>
                  <Badge variant={method.badgeVariant}>{method.tagline}</Badge>
                </div>
                <p className="mt-4 text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                  {method.name}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-neutral-400 h-14 overflow-hidden">
                  {method.description}
                </p>
                <ul className="mt-4 space-y-1.5 border-t border-white/5 pt-4">
                  {method.highlights.map((item) => (
                    <li
                      key={item}
                      className="text-[11px] text-neutral-400 flex items-center gap-1.5"
                    >
                      <span
                        className={cn(
                          "w-1 h-1 rounded-full",
                          isCorda ? "bg-cyan-400" : "bg-fuchsia-400"
                        )}
                      />
                      {item}
                    </li>
                  ))}
                </ul>
                {active && (
                  <span
                    className={cn(
                      "mt-4 inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider",
                      isCorda ? "text-cyan-400" : "text-fuchsia-400"
                    )}
                  >
                    <Check className="w-3.5 h-3.5" /> Selected Approach
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </GlassCard>

      {/* Hyperparameters Configurator */}
      <GlassCard className="p-6 relative" hover={false}>
        <div className="absolute top-0 right-0 w-40 h-40 bg-cyan-500/5 blur-3xl rounded-full" />
        <div className="flex items-center gap-2 mb-6">
          <Sliders className="h-4 w-4 text-cyan-400" />
          <h3 className="text-base font-semibold text-white">
            Hyperparameter Configuration
          </h3>
          {loadingConfig && (
            <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
          )}
        </div>

        <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-4">
          <div>
            <label className="mb-1.5 block text-[10px] font-semibold text-neutral-300 uppercase tracking-wider">
              Learning Rate
            </label>
            <input
              type="number"
              step="0.00001"
              value={lr}
              onChange={(e) => setLr(parseFloat(e.target.value))}
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[10px] font-semibold text-neutral-300 uppercase tracking-wider">
              Epochs
            </label>
            <input
              type="number"
              value={epochs}
              onChange={(e) => setEpochs(parseInt(e.target.value))}
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[10px] font-semibold text-neutral-300 uppercase tracking-wider">
              Micro-Batch Size
            </label>
            <input
              type="number"
              value={microBatchSize}
              onChange={(e) => setMicroBatchSize(parseInt(e.target.value))}
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[10px] font-semibold text-neutral-300 uppercase tracking-wider">
              Gradient Accumulation
            </label>
            <input
              type="number"
              value={gradAccum}
              onChange={(e) => setGradAccum(parseInt(e.target.value))}
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[10px] font-semibold text-neutral-300 uppercase tracking-wider">
              LoRA Rank (r)
            </label>
            <input
              type="number"
              value={loraR}
              onChange={(e) => setLoraR(parseInt(e.target.value))}
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[10px] font-semibold text-neutral-300 uppercase tracking-wider">
              LoRA Alpha
            </label>
            <input
              type="number"
              value={loraAlpha}
              onChange={(e) => setLoraAlpha(parseInt(e.target.value))}
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[10px] font-semibold text-neutral-300 uppercase tracking-wider">
              Max Sequence Length
            </label>
            <input
              type="number"
              value={maxSeqLen}
              onChange={(e) => setMaxSeqLen(parseInt(e.target.value))}
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white focus:border-cyan-500"
            />
          </div>
          <div className="flex items-end">
            <Button
              onClick={handleSaveConfig}
              disabled={submittingConfig}
              variant="outline"
              className="w-full border-white/10 bg-white/5 text-white hover:bg-white/10"
            >
              {submittingConfig ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin text-cyan-400" />
                  Saving...
                </>
              ) : (
                "Apply parameters"
              )}
            </Button>
          </div>
        </div>
      </GlassCard>

      {/* ACTIVE RUNNING STATUS DASHBOARD */}
      {trainStatus && trainStatus.state !== "IDLE" && (
        <GlassCard
          className="p-6 border-cyan-500/20 bg-cyan-950/5 relative overflow-hidden"
          hover={false}
        >
          <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-cyan-500/5 to-transparent blur-3xl" />
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6 z-10 relative">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
                <h4 className="text-base font-bold text-white uppercase tracking-wider">
                  Active Training Loop:{" "}
                  {trainStatus.method?.toUpperCase() || "Engine"}
                </h4>
              </div>
              <p className="text-xs text-neutral-400 mt-1">
                State:{" "}
                <span className="text-cyan-400 font-semibold">
                  {trainStatus.state}
                </span>{" "}
                · Isolated Process
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Button
                onClick={handleStopTraining}
                disabled={stoppingTraining}
                className="border-rose-500/30 bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 hover:border-rose-500/40 h-9 text-xs font-semibold px-3.5 rounded-xl flex items-center gap-1.5 transition-all shadow-[0_0_12px_rgba(244,63,94,0.05)]"
                variant="outline"
              >
                {stoppingTraining ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-rose-400" />
                )}
                Stop Pipeline
              </Button>
              <div className="text-right">
                <p className="text-[10px] text-neutral-400 uppercase font-semibold">
                  Elapsed Time
                </p>
                <p className="text-lg font-mono font-semibold text-white mt-0.5">
                  {formatTime(trainStatus.elapsed_time_sec)}
                </p>
              </div>
            </div>
          </div>

          {/* Progress metrics */}
          <div className="grid gap-4 sm:grid-cols-4 mb-6 z-10 relative">
            <div className="bg-black/40 border border-white/5 rounded-xl p-4">
              <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                Epoch Progress
              </span>
              <div className="mt-2 flex items-baseline gap-1.5">
                <span className="text-2xl font-bold text-white">
                  {trainStatus.epochs_completed}
                </span>
                <span className="text-xs text-neutral-500">
                  / {trainStatus.total_epochs}
                </span>
              </div>
              <div className="h-1.5 w-full bg-neutral-800 rounded-full mt-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400 transition-all duration-500"
                  style={{
                    width: `${Math.min(
                      100,
                      (trainStatus.epochs_completed / trainStatus.total_epochs) *
                        100
                    )}%`,
                  }}
                />
              </div>
            </div>

            <div className="bg-black/40 border border-white/5 rounded-xl p-4">
              <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                Training Loss
              </span>
              <p className="mt-2 text-2xl font-bold text-white">
                {trainStatus.current_loss !== null
                  ? trainStatus.current_loss.toFixed(4)
                  : "—"}
              </p>
              <p className="text-[10px] text-neutral-500 mt-3 flex items-center gap-1">
                <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                Cross entropy loss
              </p>
            </div>

            <div className="bg-black/40 border border-white/5 rounded-xl p-4">
              <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                Gradient Norm
              </span>
              <p className="mt-2 text-2xl font-bold text-white">
                {trainStatus.current_grad_norm !== null
                  ? trainStatus.current_grad_norm.toFixed(3)
                  : "—"}
              </p>
              <p className="text-[10px] text-neutral-500 mt-3">
                Parameter delta norm
              </p>
            </div>

            <div className="bg-black/40 border border-white/5 rounded-xl p-4">
              <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                ETA Remaining
              </span>
              <p className="mt-2 text-2xl font-bold text-white">
                {trainStatus.eta_sec !== null
                  ? formatTime(trainStatus.eta_sec)
                  : "Estimating..."}
              </p>
              <p className="text-[10px] text-neutral-500 mt-3">
                Dynamic step extrapolation
              </p>
            </div>
          </div>

          {/* Console log outputs */}
          <div className="z-10 relative group">
            <div className="flex items-center justify-between mb-2 px-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-neutral-300 flex items-center gap-1.5">
                <Terminal className="h-4 w-4 text-cyan-400" /> STDOUT CONSOLE
              </span>
              <span className="text-[10px] text-neutral-500 font-mono">
                logs.json telemetry format
              </span>
            </div>
            <div className="relative">
              <pre
                ref={logConsoleRef}
                className="h-60 overflow-y-auto rounded-xl border border-white/10 bg-black/90 p-4 font-mono text-[11px] leading-relaxed text-cyan-300/80 scrollbar-thin scrollbar-thumb-cyan-500/20 pr-12"
              >
                {trainStatus.logs.length > 0
                  ? trainStatus.logs.join("")
                  : "Initialising training subprocess threads...\n"}
              </pre>

              {trainStatus && trainStatus.logs.length > 0 && (
                <button
                  onClick={handleCopyLogs}
                  title="Copy console logs"
                  className="absolute top-3 right-3 p-1.5 rounded-lg border border-white/10 bg-black/60 text-neutral-400 hover:text-white hover:bg-black/85 hover:border-cyan-500/40 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-all duration-200 z-20 shadow-md flex items-center justify-center cursor-pointer"
                >
                  {copiedLogs ? (
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                  ) : (
                    <svg
                      className="h-3.5 w-3.5"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                  )}
                </button>
              )}
            </div>
          </div>
        </GlassCard>
      )}

      {/* Action Trigger Buttons */}
      {(!trainStatus ||
        trainStatus.state === "IDLE" ||
        trainStatus.state === "COMPLETED" ||
        trainStatus.state === "FAILED") && (
        <div className="flex items-center gap-4">
          <Button
            className="gap-2 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-semibold shadow-lg px-6 py-5 text-sm rounded-xl"
            onClick={handleStartTraining}
            disabled={startingTraining}
          >
            {startingTraining ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" /> Starting Process...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" /> Initiate SFT Pipeline
              </>
            )}
          </Button>
          {trainStatus?.state === "FAILED" && (
            <div className="flex items-center gap-2 text-rose-400 text-xs">
              <AlertCircle className="w-4 h-4" />
              <span>
                {trainStatus.error_message ||
                  "Execution thread crashed. Check console."}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
