"use client";

import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle2,
  Clock,
  Compass,
  Cpu,
  Database,
  GraduationCap,
  HelpCircle,
  Loader2,
  Network,
  Play,
  RefreshCw,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useFikraCore, Workspace } from "@/lib/fikracore-context";

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
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <section className="min-h-0 rounded-lg border border-cyan-500/20 bg-[#091122]/90 p-3 shadow-xl">
      <div className="flex items-center justify-between gap-3 pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2 min-w-0">
          <Icon className="h-4 w-4 text-cyan-400 shrink-0" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono truncate">{title}</h3>
        </div>
        {action}
      </div>
      <div className="pt-2">{children}</div>
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
  const { simulationState, selectedGapId, selectGap, executeAction } = useFikraCore();
  const gaps = simulationState?.knowledgeGaps || [];
  const unknownEntities = simulationState?.topology?.domains.flatMap((d) => d.entities.filter((e) => e.state === "UNKNOWN")) || [];
  const actions = simulationState?.nextBestActions || [];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-3 h-full min-h-0">
      <Panel title="Knowledge Gap Summary" icon={HelpCircle}>
        <div className="grid grid-cols-3 gap-2 text-center">
          <Metric label="Open gaps" value={gaps.length} tone="amber" />
          <Metric label="Unknown nodes" value={unknownEntities.length} tone="rose" />
          <Metric label="Evidence actions" value={actions.length} tone="cyan" />
        </div>
      </Panel>
      <Panel title="Unknown Boundaries" icon={Compass}>
        <div className="space-y-2">
          {unknownEntities.length ? unknownEntities.map((entity) => (
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
          )) : <SmallEmpty text="No unknown topology boundaries in the current state." />}
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
              <span className="text-[9px] font-bold font-mono text-cyan-300">{action.status}</span>
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
                <span className="text-xs font-bold text-white">{gap.label}</span>
                <span className="text-[9px] font-mono text-amber-300">{gap.priority}</span>
              </div>
              <p className="mt-1 text-[10px] text-slate-400">{gap.reason}</p>
            </button>
          ))}
          {!gaps.length && <SmallEmpty text="No knowledge gaps exposed by the selected scenario." />}
        </div>
      </Panel>
    </div>
  );
}

function LearnWorkspace() {
  const { simulationState } = useFikraCore();
  const learning = simulationState?.learning;
  const learningEnabled = Boolean(learning?.enabled);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-3 h-full min-h-0">
      <Panel title="Candidate Knowledge" icon={GraduationCap}>
        {learningEnabled && learning ? (
          <div className="space-y-3">
            <Metric label="Candidates" value={learning.candidate_count} tone="purple" />
            <p className="text-xs text-slate-300 leading-relaxed">{learning.summary}</p>
            <p className="rounded-md border border-purple-500/30 bg-purple-500/10 p-2 text-[11px] text-purple-100">{learning.rule}</p>
          </div>
        ) : <SmallEmpty text="No validated learning yet." />}
      </Panel>
      <Panel title="SME Validation" icon={ShieldCheck}>
        {learningEnabled && learning ? (
          <StatusList rows={[
            ["Promotion state", learning.status],
            ["Learning enabled", learning.enabled ? "YES" : "NO"],
            ["Confidence", `${Math.round(learning.confidence * 100)}%`],
          ]} />
        ) : <SmallEmpty text="Learning is available after validation starts." />}
      </Panel>
      <Panel title="Before / After" icon={Sparkles}>
        <p className="text-xs text-slate-300 leading-relaxed">
          This workspace is bound to H3 learning state. When a scenario exposes promoted knowledge, the before/after comparison will render from the backend payload rather than fabricated fixtures.
        </p>
      </Panel>
    </div>
  );
}

function PredictWorkspace() {
  const { simulationState, selectedEntityId, selectEntity } = useFikraCore();
  const impact = simulationState?.impact;
  const impactState = impact?.impact_state || impact?.state || "UNKNOWN";
  const hasImpactValues = Boolean(impact && impactState !== "UNKNOWN" && impact.throughput_impact_pct !== null);
  const impacted = hasImpactValues
    ? simulationState?.topology?.domains.flatMap((d) => d.entities.filter((e) => e.state === "IMPACTED" || e.state === "SYMPTOM")) || []
    : [];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-3 h-full min-h-0">
      <Panel title="Blast Radius" icon={Network}>
        {impact && hasImpactValues ? (
          <div className="grid grid-cols-3 gap-2">
            <Metric label="Service impact" value={`${impact.throughput_impact_pct}%`} tone="rose" />
            <Metric label="Regions" value={impact.regions_affected ?? "—"} tone="amber" />
            <Metric label="Users" value={impact.affected_label} tone="cyan" />
          </div>
        ) : <SmallEmpty text={impact ? "Impact is UNKNOWN. No customer-impact evidence yet." : "No impact payload returned for this scenario."} />}
      </Panel>
      <Panel title="Forward Propagation" icon={Activity}>
        <div className="space-y-2">
          {simulationState?.topology?.causal_path.map((edge, index) => (
            <div key={`${edge.from}-${edge.to}-${index}`} className="flex items-center gap-2 text-xs text-slate-300">
              <span className="font-mono text-cyan-300">{edge.from}</span>
              <ArrowRight className="h-3 w-3 text-slate-500" />
              <span className="font-mono text-cyan-300">{edge.to}</span>
              <span className="ml-auto text-[9px] text-slate-500">{edge.relation}</span>
            </div>
          )) || <SmallEmpty text="No propagation path in the current state." />}
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
        <StatusList rows={[
          ["Primary action", "Run next-best evidence"],
          ["Re-simulate", "Available from Simulator Lab"],
          ["Risk basis", impact && hasImpactValues ? impact.service : "No confirmed impact model"],
        ]} />
      </Panel>
    </div>
  );
}

function KnowledgeWorkspace() {
  const { simulationState, scenarioRegistry, scenarioId, selectEntity } = useFikraCore();
  const activeScenario = scenarioRegistry.find((s) => s.id === scenarioId);
  const entities = simulationState?.topology?.domains.flatMap((d) => d.entities.map((entity) => ({ ...entity, domain: d.name }))) || [];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-3 h-full min-h-0">
      <Panel title="Knowledge Summary" icon={Database}>
        <StatusList rows={[
          ["Source", activeScenario?.source || "live_telecombrain"],
          ["Stage", activeScenario?.stage || simulationState?.scenario?.stage || "-"],
          ["Status", activeScenario?.status || simulationState?.scenario?.status || "-"],
        ]} />
      </Panel>
      <Panel title="Domain Coverage" icon={BarChart3}>
        <div className="grid grid-cols-2 gap-2">
          {(simulationState?.topology?.domains || []).map((domain) => (
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
          {!simulationState?.knowledgeGaps?.length && <SmallEmpty text="No gaps, orphans, or stale records surfaced by current state." />}
        </div>
      </Panel>
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

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-3 h-full min-h-0">
      <Panel title="Scenario Library" icon={Search}>
        <div className="max-h-[56vh] overflow-y-auto custom-scrollbar space-y-2 pr-1">
          {scenarioRegistry.map((scenario) => (
            <button
              key={scenario.id}
              onClick={() => selectScenario(scenario.id)}
              className={cn(
                "w-full rounded-md border p-2 text-left transition-colors",
                scenarioId === scenario.id ? "border-cyan-400 bg-cyan-500/10" : "border-slate-800 bg-slate-900/50 hover:border-cyan-400/50"
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold text-white">{scenario.display_name}</span>
                <span className="text-[9px] font-mono text-purple-300">{scenario.stage}</span>
              </div>
              <p className="mt-1 text-[10px] text-slate-400">{scenario.id} · {scenario.domains.join(", ") || "No domains tagged"}</p>
            </button>
          ))}
          {!scenarioRegistry.length && <SmallEmpty text="Scenario registry has not returned entries yet." />}
        </div>
      </Panel>
      <Panel title="Run Controls" icon={Play}>
        <div className="grid grid-cols-4 gap-2">
          <button onClick={() => startSimulation(scenarioId ?? "SCN-001")} className="rounded-md border border-emerald-500/40 bg-emerald-500/10 p-3 text-xs font-bold text-emerald-300">Start</button>
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
    </div>
  );
}

function BenchmarkWorkspace() {
  const { simulationState, scenarioRegistry } = useFikraCore();
  const hypotheses = simulationState?.hypotheses || [];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-3 h-full min-h-0">
      <Panel title="H1-H4 Results" icon={BarChart3}>
        <div className="grid grid-cols-4 gap-2">
          {["H1", "H2", "H3", "H4"].map((stage) => (
            <Metric key={stage} label={stage} value={scenarioRegistry.filter((s) => s.stage === stage).length} tone="cyan" />
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

function Metric({ label, value, tone }: { label: string; value: React.ReactNode; tone: "cyan" | "amber" | "rose" | "purple" }) {
  return (
    <div className={cn(
      "rounded-md border p-2",
      tone === "cyan" && "border-cyan-500/30 bg-cyan-500/10",
      tone === "amber" && "border-amber-500/30 bg-amber-500/10",
      tone === "rose" && "border-rose-500/30 bg-rose-500/10",
      tone === "purple" && "border-purple-500/30 bg-purple-500/10"
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
        <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-3">
          {body}
        </div>
      </div>
    </StateShell>
  );
}
