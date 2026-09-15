"use client";

import React, { useState } from "react";
import {
  Eye,
  Brain,
  CircleDot,
  FileText,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

interface PipelineStep {
  id: string;
  label: string;
  count: string;
  icon: LucideIcon;
  color: string;
  bg: string;
  detail: string;
  action: string;
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "focus",
    label: "Focus",
    count: "5 Key Domains",
    icon: Brain,
    color: "text-purple-400",
    bg: "bg-purple-950/50 border-purple-500/30",
    detail: "Prioritizing 5G Core AMF & UPF control plane anomalies.",
    action: "Active observation on Dubai North 5G cluster.",
  },
  {
    id: "correlate",
    label: "Correlate",
    count: "122 Events",
    icon: CircleDot,
    color: "text-cyan-400",
    bg: "bg-cyan-950/50 border-cyan-500/30",
    detail: "Cross-correlating DWDM Optical LOS with UPF packet drops.",
    action: "Graph correlation confidence: 94.2%.",
  },
  {
    id: "summarize",
    label: "Summarize",
    count: "12 Insights",
    icon: FileText,
    color: "text-sky-400",
    bg: "bg-sky-950/50 border-sky-500/30",
    detail: "Synthesizing blast radius and subscriber impact narrative.",
    action: "Deterministic incident story generated for SecOps.",
  },
  {
    id: "predict",
    label: "Predict",
    count: "3 Next Risks",
    icon: TrendingUp,
    color: "text-amber-400",
    bg: "bg-amber-950/50 border-amber-500/30",
    detail: "Predicting memory pressure on Secondary SMF in 18 minutes.",
    action: "Risk level: Medium (Preventative mitigation ready).",
  },
  {
    id: "suggest",
    label: "Suggest",
    count: "7 Actions",
    icon: ShieldCheck,
    color: "text-emerald-400",
    bg: "bg-emerald-950/50 border-emerald-500/30",
    detail: "Automated rerouting of critical eMBB slice to Standby Pod.",
    action: "Awaiting operator authorization or autopilot execution.",
  },
];

export function FcspsLens() {
  const [activeStepId, setActiveStepId] = useState("focus");

  const currentStep = PIPELINE_STEPS.find((s) => s.id === activeStepId) || PIPELINE_STEPS[0];
  const StepIcon = currentStep.icon;

  return (
    <div className="flex flex-col gap-3 h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/15 text-[#00e5ff] flex items-center justify-center border border-cyan-400/35 shadow-[0_0_10px_rgba(0,229,255,0.2)]">
            <Eye className="w-4 h-4" strokeWidth={2.2} />
          </div>
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 leading-tight">
              FCAPS COGNITIVE LENS
            </h3>
            <p className="font-mono text-[9px] text-cyan-400/70">
              Focus • Correlate • Summarize • Predict • Suggest
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-950/50 border border-cyan-500/30 text-[9px] font-mono text-cyan-300">
          <CheckCircle2 className="w-3 h-3 text-cyan-400" />
          <span>AUTONOMOUS</span>
        </div>
      </div>

      {/* Radar & Scan Grid */}
      <div className="grid grid-cols-[110px_1fr] gap-2.5 items-center p-2 rounded-xl bg-[#030914]/80 border border-cyan-500/20 shrink-0">
        {/* Radar Scope */}
        <div className="relative w-[100px] h-[100px] mx-auto rounded-full bg-[#020712] border border-cyan-500/40 overflow-hidden flex items-center justify-center shadow-inner">
          <div className="absolute inset-1.5 rounded-full border border-cyan-500/20" />
          <div className="absolute inset-4 rounded-full border border-cyan-400/25" />
          <div className="absolute inset-7 rounded-full border border-purple-400/30" />
          <div className="absolute inset-x-0 top-1/2 h-px bg-cyan-500/30" />
          <div className="absolute inset-y-0 left-1/2 w-px bg-cyan-500/30" />

          {/* Radar Sweep */}
          <div
            className="absolute inset-0 rounded-full radar-sweep-anim pointer-events-none"
            style={{
              background:
                "conic-gradient(from 0deg, rgba(0,229,255,0.45) 0deg, rgba(139,92,246,0.3) 45deg, transparent 120deg)",
            }}
          />

          {/* Core Node */}
          <div className="relative w-5 h-5 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 shadow-[0_0_12px_rgba(0,229,255,0.8)] flex items-center justify-center">
            <div className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
            <div className="absolute w-1 h-1 rounded-full bg-white" />
          </div>

          <div className="absolute top-3.5 right-4 w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#00e5ff]" />
          <div className="absolute bottom-4 left-3.5 w-1.5 h-1.5 rounded-full bg-rose-500 shadow-[0_0_6px_#f43f5e]" />
        </div>

        {/* Radar Status Details */}
        <div className="flex flex-col gap-1 font-mono text-[9px]">
          <span className="text-cyan-300 font-bold uppercase tracking-wide">
            Cognitive Loop State
          </span>
          <p className="text-slate-300 text-[8.5px] leading-relaxed">
            Continuous closed-loop reasoning mapping raw alarms to deterministic remediation recipes.
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-slate-400">Scan: <span className="text-emerald-400 font-bold">ACTIVE</span></span>
            <span className="text-slate-400">Latency: <span className="text-cyan-300 font-bold">12ms</span></span>
          </div>
        </div>
      </div>

      {/* 5-Stage Pipeline Selector */}
      <div className="flex flex-col gap-1.5 shrink-0">
        <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300 px-0.5">
          Cognitive Lifecycle Stages
        </span>
        <div className="flex flex-col gap-1">
          {PIPELINE_STEPS.map((step) => {
            const Icon = step.icon;
            const isSelected = activeStepId === step.id;
            return (
              <button
                key={step.id}
                onClick={() => setActiveStepId(step.id)}
                className={`flex items-center justify-between p-2 rounded-lg border transition-all cursor-pointer text-left ${
                  isSelected
                    ? "bg-cyan-500/15 border-cyan-400/50 shadow-[0_0_10px_rgba(0,229,255,0.2)]"
                    : "bg-[#030914]/70 border-cyan-500/20 hover:bg-white/5 hover:border-cyan-500/40"
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-5 h-5 rounded-md ${step.bg} border flex items-center justify-center shrink-0`}>
                    <Icon className={`w-3 h-3 ${step.color}`} strokeWidth={2.4} />
                  </div>
                  <span className="font-mono text-[10px] font-bold text-slate-100 uppercase tracking-wide">
                    {step.label}
                  </span>
                </div>
                <span className="font-mono text-[9px] font-medium text-cyan-400/80">
                  {step.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Stage Details & Suggestion */}
      <div className="flex-1 min-h-0 p-2.5 rounded-xl bg-[#030914]/80 border border-cyan-500/25 flex flex-col justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span className="font-mono text-[9.5px] font-bold uppercase tracking-wider text-cyan-300">
            {currentStep.label} Stage Analysis
          </span>
        </div>
        <p className="font-mono text-[9px] text-slate-300 leading-relaxed my-1">
          {currentStep.detail}
        </p>
        <div className="p-1.5 rounded bg-cyan-950/40 border border-cyan-500/30">
          <span className="font-mono text-[8.5px] text-cyan-200">
            Action: {currentStep.action}
          </span>
        </div>
      </div>
    </div>
  );
}
