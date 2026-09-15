"use client";

import React from "react";
import {
  X,
  Workflow,
  Eye,
  Database,
  Bot,
  TrendingUp,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";

interface OrbDetailModalProps {
  orbId: string | null;
  onClose: () => void;
  onRunAction?: (actionText: string) => void;
}

const ORB_DETAILS: Record<
  string,
  {
    title: string;
    subtitle: string;
    icon: typeof Workflow;
    description: string;
    stats: { label: string; value: string }[];
    actions: string[];
    telecomEntities: string[];
  }
> = {
  correlation: {
    title: "Correlation Engine",
    subtitle: "Real-time Multi-Domain Event & Alarm Aggregator",
    icon: Workflow,
    description:
      "Correlates raw alarms, telemetry KPI deviations, topology links, and recent configuration changes into actionable incident clusters with auto-calculated MTTR reductions.",
    stats: [
      { label: "Raw Events (Last 1hr)", value: "18,290" },
      { label: "Correlated Clusters", value: "3,456" },
      { label: "Active Root Incidents", value: "152" },
      { label: "MTTR Compression", value: "42%" },
    ],
    telecomEntities: ["Alarms", "Events", "KPIs", "Changes", "Topology", "Root Cause"],
    actions: ["Run Automated Root Cause Analysis", "Filter by Severity: Critical", "Export Correlation Matrix"],
  },
  fcsps: {
    title: "FCSPS Telecom Lens",
    subtitle: "Focus → Correlate → Summarize → Predict → Suggest",
    icon: Eye,
    description:
      "A cognitive operational lens that focuses on critical network nodes, correlates multi-vendor logs, summarizes executive impact, predicts cascading failures, and suggests remediation MOPs.",
    stats: [
      { label: "Focus Areas", value: "5 Key Hubs" },
      { label: "Correlated Logs", value: "122 Events" },
      { label: "Active Insights", value: "12 Generated" },
      { label: "Predicted Risks", value: "3 Degradations" },
    ],
    telecomEntities: ["Focus", "Correlate", "Summarize", "Predict", "Suggest"],
    actions: ["Execute Suggested Healing Action", "Deep Dive Dubai 5GC Lens", "Recalibrate Lens Sensitivity"],
  },
  "digital-assets": {
    title: "Digital Telecom Assets",
    subtitle: "Inventory, VNF/CNF Services & Configuration Catalog",
    icon: Database,
    description:
      "Live discovery and cataloging of all physical and virtual network functions, containerized microservices, routing configs, runbooks, and operational documentation.",
    stats: [
      { label: "Total Asset Count", value: "12,546" },
      { label: "Active VNFs / CNFs", value: "2,548" },
      { label: "Kubernetes Pods", value: "4,321" },
      { label: "Config Drift Count", value: "4" },
    ],
    telecomEntities: ["NEs", "CNFs", "VNFs", "Pods", "Clusters", "Configs", "Runbooks", "Documents", "Scripts"],
    actions: ["Sync Asset Catalog", "Check Configuration Drift", "Audit Inactive Pods"],
  },
  automation: {
    title: "Telecom Automation Suite",
    subtitle: "Closed-Loop RCA, Healing & Diagnostics",
    icon: Bot,
    description:
      "Autonomous orchestrator capable of triggering pre-approved MOPs, self-healing degraded UPF pods, validating change tickets, and generating instant post-mortem reports.",
    stats: [
      { label: "Automated Workflows", value: "84" },
      { label: "Auto-Healed Incidents", value: "1,204" },
      { label: "Average Execution Time", value: "3.2s" },
      { label: "Success Rate", value: "99.4%" },
    ],
    telecomEntities: ["RCA", "Health Check", "Change Validation", "Healing", "Diagnostics"],
    actions: ["Run Full Network Health Check", "Trigger Self-Healing for Site 1023", "Verify Pre-Check Gateways"],
  },
  predictions: {
    title: "Predictive Intelligence",
    subtitle: "Capacity, Congestion & SLA Degradation Forecasting",
    icon: TrendingUp,
    description:
      "Machine learning models forecasting bandwidth saturation, radio cell congestion, hardware degradation, and SLA breach probabilities over the next 30 to 180 minutes.",
    stats: [
      { label: "Forecast Horizon", value: "180 Mins" },
      { label: "Predicted Anomalies", value: "3 Upcoming" },
      { label: "Capacity Warning Sites", value: "12" },
      { label: "Model Accuracy (F1)", value: "94.8%" },
    ],
    telecomEntities: ["Congestion", "Capacity", "Degradation", "SLA Risk", "Failure Probability"],
    actions: ["Simulate Traffic Spike +30%", "Predict Impact for Next 30 Mins", "Scale UPF User Plane Nodes"],
  },
  knowledge: {
    title: "Knowledge Core",
    subtitle: "Operational SOPs, MOPs & Incident Memory",
    icon: BookOpen,
    description:
      "Enterprise vector memory containing standard operating procedures, vendor errata, historic incident post-mortems, and engineering runbooks.",
    stats: [
      { label: "Indexed SOPs / MOPs", value: "1,420" },
      { label: "Historic Incidents", value: "8,950" },
      { label: "Vector Embeddings", value: "250K" },
      { label: "Knowledge Freshness", value: "Real-time" },
    ],
    telecomEntities: ["SOPs", "MOPs", "RCA History", "Vendor Docs", "Topology", "Past Incidents"],
    actions: ["Search Similar Historic Outages", "Generate New MOP Document", "Query Ericsson/Nokia Vendor Errata"],
  },
};

export function OrbDetailModal({
  orbId,
  onClose,
  onRunAction,
}: OrbDetailModalProps) {
  if (!orbId || !ORB_DETAILS[orbId]) return null;

  const detail = ORB_DETAILS[orbId];
  const Icon = detail.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-md animate-in fade-in duration-200">
      <div className="jarvis-card w-full max-w-[560px] p-6 shadow-2xl border border-blue-200/80 dark:border-cyan-500/40 bg-white/95 dark:bg-slate-900/95 text-[#102b5c] dark:text-slate-100 relative animate-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-full text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/10 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3.5 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 dark:bg-cyan-950/70 text-[#0a66ff] dark:text-[#00e5ff] border border-blue-200/80 dark:border-cyan-500/40 flex items-center justify-center shadow-inner">
            <Icon className="w-6 h-6" strokeWidth={2} />
          </div>
          <div>
            <h2 className="text-lg font-black tracking-tight text-[#082863] dark:text-white">
              {detail.title}
            </h2>
            <p className="text-xs font-bold text-[#0a66ff] dark:text-[#00e5ff]">
              {detail.subtitle}
            </p>
          </div>
        </div>

        {/* Description */}
        <p className="text-xs font-medium text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
          {detail.description}
        </p>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
          {detail.stats.map((s) => (
            <div key={s.label} className="p-2.5 rounded-xl bg-blue-50/50 dark:bg-white/5 border border-blue-100 dark:border-cyan-500/20 text-center">
              <div className="text-xs sm:text-sm font-black text-[#0a66ff] dark:text-[#00e5ff]">{s.value}</div>
              <div className="text-[9px] font-bold text-slate-400 uppercase mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Telecom Entities */}
        <div className="mb-4">
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1.5">
            Managed Telecom Artifacts
          </span>
          <div className="flex flex-wrap gap-1.5">
            {detail.telecomEntities.map((entity) => (
              <span
                key={entity}
                className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
              >
                {entity}
              </span>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-2">
            Automated Trigger Actions
          </span>
          <div className="flex flex-col gap-1.5">
            {detail.actions.map((act) => (
              <button
                key={act}
                onClick={() => {
                  onRunAction?.(act);
                  onClose();
                }}
                className="flex items-center justify-between p-2 rounded-xl bg-white dark:bg-slate-800/80 hover:bg-blue-50/80 dark:hover:bg-cyan-950/40 border border-blue-100 dark:border-cyan-500/30 text-left text-xs font-bold text-[#082863] dark:text-slate-100 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#0a66ff] dark:text-[#00e5ff]" />
                  <span>{act}</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-[#00e5ff] transition-colors" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
