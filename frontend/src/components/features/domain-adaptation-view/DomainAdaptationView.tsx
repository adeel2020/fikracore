"use client";

import React from "react";
import { ArrowRight, Check, ChevronRight } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { cn, glassSurfaceStatic } from "@/lib/utils";

import { useDomainAdaptation } from "./hooks/useDomainAdaptation";
import { PIPELINE_STAGES, PipelineStageId } from "./types/domain-adaptation.types";
import { PreprocessStage } from "./components/PreprocessStage";
import { EmbedStage } from "./components/EmbedStage";
import { FineTuneStage } from "./components/FineTuneStage";
import { EvaluateStage } from "./components/EvaluateStage";

const iconStroke = { strokeWidth: 1.5 } as const;

function stageIndex(stage: PipelineStageId): number {
  return PIPELINE_STAGES.findIndex((s) => s.id === stage);
}

export function DomainAdaptationView() {
  const {
    pipelineStage,
    setPipelineStage,
    autoOptimize,
    setAutoOptimize,
    datasets,
    selectedDatasetId,
    setSelectedDatasetId,
    trainStatus,
    evalResults,
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
    templateId,
    setTemplateId,
    structuredPayload,
    embedComplete,
    searchQuery,
    setSearchQuery,
    sortField,
    sortDirection,
    copiedLogs,
    loadingDatasets,
    loadingConfig,
    submittingConfig,
    startingTraining,
    stoppingTraining,
    startingEval,
    logConsoleRef,
    handleCopyLogs,
    handleStopTraining,
    handleSaveConfig,
    handleStartTraining,
    handleStartEvaluation,
    applyPreprocess,
    runEmbed,
    handleSort,
    template,
    provider,
    preprocessVars,
    preprocessPreview,
    tokenEstimate,
    sortedCategories,
  } = useDomainAdaptation();

  const currentStageIdx = stageIndex(pipelineStage);

  return (
    <div className="space-y-6">
      {/* Dynamic Stage Header Navigation */}
      <GlassCard className="p-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-40 bg-gradient-to-br from-cyan-500/10 to-transparent blur-3xl" />
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="default" className="uppercase tracking-wider text-[10px]">
                On-Prem adaptation engine
              </Badge>
              {trainStatus?.state !== "IDLE" && (
                <Badge variant="neon" className="animate-pulse">
                  {trainStatus?.state} ACTIVE
                </Badge>
              )}
            </div>
            <h3 className="text-xl font-semibold text-white mt-1.5">Domain Adaptation Pipeline</h3>
            <p className="text-xs text-neutral-400 mt-1">
              Configure, train, and validate specialized models in a secure, isolated workspace
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-neutral-400">Auto-optimize hyperparameters</span>
            <Switch checked={autoOptimize} onCheckedChange={setAutoOptimize} />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 relative z-10">
          {PIPELINE_STAGES.map((step, i) => {
            const idx = stageIndex(step.id);
            const done = idx < currentStageIdx || (step.id === "embed" && embedComplete);
            const active = step.id === pipelineStage;
            return (
              <div key={step.id} className="flex items-center gap-2">
                <button
                  onClick={() => {
                    if (idx <= currentStageIdx || done || embedComplete) {
                      setPipelineStage(step.id);
                    }
                  }}
                  className={cn(
                    glassSurfaceStatic,
                    "flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm transition-all duration-300 border border-white/5",
                    active && "border-cyan-500/40 bg-cyan-500/10 text-white font-medium shadow-[0_0_15px_rgba(6,182,212,0.15)]",
                    done && !active && "border-emerald-500/30 text-emerald-400 hover:border-emerald-500/50",
                    !active && !done && "text-neutral-500 hover:text-neutral-300 hover:border-white/10"
                  )}
                >
                  {done ? (
                    <Check className="h-3.5 w-3.5 text-emerald-400" {...iconStroke} />
                  ) : (
                    <span className="w-4 h-4 rounded-full border border-current text-[10px] flex items-center justify-center font-bold">
                      {i + 1}
                    </span>
                  )}
                  {step.label}
                </button>
                {i < PIPELINE_STAGES.length - 1 && (
                  <ChevronRight className="h-4 w-4 text-cyan-500/40" {...iconStroke} />
                )}
              </div>
            );
          })}
          <ArrowRight className="ml-2 h-4 w-4 text-neutral-600 hidden md:block" {...iconStroke} />
          <span
            className={cn(
              "text-xs ml-1 hidden md:inline-block",
              pipelineStage === "evaluate" ? "text-emerald-400" : "text-neutral-500"
            )}
          >
            {pipelineStage === "evaluate" ? "Finished" : "In Progress"}
          </span>
        </div>
      </GlassCard>

      {/* Stage 1: Preprocess */}
      {pipelineStage === "preprocess" && (
        <PreprocessStage
          loadingDatasets={loadingDatasets}
          datasets={datasets}
          selectedDatasetId={selectedDatasetId}
          setSelectedDatasetId={setSelectedDatasetId}
          templateId={templateId}
          setTemplateId={setTemplateId}
          provider={provider}
          template={template}
          preprocessPreview={preprocessPreview}
          preprocessVars={preprocessVars}
          applyPreprocess={applyPreprocess}
        />
      )}

      {/* Stage 2: Embed */}
      {pipelineStage === "embed" && structuredPayload && (
        <EmbedStage
          tokenEstimate={tokenEstimate}
          maxSeqLen={maxSeqLen}
          provider={provider}
          structuredPayload={structuredPayload}
          runEmbed={runEmbed}
        />
      )}

      {/* Stage 3: Fine-Tune */}
      {pipelineStage === "finetune" && (
        <FineTuneStage
          activeMethod={activeMethod}
          setActiveMethod={setActiveMethod}
          lr={lr}
          setLr={setLr}
          epochs={epochs}
          setEpochs={setEpochs}
          microBatchSize={microBatchSize}
          setMicroBatchSize={setMicroBatchSize}
          gradAccum={gradAccum}
          setGradAccum={setGradAccum}
          loraR={loraR}
          setLoraR={setLoraR}
          loraAlpha={loraAlpha}
          setLoraAlpha={setLoraAlpha}
          maxSeqLen={maxSeqLen}
          setMaxSeqLen={setMaxSeqLen}
          loadingConfig={loadingConfig}
          submittingConfig={submittingConfig}
          handleSaveConfig={handleSaveConfig}
          trainStatus={trainStatus}
          stoppingTraining={stoppingTraining}
          handleStopTraining={handleStopTraining}
          logConsoleRef={logConsoleRef}
          copiedLogs={copiedLogs}
          handleCopyLogs={handleCopyLogs}
          startingTraining={startingTraining}
          handleStartTraining={handleStartTraining}
        />
      )}

      {/* Stage 4: Evaluate */}
      {pipelineStage === "evaluate" && (
        <EvaluateStage
          trainStatus={trainStatus}
          evalResults={evalResults}
          startingEval={startingEval}
          handleStartEvaluation={handleStartEvaluation}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          sortField={sortField}
          sortDirection={sortDirection}
          handleSort={handleSort}
          sortedCategories={sortedCategories}
        />
      )}
    </div>
  );
}
