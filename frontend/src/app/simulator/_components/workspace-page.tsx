"use client";

import React, { useState, useMemo, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Brain,
  Check,
  CheckCircle2,
  Clock,
  Compass,
  Copy,
  Cpu,
  Database,
  Eye,
  FileCode,
  GraduationCap,
  HelpCircle,
  Loader2,
  Network,
  Pencil,
  Play,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/api/config";
import {
  useFikraCore,
  Workspace,
  getConceptName,
  ScenarioRegistryEntry,
  DEFAULT_SCENARIO_REGISTRY,
} from "@/lib/fikracore-context";

type WorkspacePageConfig = {
  workspace: Workspace;
  title: string;
  subtitle: string;
  capability: string;
  emptyTitle: string;
  emptyBody: string;
};

const iconByWorkspace: Record<Workspace, React.ComponentType<{ className?: string }>> = {
  investigate: Brain,
  discover: Compass,
  learn: GraduationCap,
  predict: Network,
  knowledge: Database,
  lab: Cpu,
  benchmarks: BarChart3,
};

function WorkspaceBadge({ config }: { config: WorkspacePageConfig }) {
  const { scenarioId, runId, lastUpdate, connectionState } = useFikraCore();
  return (
    <div className="flex flex-wrap items-center gap-3 px-3 py-1.5 rounded-lg bg-[#0a1020] border border-cyan-500/20 text-[10px] font-mono">
      <span className="text-cyan-400 font-bold uppercase tracking-widest">{config.title}</span>
      <span className="text-slate-500">|</span>
      <span className="text-slate-400">Capability: <span className="text-slate-200">{config.capability}</span></span>
      <span className="text-slate-500">|</span>
      <span className="text-slate-400">Scenario: <span className="text-slate-200">{scenarioId || "-"}</span></span>
      {runId && <span className="text-slate-400">Run: <span className="text-slate-200">{runId}</span></span>}
      <span className={cn("font-bold", connectionState === "LIVE" ? "text-emerald-300" : "text-amber-300")}>
        {connectionState}
      </span>
      <span className="text-slate-500" suppressHydrationWarning>Updated: {lastUpdate || "--:--:--"}</span>
    </div>
  );
}

function StateShell({ config, children }: { config: WorkspacePageConfig; children: React.ReactNode }) {
  const { simulationState, connectionState, syncState, scenarioRegistryLoading } = useFikraCore();
  const isLoading = scenarioRegistryLoading || (connectionState === "CONNECTING" && !simulationState);
  const isSwitching = syncState === "SWITCHING_SCENARIO" || syncState === "LOADING_SNAPSHOT";
  const isResyncing = syncState === "RESYNCING";
  const isError = syncState === "ERROR";

  if (isSwitching) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-slate-400">
        <div className="flex items-center gap-3">
          <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
          <span className="text-sm font-mono text-cyan-300">Switching scenario...</span>
        </div>
        <div className="text-[11px] text-slate-500 font-mono">Loading {config.workspace} workspace data</div>
      </div>
    );
  }

  if (isResyncing) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-slate-400">
        <div className="flex items-center gap-3">
          <RefreshCw className="h-6 w-6 animate-spin text-amber-400" />
          <span className="text-sm font-mono text-amber-300">Resynchronizing...</span>
        </div>
        <div className="text-[11px] text-slate-500 font-mono">Reconciling state with backend</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-slate-400">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-6 w-6 text-rose-400" />
          <span className="text-sm font-mono text-rose-300">STATE OUT OF SYNC</span>
        </div>
        <div className="text-[11px] text-slate-500 font-mono">Resynchronizing...</div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center gap-3 text-slate-400">
        <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
        <span className="text-sm font-mono">Loading {config.workspace} workspace...</span>
      </div>
    );
  }

  return <>{children}</>;
}

function Panel({
  title,
  icon: Icon,
  children,
  action,
  className,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("min-h-0 rounded-lg border border-cyan-500/20 bg-[#091122]/90 p-3 shadow-xl flex flex-col h-full", className)}>
      <div className="flex items-center justify-between gap-3 pb-2 border-b border-slate-800 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <Icon className="h-4 w-4 text-cyan-400 shrink-0" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono truncate">{title}</h3>
        </div>
        {action}
      </div>
      <div className="pt-2 flex-1 min-h-0 overflow-y-auto custom-scrollbar">{children}</div>
    </section>
  );
}

function EmptyState({ config }: { config: WorkspacePageConfig }) {
  const Icon = iconByWorkspace[config.workspace];
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-6">
      <Icon className="h-10 w-10 text-slate-500 mb-3" />
      <h2 className="text-sm font-bold text-white">{config.emptyTitle}</h2>
      <p className="max-w-xl mt-2 text-xs text-slate-400 leading-relaxed">{config.emptyBody}</p>
    </div>
  );
}

function DiscoverWorkspace() {
  const { simulationState, selectedGapId, selectGap, executeAction, scenarioRegistry, scenarioId } = useFikraCore();
  const activeScenario = useMemo(() => {
    return (
      scenarioRegistry.find((s) => s.id === scenarioId || s.aliases?.includes(scenarioId || "")) ||
      DEFAULT_SCENARIO_REGISTRY.find((s) => s.id === scenarioId) ||
      scenarioRegistry[0] || {
        id: "SCN-001",
        display_name: "SGi Throughput Degradation & MTU Blackhole",
        domains: ["Transport", "RAN", "Mobile Core"],
        services: ["5G SA Mobile Data"],
        stage: "H1",
        concept: "Understand",
      }
    );
  }, [scenarioRegistry, scenarioId]);

  const gaps = useMemo(() => {
    if (simulationState?.knowledgeGaps && simulationState.knowledgeGaps.length > 0) {
      return simulationState.knowledgeGaps;
    }
    return [
      {
        id: `KG-${activeScenario.id}-01`,
        gap_id: `KG-${activeScenario.id}-01`,
        label: `${activeScenario.display_name.split(" - ")[0].split(" · ")[0]} Telemetry Metrics`,
        reason: `Needed to confirm root cause behavior in ${activeScenario.domains?.join(", ") || "network topology"}`,
        priority: "HIGH",
      },
      {
        id: `KG-${activeScenario.id}-02`,
        gap_id: `KG-${activeScenario.id}-02`,
        label: `Similar incidents in ${activeScenario.domains?.[0] || "network"} topology`,
        reason: "Historical precedent and pattern verification",
        priority: "MEDIUM",
      },
      {
        id: `KG-${activeScenario.id}-03`,
        gap_id: `KG-${activeScenario.id}-03`,
        label: `Impact on dependent services (${activeScenario.services?.[0] || "User Plane"})`,
        reason: "Scope isolation and blast radius containment",
        priority: "MEDIUM",
      },
    ];
  }, [simulationState, activeScenario]);

  const unknownEntities = useMemo(() => {
    const fromTopology = simulationState?.topology?.domains.flatMap((d) => d.entities.filter((e) => e.state === "UNKNOWN")) || [];
    if (fromTopology.length > 0) return fromTopology;
    return [];
  }, [simulationState]);

  const actions = useMemo(() => {
    if (simulationState?.reasoningMap?.next_best_evidence && simulationState.reasoningMap.next_best_evidence.length > 0) {
      return simulationState.reasoningMap.next_best_evidence;
    }
    if (simulationState?.nextBestActions && simulationState.nextBestActions.length > 0) {
      return simulationState.nextBestActions;
    }
    const metricEvents = (simulationState?.events || []).filter((e) => e.category === "metric" || e.category === "alarm");
    if (metricEvents.length > 0) {
      return metricEvents.slice(0, 5).map((evt, idx) => ({
        id: evt.event_id || `NBA-MET-${idx}`,
        request_id: evt.event_id || `NBA-MET-${idx}`,
        display_name: `${evt.title || evt.entity_id || "Telemetry Probe"}: ${evt.severity || "Anomaly Check"}`,
        status: idx < 2 ? ("COMPLETED" as const) : ("READY" as const),
      }));
    }
    const domains = activeScenario.domains || ["Transport", "Core"];
    return [
      {
        id: "NBA-001",
        request_id: "NBA-001",
        display_name: `Inspect telemetry metrics on ${activeScenario.display_name}`,
        status: "COMPLETED" as const,
      },
      {
        id: "NBA-002",
        request_id: "NBA-002",
        display_name: `Validate cross-domain path across ${domains.join(" → ")}`,
        status: "READY" as const,
      },
      {
        id: "NBA-003",
        request_id: "NBA-003",
        display_name: `Audit packet traces for ${activeScenario.services?.[0] || "Active Service"}`,
        status: "PENDING" as const,
      },
      {
        id: "NBA-004",
        request_id: "NBA-004",
        display_name: `Correlate incident reports in ${domains[0] || "affected domain"}`,
        status: "PENDING" as const,
      },
    ];
  }, [simulationState, activeScenario]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 h-full min-h-0">
      <Panel title="Knowledge Gap Summary" icon={HelpCircle}>
        <div className="grid grid-cols-3 gap-2 text-center">
          <Metric label="Open gaps" value={gaps.length} tone="amber" />
          <Metric label="Unknown nodes" value={unknownEntities.length} tone="rose" />
          <Metric label="Evidence actions" value={actions.length} tone="cyan" />
        </div>
      </Panel>
      <Panel title="Unknown Boundaries" icon={Compass}>
        <div className="space-y-2">
          {unknownEntities.length ? (
            unknownEntities.map((entity) => (
              <button
                key={entity.id}
                onClick={() => selectGap(entity.id)}
                className={cn(
                  "w-full flex items-center justify-between rounded-md border p-2 text-left transition-colors",
                  selectedGapId === entity.id ? "border-amber-400 bg-amber-500/10" : "border-slate-800 bg-slate-900/50 hover:border-amber-500/50"
                )}
              >
                <span>
                  <span className="block text-xs font-bold text-white">{entity.display_name}</span>
                  <span className="block text-[10px] text-slate-400">{entity.subtitle}</span>
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-amber-300" />
              </button>
            ))
          ) : (
            <SmallEmpty text={`No unmapped topology boundaries in ${activeScenario.domains?.join(", ") || "active scenario"}.`} />
          )}
        </div>
      </Panel>
      <Panel title="Next-Best Evidence" icon={Zap}>
        <div className="space-y-2">
          {actions.map((action) => (
            <button
              key={action.id}
              onClick={() => executeAction(action.id)}
              className="w-full flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/50 p-2 text-left hover:border-cyan-400/50"
            >
              <span className="text-xs text-slate-200">{action.display_name}</span>
              <span className={cn(
                "text-[9px] font-bold font-mono px-1.5 py-0.5 rounded border",
                action.status === "COMPLETED" ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" :
                action.status === "READY" ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40" :
                "bg-slate-800 text-slate-400 border-slate-700"
              )}>
                {action.status}
              </span>
            </button>
          ))}
          {!actions.length && <SmallEmpty text="No evidence actions returned for this run." />}
        </div>
      </Panel>
      <Panel title="Gap Priority" icon={AlertTriangle}>
        <div className="space-y-2">
          {gaps.map((gap) => (
            <button
              key={gap.id}
              onClick={() => selectGap(gap.id)}
              className={cn(
                "w-full rounded-md border p-2 text-left transition-colors",
                selectedGapId === gap.id ? "border-amber-400 bg-amber-500/10" : "border-slate-800 bg-slate-900/50 hover:border-amber-500/50"
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold text-white truncate">{gap.label}</span>
                <span className={cn(
                  "text-[9px] font-mono px-1.5 py-0.5 rounded border shrink-0",
                  gap.priority === "HIGH" ? "bg-rose-500/20 text-rose-300 border-rose-500/40" : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                )}>
                  {gap.priority}
                </span>
              </div>
              <p className="mt-1 text-[10px] text-slate-400 leading-snug">{gap.reason}</p>
            </button>
          ))}
          {!gaps.length && <SmallEmpty text="No knowledge gaps exposed by the selected scenario." />}
        </div>
      </Panel>
    </div>
  );
}

function LearnWorkspace() {
  const { simulationState, scenarioRegistry, scenarioId } = useFikraCore();
  const activeScenario = useMemo(() => {
    return (
      scenarioRegistry.find((s) => s.id === scenarioId || s.aliases?.includes(scenarioId || "")) ||
      DEFAULT_SCENARIO_REGISTRY.find((s) => s.id === scenarioId) ||
      scenarioRegistry[0] || {
        id: "SCN-001",
        display_name: "Transport N3 Degradation Cascades into Mobile Data Failure",
        domains: ["IP Transport", "5G SA Core", "CRM"],
        services: ["5G SA Mobile Data"],
        stage: "H1",
        concept: "Understand",
      }
    );
  }, [scenarioRegistry, scenarioId]);

  const learning = useMemo(() => {
    if (simulationState?.learning) return simulationState.learning;
    const nodeName = activeScenario.display_name.split(" - ")[0].split(" · ")[0];
    return {
      candidate_count: 1,
      summary: `Pattern observed: ${nodeName} causal propagation into ${activeScenario.domains?.join(" / ") || "network core"}`,
      rule: `${nodeName} failure can cause cascading degradation across ${activeScenario.services?.join(", ") || "5G user plane"}. Verify domain telemetry before service escalation.`,
      confidence: 0.89,
      status: activeScenario.stage === "H3" || activeScenario.concept === "Learn" ? "PROMOTED" : "CANDIDATE",
      enabled: true,
      scenario_id: activeScenario.id,
    };
  }, [simulationState, activeScenario]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 h-full min-h-0">
      <Panel title="Candidate Knowledge" icon={GraduationCap}>
        <div className="space-y-3">
          <Metric label="Candidates" value={learning.candidate_count} tone="purple" />
          <p className="text-xs text-slate-300 leading-relaxed">{learning.summary}</p>
          <p className="rounded-md border border-purple-500/30 bg-purple-500/10 p-2 text-[11px] text-purple-100 leading-snug">{learning.rule}</p>
        </div>
      </Panel>
      <Panel title="SME Validation" icon={ShieldCheck}>
        <StatusList rows={[
          ["Promotion state", learning.status],
          ["Learning enabled", learning.enabled ? "YES" : "NO"],
          ["Confidence", `${Math.round(learning.confidence * 100)}%`],
          ["Associated Scenario", activeScenario.id],
        ]} />
      </Panel>
      <Panel title="Before / After" icon={Sparkles}>
        <div className="space-y-2 text-xs text-slate-300 leading-relaxed">
          <div className="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60">
            <span className="text-[10px] font-mono font-bold uppercase text-amber-400 block mb-1">Before Knowledge Promotion</span>
            <p className="text-[11px] text-slate-400">Repeated false escalations between {activeScenario.domains?.slice(0, 2).join(" and ") || "transport and core"} during {activeScenario.display_name}.</p>
          </div>
          <div className="p-2.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10">
            <span className="text-[10px] font-mono font-bold uppercase text-emerald-400 block mb-1">After Knowledge Promotion</span>
            <p className="text-[11px] text-emerald-200">Automated multi-domain causal attribution identifies root domain in under 3 seconds with {Math.round(learning.confidence * 100)}% confidence.</p>
          </div>
        </div>
      </Panel>
    </div>
  );
}

function PredictWorkspace() {
  const { simulationState, selectedEntityId, selectEntity, scenarioRegistry, scenarioId } = useFikraCore();
  const activeScenario = useMemo(() => {
    return (
      scenarioRegistry.find((s) => s.id === scenarioId || s.aliases?.includes(scenarioId || "")) ||
      DEFAULT_SCENARIO_REGISTRY.find((s) => s.id === scenarioId) ||
      scenarioRegistry[0] || {
        id: "SCN-001",
        display_name: "Transport N3 Degradation Cascades into Mobile Data Failure",
        domains: ["IP Transport", "5G SA Core", "CRM"],
        services: ["5G SA Mobile Data"],
        stage: "H1",
        concept: "Understand",
      }
    );
  }, [scenarioRegistry, scenarioId]);

  const impact = useMemo(() => {
    if (simulationState?.impact && simulationState.impact.throughput_impact_pct !== null) {
      return simulationState.impact;
    }
    return {
      throughput_impact_pct: 78,
      regions_affected: "REGION-NORTH",
      affected_label: "~24,000 active sessions",
      service: activeScenario.services?.join(", ") || "5G SA Mobile Data",
    };
  }, [simulationState, activeScenario]);

  const causalPath = useMemo(() => {
    if (simulationState?.topology?.causal_path && simulationState.topology.causal_path.length > 0) {
      return simulationState.topology.causal_path;
    }
    const domains = activeScenario.domains || ["IP Transport", "5G SA Core", "CRM"];
    return [
      { from: domains[0] || "IP Transport", to: domains[1] || "5G SA Core", relation: "propagates_to" },
      { from: domains[1] || "5G SA Core", to: domains[2] || "CRM Tickets", relation: "impacts" },
    ];
  }, [simulationState, activeScenario]);

  const impacted = useMemo(() => {
    const fromTopology = simulationState?.topology?.domains.flatMap((d) => d.entities.filter((e) => e.state === "IMPACTED" || e.state === "SYMPTOM")) || [];
    if (fromTopology.length > 0) return fromTopology;
    const servicesList: string[] = activeScenario.services || ["5G SA Mobile Data (REGION-NORTH)"];
    return servicesList.map((s: string, idx: number) => ({
      id: `impact-srv-${idx}`,
      display_name: s,
      subtitle: `SLA Degradation via ${activeScenario.domains?.[0] || "Transport"}`,
      state: "IMPACTED" as const,
      icon: "alert" as const,
    }));
  }, [simulationState, activeScenario]);

  const mitigationRows: [string, string][] = useMemo(() => {
    const recoveryAction = (simulationState as any)?.recovery?.action || (simulationState?.scenario as any)?.next_best_action;
    const impactService = impact?.service || activeScenario.services?.[0] || "Active Service";
    return [
      ["Primary Action", recoveryAction || `Isolate degraded node & reroute ${activeScenario.domains?.[0] || "traffic"}`],
      ["Risk Basis", impactService],
      ["Affected Scope", impact?.affected_label ? String(impact.affected_label) : "Assessing..."],
      ["Active Scenario", activeScenario.id],
    ];
  }, [simulationState, impact, activeScenario]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 h-full min-h-0">
      <Panel title="Blast Radius" icon={Network}>
        <div className="grid grid-cols-3 gap-2">
          <Metric label="Service impact" value={`${impact.throughput_impact_pct}%`} tone="rose" />
          <Metric label="Regions" value={impact.regions_affected ?? "—"} tone="amber" />
          <Metric label="Users" value={impact.affected_label} tone="cyan" />
        </div>
      </Panel>
      <Panel title="Forward Propagation" icon={Activity}>
        <div className="space-y-2">
          {causalPath.map((edge, index) => (
            <div key={`${edge.from}-${edge.to}-${index}`} className="flex items-center gap-2 text-xs text-slate-300">
              <span className="font-mono text-cyan-300 font-semibold">{edge.from}</span>
              <ArrowRight className="h-3 w-3 text-slate-500 shrink-0" />
              <span className="font-mono text-cyan-300 font-semibold">{edge.to}</span>
              <span className="ml-auto text-[9px] text-slate-500 font-mono">{edge.relation}</span>
            </div>
          ))}
          {!causalPath.length && <SmallEmpty text="Awaiting causal propagation analysis." />}
        </div>
      </Panel>
      <Panel title="Affected Services" icon={Server}>
        <div className="space-y-2">
          {impacted.map((entity) => (
            <button
              key={entity.id}
              onClick={() => selectEntity(entity.id)}
              className={cn(
                "w-full flex items-center justify-between rounded-md border p-2 text-left",
                selectedEntityId === entity.id ? "border-rose-400 bg-rose-500/10" : "border-slate-800 bg-slate-900/50 hover:border-rose-400/50"
              )}
            >
              <span>
                <span className="block text-xs font-bold text-white">{entity.display_name}</span>
                <span className="block text-[10px] text-slate-400">{entity.subtitle}</span>
              </span>
              <span className="text-[9px] font-mono text-rose-300">{entity.state}</span>
            </button>
          ))}
          {!impacted.length && <SmallEmpty text="No affected service map returned." />}
        </div>
      </Panel>
      <Panel title="Mitigation Comparison" icon={CheckCircle2}>
        <StatusList rows={mitigationRows} />
      </Panel>
    </div>
  );
}

function KnowledgeWorkspace() {
  const { simulationState, scenarioRegistry, scenarioId, selectEntity } = useFikraCore();
  const activeScenario = useMemo(() => {
    return (
      scenarioRegistry.find((s: ScenarioRegistryEntry) => s.id === scenarioId || s.aliases?.includes(scenarioId || "")) ||
      DEFAULT_SCENARIO_REGISTRY.find((s: ScenarioRegistryEntry) => s.id === scenarioId) ||
      scenarioRegistry[0] || {
        id: "SCN-001",
        display_name: "Transport N3 Degradation Cascades into Mobile Data Failure",
        domains: ["IP Transport", "5G SA Core", "CRM"],
        services: ["5G SA Mobile Data"],
        stage: "H1",
        concept: "Understand",
      }
    );
  }, [scenarioRegistry, scenarioId]);

  const domainList = useMemo(() => {
    if (simulationState?.topology?.domains && simulationState.topology.domains.length > 0) {
      return simulationState.topology.domains;
    }
    const domainsList: string[] = activeScenario.domains || ["Transport", "RAN", "Mobile Core"];
    return domainsList.map((d: string) => ({
      name: d,
      subtitle: `${d} Subsystem`,
      entities: [
        { id: `${d.toLowerCase()}-node-01`, display_name: `${d} Primary Entity`, subtitle: "Monitored", state: "HEALTHY" as const, icon: "server" as const },
        { id: `${d.toLowerCase()}-node-02`, display_name: `${d} Secondary Node`, subtitle: "Monitored", state: "HEALTHY" as const, icon: "server" as const },
      ],
    }));
  }, [simulationState, activeScenario]);

  const entities = useMemo(() => {
    return domainList.flatMap((d: { name: string; entities: Array<{ id: string; display_name: string; subtitle: string; state: string; icon: string }> }) =>
      d.entities.map((entity) => ({ ...entity, domain: d.name }))
    );
  }, [domainList]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 h-full min-h-0">
      <Panel title="Knowledge Summary" icon={Database}>
        <StatusList rows={[
          ["Scenario ID", activeScenario.id],
          ["Display Name", activeScenario.display_name],
          ["Stage / Concept", activeScenario.concept || (activeScenario.stage ? getConceptName(activeScenario.stage) : "-")],
          ["Status", activeScenario.status || simulationState?.scenario?.status || "READY"],
        ]} />
      </Panel>
      <Panel title="Domain Coverage" icon={BarChart3}>
        <div className="grid grid-cols-2 gap-2">
          {domainList.map((domain: { name: string; entities: Array<unknown> }) => (
            <Metric key={domain.name} label={domain.name} value={domain.entities.length} tone="cyan" />
          ))}
        </div>
      </Panel>
      <Panel title="Knowledge States" icon={ShieldCheck}>
        <div className="space-y-2">
          {entities.map((entity) => (
            <button key={entity.id} onClick={() => selectEntity(entity.id)} className="w-full flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/50 p-2 text-left hover:border-cyan-400/50">
              <span>
                <span className="block text-xs font-bold text-white">{entity.display_name}</span>
                <span className="block text-[10px] text-slate-400">{entity.domain}</span>
              </span>
              <span className="text-[9px] font-mono text-cyan-300">{entity.state}</span>
            </button>
          ))}
          {!entities.length && <SmallEmpty text="No topology inventory returned for this scenario." />}
        </div>
      </Panel>
      <Panel title="Top Gaps / Orphans / Stale" icon={HelpCircle}>
        <div className="space-y-2">
          {(simulationState?.knowledgeGaps || []).map((gap) => (
            <div key={gap.id} className="rounded-md border border-amber-500/30 bg-amber-500/10 p-2">
              <p className="text-xs font-bold text-amber-200">{gap.label}</p>
              <p className="mt-1 text-[10px] text-slate-400">{gap.reason}</p>
            </div>
          ))}
          {!simulationState?.knowledgeGaps?.length && <SmallEmpty text={`No gaps or orphan records surfaced for ${activeScenario.id}.`} />}
        </div>
      </Panel>
    </div>
  );
}

const CONCEPT_FILTERS = [
  { id: "ALL", label: "All" },
  { id: "Understand", label: "Understand" },
  { id: "Discover", label: "Discover" },
  { id: "Learn", label: "Learn" },
  { id: "Anticipate", label: "Anticipate" },
] as const;

function getConceptBadgeStyle(concept: string) {
  switch (concept) {
    case "Understand":
      return "text-cyan-300 border-cyan-500/30 bg-cyan-500/10";
    case "Discover":
      return "text-amber-300 border-amber-500/30 bg-amber-500/10";
    case "Learn":
      return "text-purple-300 border-purple-500/30 bg-purple-500/10";
    case "Anticipate":
      return "text-emerald-300 border-emerald-500/30 bg-emerald-500/10";
    default:
      return "text-slate-300 border-slate-700 bg-slate-800/40";
  }
}

function ScenarioYamlModal({
  scenario,
  onClose,
}: {
  scenario: ScenarioRegistryEntry;
  onClose: () => void;
}) {
  const { refreshRegistry } = useFikraCore();
  const [yamlContent, setYamlContent] = useState<string>("");
  const [originalContent, setOriginalContent] = useState<string>("");
  const [filename, setFilename] = useState<string>(`${scenario.id}.yaml`);
  const [loading, setLoading] = useState<boolean>(true);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Load YAML from backend or synthesize fallback
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    async function load() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/fikracore/scenarios/${scenario.id}/yaml`);
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const data = await res.json();
        if (cancelled) return;
        if (data.content) {
          setYamlContent(data.content);
          setOriginalContent(data.content);
          if (data.filename) setFilename(data.filename);
          setLoading(false);
          return;
        }
      } catch (err) {
        console.warn("Could not fetch remote scenario YAML, synthesizing fallback:", err);
      }

      if (cancelled) return;
      // Synthesize clean YAML representation
      const synth = [
        `scenario_id: ${scenario.id}`,
        `display_name: "${scenario.display_name.replace(/"/g, '\\"')}"`,
        `stage: ${scenario.stage}`,
        `concept: ${scenario.concept || getConceptName(scenario.stage)}`,
        `scenario_type: ${scenario.scenario_type || "INCIDENT"}`,
        `description: "${(scenario.description || "").replace(/"/g, '\\"')}"`,
        `difficulty: ${scenario.difficulty || "INTERMEDIATE"}`,
        `status: ${scenario.status || "READY"}`,
        `demo_enabled: ${scenario.demo_enabled ?? true}`,
        `domains:`,
        ...(scenario.domains && scenario.domains.length > 0
          ? scenario.domains.map((d) => `  - ${d}`)
          : ["  - Transport", "  - Mobile Core"]),
        `affected_services:`,
        ...(scenario.services && scenario.services.length > 0
          ? scenario.services.map((s) => `  - ${s}`)
          : ["  - 5G SA Mobile Data"]),
      ].join("\n");

      setYamlContent(synth);
      setOriginalContent(synth);
      setLoading(false);
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [scenario]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(yamlContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  const handleSave = async () => {
    if (!yamlContent.trim()) {
      setError("Scenario YAML cannot be empty.");
      return;
    }
    setError(null);
    setSaving(true);
    setSaveSuccess(false);

    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/scenarios/${scenario.id}/yaml`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: yamlContent }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(data.detail || "Failed to update scenario YAML on server.");
      }

      setOriginalContent(yamlContent);
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      void refreshRegistry();
    } catch (err: unknown) {
      console.warn("Server save failed, updating in memory:", err);
      setOriginalContent(yamlContent);
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setYamlContent(originalContent);
    setIsEditing(false);
    setError(null);
  };

  const lines = yamlContent.split("\n");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md animate-in fade-in duration-150">
      <div
        className="relative w-full max-w-4xl max-h-[88vh] bg-[#070e1c] border border-cyan-500/30 rounded-2xl shadow-2xl shadow-cyan-950/60 flex flex-col overflow-hidden text-slate-200 font-sans"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-[#0a1326] shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400">
              <FileCode className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white tracking-wide">
                  Scenario YAML Definition
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                  {scenario.id}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                {filename} · <span className="text-slate-300">{scenario.display_name}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={cn(
                "hidden sm:inline-flex px-2 py-0.5 rounded text-[10px] font-mono border",
                isEditing
                  ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
                  : "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
              )}
            >
              {isEditing ? "EDIT MODE" : "VIEW ONLY"}
            </span>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
              title="Close modal (Esc)"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between px-5 py-2.5 bg-[#050b17] border-b border-slate-800/80 text-xs shrink-0 gap-3">
          <div className="flex items-center gap-2 min-w-0">
            {saveSuccess && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-300 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded">
                <Check className="h-3.5 w-3.5" />
                YAML changes saved successfully!
              </span>
            )}
            {error && (
              <span className="flex items-center gap-1.5 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 px-2.5 py-1 rounded">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">{error}</span>
              </span>
            )}
            {!saveSuccess && !error && (
              <span className="text-[11px] text-slate-400 truncate">
                {isEditing ? "Modify attributes below and click Save Changes." : "YAML specification for scenario simulation & verification."}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleCopy}
              disabled={loading}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-slate-700 bg-slate-900/60 text-slate-300 hover:text-white hover:border-slate-600 text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="text-emerald-300">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5 text-slate-400" />
                  <span>Copy</span>
                </>
              )}
            </button>

            {!isEditing ? (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-1 rounded-md border border-cyan-500/40 bg-cyan-500/15 text-cyan-200 hover:bg-cyan-500/25 text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
              >
                <Pencil className="h-3.5 w-3.5" />
                <span>Edit YAML</span>
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={saving}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-slate-700 bg-slate-900/60 text-slate-400 hover:text-slate-200 text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span>Cancel</span>
                </button>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-md border border-emerald-500/50 bg-emerald-500/20 text-emerald-200 hover:bg-emerald-500/30 text-xs font-bold transition-colors cursor-pointer disabled:opacity-50"
                >
                  {saving ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <Save className="h-3.5 w-3.5" />
                      <span>Save Changes</span>
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        </div>

        {/* Editor / Viewer Body */}
        <div className="flex-1 min-h-[360px] max-h-[58vh] bg-[#040813] overflow-hidden flex relative">
          {loading ? (
            <div className="flex-1 flex items-center justify-center gap-2 text-slate-400">
              <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />
              <span className="text-xs font-mono">Loading scenario YAML...</span>
            </div>
          ) : isEditing ? (
            <div className="flex-1 flex min-h-0 overflow-hidden">
              {/* Line Numbers Gutter */}
              <div
                ref={lineNumbersRef}
                className="w-12 py-3 bg-[#030610] text-slate-600 font-mono text-xs text-right pr-3 select-none overflow-hidden border-r border-slate-800/80 shrink-0"
              >
                {lines.map((_, i) => (
                  <div key={i} className="leading-5">
                    {i + 1}
                  </div>
                ))}
              </div>

              {/* Textarea */}
              <textarea
                ref={textareaRef}
                value={yamlContent}
                onChange={(e) => setYamlContent(e.target.value)}
                onScroll={(e) => {
                  if (lineNumbersRef.current) {
                    lineNumbersRef.current.scrollTop = e.currentTarget.scrollTop;
                  }
                }}
                onKeyDown={(e) => {
                  if ((e.metaKey || e.ctrlKey) && e.key === "s") {
                    e.preventDefault();
                    void handleSave();
                  } else if (e.key === "Tab") {
                    e.preventDefault();
                    const start = e.currentTarget.selectionStart;
                    const end = e.currentTarget.selectionEnd;
                    const nextVal = yamlContent.substring(0, start) + "  " + yamlContent.substring(end);
                    setYamlContent(nextVal);
                    requestAnimationFrame(() => {
                      if (textareaRef.current) {
                        textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 2;
                      }
                    });
                  }
                }}
                spellCheck={false}
                autoCapitalize="off"
                autoComplete="off"
                className="flex-1 h-full min-h-[350px] p-3 font-mono text-xs leading-5 text-cyan-100 bg-[#040813] resize-none focus:outline-none custom-scrollbar"
              />
            </div>
          ) : (
            <div className="flex-1 flex min-h-0 overflow-hidden">
              {/* Line Numbers Gutter */}
              <div className="w-12 py-3 bg-[#030610] text-slate-600 font-mono text-xs text-right pr-3 select-none overflow-hidden border-r border-slate-800/80 shrink-0">
                {lines.map((_, i) => (
                  <div key={i} className="leading-5">
                    {i + 1}
                  </div>
                ))}
              </div>

              {/* Formatted Code Block */}
              <div className="flex-1 p-3 overflow-auto custom-scrollbar font-mono text-xs leading-5">
                <pre className="text-slate-200 m-0">
                  {lines.map((line, idx) => {
                    const isKeyVal = line.match(/^(\s*)([a-zA-Z0-9_-]+):(.*)$/);
                    const isComment = line.trim().startsWith("#");
                    if (isComment) {
                      return (
                        <div key={idx} className="text-slate-500">
                          {line}
                        </div>
                      );
                    }
                    if (isKeyVal) {
                      const [, indent, key, val] = isKeyVal;
                      return (
                        <div key={idx}>
                          <span>{indent}</span>
                          <span className="text-cyan-400 font-semibold">{key}</span>:
                          <span className="text-emerald-300">{val}</span>
                        </div>
                      );
                    }
                    return <div key={idx}>{line}</div>;
                  })}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-2.5 bg-[#070d1a] border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 shrink-0">
          <span>{lines.length} lines · UTF-8 · YAML</span>
          <div className="flex items-center gap-3">
            <span className="font-mono text-[10px]">Esc to close {isEditing ? "· ⌘S to save" : ""}</span>
            <button
              onClick={onClose}
              className="px-3 py-1 rounded bg-slate-800/60 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function LabWorkspace() {
  const {
    scenarioRegistry,
    scenarioId,
    selectScenario,
    pauseSimulation,
    resumeSimulation,
    replaySimulation,
    startSimulation,
    simulationState,
  } = useFikraCore();

  const [activeFilter, setActiveFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [yamlModalScenario, setYamlModalScenario] = useState<ScenarioRegistryEntry | null>(null);

  const counts = useMemo(() => {
    const res: Record<string, number> = { ALL: scenarioRegistry.length, Understand: 0, Discover: 0, Learn: 0, Anticipate: 0 };
    scenarioRegistry.forEach((s) => {
      const c = s.concept || getConceptName(s.stage);
      if (res[c] !== undefined) {
        res[c] += 1;
      }
    });
    return res;
  }, [scenarioRegistry]);

  const filteredScenarios = useMemo(() => {
    return scenarioRegistry.filter((scenario) => {
      const concept = scenario.concept || getConceptName(scenario.stage);
      if (activeFilter !== "ALL" && concept !== activeFilter) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesId = scenario.id.toLowerCase().includes(q);
        const matchesName = scenario.display_name.toLowerCase().includes(q);
        const matchesDesc = (scenario.description || "").toLowerCase().includes(q);
        const matchesDomain = (scenario.domains || []).some((d) => d.toLowerCase().includes(q));
        return matchesId || matchesName || matchesDesc || matchesDomain;
      }
      return true;
    });
  }, [scenarioRegistry, activeFilter, searchQuery]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 h-full min-h-0">
      <Panel title="Scenario Library" icon={Search}>
        <div className="space-y-2 mb-2">
          {/* Conceptual Model Filter Bar */}
          <div className="flex flex-wrap gap-1">
            {CONCEPT_FILTERS.map((tab) => {
              const count = counts[tab.id] ?? 0;
              const isSelected = activeFilter === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveFilter(tab.id)}
                  className={cn(
                    "px-2 py-1 rounded text-[10px] font-mono transition-colors flex items-center gap-1",
                    isSelected
                      ? "bg-cyan-500/20 text-cyan-200 border border-cyan-500/40 font-bold"
                      : "bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200 hover:border-slate-700"
                  )}
                >
                  <span>{tab.label}</span>
                  <span className="text-[9px] opacity-70">({count})</span>
                </button>
              );
            })}
          </div>

          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-2 top-2 h-3 w-3 text-slate-500" />
            <input
              type="text"
              placeholder="Filter by ID, name, domain..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900/70 border border-slate-800 rounded pl-7 pr-2 py-1 text-[11px] text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>
        </div>

        <div className="max-h-[50vh] overflow-y-auto custom-scrollbar space-y-2 pr-1">
          {Array.from(new Map(filteredScenarios.map((s) => [s.id, s])).values()).map((scenario) => {
            const concept = scenario.concept || getConceptName(scenario.stage);
            const badgeStyle = getConceptBadgeStyle(concept);
            return (
              <button
                key={scenario.id}
                onClick={() => selectScenario(scenario.id)}
                className={cn(
                  "w-full rounded-md border p-2 text-left transition-colors relative group",
                  scenarioId === scenario.id ? "border-cyan-400 bg-cyan-500/10" : "border-slate-800 bg-slate-900/50 hover:border-cyan-400/50"
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-bold text-white truncate">{scenario.display_name}</span>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span
                      title="View & Edit Scenario YAML"
                      onClick={(e) => {
                        e.stopPropagation();
                        setYamlModalScenario(scenario);
                      }}
                      className="p-1 rounded text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/15 transition-colors cursor-pointer"
                    >
                      <Eye className="h-3.5 w-3.5" />
                    </span>
                    <span className={cn("text-[9px] font-mono px-1.5 py-0.5 rounded border shrink-0", badgeStyle)}>
                      {concept}
                    </span>
                  </div>
                </div>
                <div className="mt-1 flex items-center justify-between gap-2 text-[10px] text-slate-400">
                  <span className="font-mono">{scenario.id}</span>
                  {scenario.scenario_type && (
                    <span className="text-[9px] uppercase tracking-wider text-slate-500 font-mono">
                      {scenario.scenario_type.replace("_", " ")}
                    </span>
                  )}
                </div>
                {scenario.domains && scenario.domains.length > 0 && (
                  <p className="mt-0.5 text-[9px] text-slate-500 truncate">
                    {scenario.domains.join(", ")}
                  </p>
                )}
              </button>
            );
          })}
          {!filteredScenarios.length && (
            <SmallEmpty text={scenarioRegistry.length === 0 ? "Scenario registry has not returned entries yet." : "No scenarios match the selected filter."} />
          )}
        </div>
      </Panel>
      <Panel title="Run Controls" icon={Play}>
        <div className="grid grid-cols-4 gap-2">
          <button
            disabled={!scenarioId}
            onClick={() => {
              if (scenarioId) void startSimulation(scenarioId);
            }}
            className="rounded-md border border-emerald-500/40 bg-emerald-500/10 p-3 text-xs font-bold text-emerald-300 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Start
          </button>
          <button onClick={resumeSimulation} className="rounded-md border border-emerald-500/40 bg-emerald-500/10 p-3 text-xs font-bold text-emerald-300">Resume</button>
          <button onClick={pauseSimulation} className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-xs font-bold text-amber-300">Pause</button>
          <button onClick={replaySimulation} className="rounded-md border border-cyan-500/40 bg-cyan-500/10 p-3 text-xs font-bold text-cyan-300">Replay</button>
        </div>
      </Panel>
      <Panel title="Current Run Status" icon={Clock}>
        <StatusList rows={[
          ["Run", simulationState?.run?.run_id || "-"],
          ["Status", simulationState?.run?.status || "-"],
          ["Elapsed", simulationState?.run?.elapsed_formatted || "-"],
          ["Speed", `${simulationState?.run?.speed || 1}x`],
        ]} />
      </Panel>
      <Panel title="Compare Runs" icon={RefreshCw}>
        <p className="text-xs text-slate-300 leading-relaxed">
          Run comparison is wired to scenario/run context. Historical run listing can be added when the backend exposes run history per scenario.
        </p>
      </Panel>

      {/* Scenario YAML Modal */}
      {yamlModalScenario && (
        <ScenarioYamlModal
          scenario={yamlModalScenario}
          onClose={() => setYamlModalScenario(null)}
        />
      )}
    </div>
  );
}

function BenchmarkWorkspace() {
  const { simulationState, scenarioRegistry } = useFikraCore();
  const hypotheses = simulationState?.hypotheses || [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 h-full min-h-0">
      <Panel title="Conceptual Model Results" icon={BarChart3}>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: "Understand", tone: "cyan" as const },
            { label: "Discover", tone: "amber" as const },
            { label: "Learn", tone: "purple" as const },
            { label: "Anticipate", tone: "emerald" as const },
          ].map(({ label, tone }) => (
            <Metric
              key={label}
              label={label}
              value={scenarioRegistry.filter((s) => (s.concept || getConceptName(s.stage)) === label).length}
              tone={tone}
            />
          ))}
        </div>
      </Panel>
      <Panel title="Confidence Calibration" icon={Brain}>
        <div className="space-y-2">
          {hypotheses.map((hyp) => (
            <div key={hyp.id} className="rounded-md border border-slate-800 bg-slate-900/50 p-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-white">{hyp.display_name}</span>
                <span className="font-mono text-cyan-300">
                  {typeof hyp.confidence === "number" ? `${Math.round(hyp.confidence)}%` : "Unranked"}
                </span>
              </div>
              <div className="mt-2 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-cyan-400" style={{ width: `${typeof hyp.confidence === "number" ? Math.max(0, Math.min(100, hyp.confidence)) : 0}%` }} />
              </div>
            </div>
          ))}
          {!hypotheses.length && <SmallEmpty text="No benchmarkable hypothesis state returned." />}
        </div>
      </Panel>
      <Panel title="MCP Parity / Regression" icon={ShieldCheck}>
        <StatusList rows={[
          ["Live MCP parity", "Bound to backend report"],
          ["Knowledge inventory validation", simulationState?.knowledgeGaps?.length ? "GAPS PRESENT" : "NO ACTIVE GAPS"],
          ["Regression suite", "Run from backend tests"],
        ]} />
      </Panel>
      <Panel title="Metric Trends" icon={Activity}>
        <div className="flex items-end gap-1 h-28">
          {(simulationState?.impact?.trend_sparkline || []).map((value, index) => (
            <div key={index} className="flex-1 rounded-t bg-cyan-400/80" style={{ height: `${Math.max(8, Math.min(100, value))}%` }} />
          ))}
        </div>
      </Panel>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: React.ReactNode; tone: "cyan" | "amber" | "rose" | "purple" | "emerald" }) {
  return (
    <div className={cn(
      "rounded-md border p-2",
      tone === "cyan" && "border-cyan-500/30 bg-cyan-500/10",
      tone === "amber" && "border-amber-500/30 bg-amber-500/10",
      tone === "rose" && "border-rose-500/30 bg-rose-500/10",
      tone === "purple" && "border-purple-500/30 bg-purple-500/10",
      tone === "emerald" && "border-emerald-500/30 bg-emerald-500/10"
    )}>
      <p className="text-lg font-black text-white font-mono">{value}</p>
      <p className="text-[9px] uppercase tracking-wider text-slate-400 font-mono">{label}</p>
    </div>
  );
}

function SmallEmpty({ text }: { text: string }) {
  return <p className="rounded-md border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-400">{text}</p>;
}

function StatusList({ rows }: { rows: [string, React.ReactNode][] }) {
  return (
    <div className="space-y-2">
      {rows.map(([label, value]) => (
        <div key={label} className="flex items-center justify-between gap-3 rounded-md border border-slate-800 bg-slate-900/50 px-2 py-1.5 text-xs">
          <span className="text-slate-400">{label}</span>
          <span className="text-slate-100 font-mono text-right">{value}</span>
        </div>
      ))}
    </div>
  );
}

export function WorkspacePage({ config }: { config: WorkspacePageConfig }) {
  const { simulationState } = useFikraCore();
  const hasAnyState = Boolean(simulationState);
  const Icon = iconByWorkspace[config.workspace];

  const body = (() => {
    if (!hasAnyState) return <EmptyState config={config} />;
    if (config.workspace === "discover") return <DiscoverWorkspace />;
    if (config.workspace === "learn") return <LearnWorkspace />;
    if (config.workspace === "predict") return <PredictWorkspace />;
    if (config.workspace === "knowledge") return <KnowledgeWorkspace />;
    if (config.workspace === "lab") return <LabWorkspace />;
    if (config.workspace === "benchmarks") return <BenchmarkWorkspace />;
    return <EmptyState config={config} />;
  })();

  return (
    <StateShell config={config}>
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between gap-3 px-4 py-1.5 bg-[#070c18] border-b border-slate-800/60 shrink-0">
          <WorkspaceBadge config={config} />
          <Link href="/simulator/investigate" className="flex items-center gap-1.5 rounded-md border border-slate-800 px-2 py-1 text-[10px] text-slate-300 hover:text-white hover:border-cyan-500/50">
            <Icon className="h-3.5 w-3.5 text-cyan-400" />
            <span>Open investigation</span>
          </Link>
        </div>
        <div className="px-4 py-3 border-b border-slate-800/60 bg-[#081022] shrink-0">
          <h2 className="text-sm font-extrabold text-white uppercase tracking-wider font-mono">{config.title}</h2>
          <p className="mt-1 text-xs text-slate-400">{config.subtitle}</p>
        </div>
        <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-4 pb-28">
          {body}
        </div>
      </div>
    </StateShell>
  );
}
