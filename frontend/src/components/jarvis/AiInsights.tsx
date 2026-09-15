"use client";

import React from "react";
import dynamic from "next/dynamic";
import {
  Brain,
  AlertTriangle,
  TrendingDown,
  ShieldCheck,
  CircleDot,
  MoreHorizontal,
} from "lucide-react";

const ThreeNeuralSphere = dynamic(
  () => import("./ThreeNeuralSphere").then((mod) => mod.ThreeNeuralSphere),
  { ssr: false }
);

const INSIGHTS = [
  { label: "Anomaly Detection", sub: "3 Anomalies Detected", icon: AlertTriangle, color: "text-rose-500", bg: "bg-rose-50 dark:bg-rose-950/50" },
  { label: "Performance Prediction", sub: "2 Degradations Predicted", icon: TrendingDown, color: "text-orange-500", bg: "bg-orange-50 dark:bg-orange-950/50" },
  { label: "Root Cause Analysis", sub: "5 RCA Suggestions", icon: ShieldCheck, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-950/50" },
  { label: "Capacity Planning", sub: "12 Sites Requiring Attention", icon: CircleDot, color: "text-blue-600 dark:text-cyan-400", bg: "bg-blue-50 dark:bg-cyan-950/50" },
];

export function AiInsights() {
  return (
    <div className="flex flex-col gap-3 h-full">
      {/* 1. Header */}
      <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/15 text-[#00e5ff] flex items-center justify-center border border-cyan-400/35 shadow-[0_0_10px_rgba(0,229,255,0.2)]">
            <Brain className="w-4 h-4" strokeWidth={2.2} />
          </div>
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 leading-tight">
              AI COGNITIVE INSIGHTS
            </h3>
            <p className="font-mono text-[9px] text-cyan-400/70">
              Deterministic RAG • Autopilot • Neural Spine
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-950/50 border border-cyan-500/30 text-[9px] font-mono text-cyan-300">
          <span>LLM ACTIVE</span>
        </div>
      </div>

      {/* 2. Neural Visualizer & Model State */}
      <div className="grid grid-cols-[1fr_105px] gap-2.5 p-2.5 rounded-xl bg-[#030914]/80 border border-cyan-500/20 items-center shrink-0">
        <div className="flex flex-col gap-1 font-mono text-[9px]">
          <span className="text-cyan-300 font-bold uppercase tracking-wide">
            Model Context Status
          </span>
          <p className="text-slate-300 text-[8.5px] leading-relaxed">
            Telecom gbrain graph grounding live inference with Zero-Hallucination deterministic guardrails.
          </p>
          <div className="flex items-center gap-2 mt-0.5 text-[8px] text-slate-400">
            <span>RAG Context: <strong className="text-[#00e5ff]">4.2k tokens</strong></span>
            <span>Latency: <strong className="text-emerald-400">220ms</strong></span>
          </div>
        </div>

        {/* 3D Volumetric Neural Sphere */}
        <div className="relative w-[95px] h-[95px] mx-auto rounded-xl bg-[#020712] border border-cyan-500/30 overflow-hidden flex items-center justify-center shadow-inner">
          <ThreeNeuralSphere width={95} height={95} />
        </div>
      </div>

      {/* 3. Predictive Insights List */}
      <div className="flex flex-col gap-1.5 flex-1 min-h-0">
        <div className="flex items-center justify-between px-0.5">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300">
            Cognitive Predictions
          </span>
          <span className="font-mono text-[9px] text-cyan-400">
            High Confidence
          </span>
        </div>

        <div className="flex flex-col gap-1.5 overflow-y-auto jarvis-scrollbar pr-1">
          {INSIGHTS.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.label}
                className="p-2 rounded-lg bg-[#030914]/80 border border-cyan-500/20 hover:border-cyan-400/40 transition-all flex items-center gap-2"
              >
                <div className={`w-6 h-6 rounded-md ${item.bg} border border-cyan-500/20 flex items-center justify-center shrink-0`}>
                  <Icon className={`w-3.5 h-3.5 ${item.color}`} strokeWidth={2.2} />
                </div>
                <div className="flex-1 min-w-0 font-mono">
                  <span className="text-[9.5px] font-bold text-slate-100 block leading-tight truncate">
                    {item.label}
                  </span>
                  <span className="text-[8.5px] text-cyan-400/70 block mt-0.5 truncate">
                    {item.sub}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Footer Autopilot Summary */}
      <div className="p-2 rounded-xl bg-cyan-950/30 border border-cyan-500/30 flex items-center justify-between font-mono text-[9px] shrink-0">
        <span className="text-slate-300">Autopilot Decision Engine:</span>
        <span className="text-[#00e5ff] font-bold">READY FOR EXECUTION</span>
      </div>
    </div>
  );
}
