"use client";

import React, { useEffect, useState, useRef, Suspense } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Activity,
  BarChart3,
  Bell,
  Check,
  ChevronDown,
  ChevronUp,
  Compass,
  Cpu,
  Database,
  GraduationCap,
  Loader2,
  Microscope,
  Moon,
  MoreHorizontal,
  Network,
  Pause,
  Play,
  Search,
  Send,
  Sparkles,
  Square,
  Sun,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/api/config";
import {
  FikraCoreProvider,
  DEFAULT_SCENARIO_REGISTRY,
  Workspace,
  ResponseLevel,
  buildZakiContextEnvelope,
  getWorkspaceSuggestions,
  useFikraCore,
} from "@/lib/fikracore-context";

// ─── Workspace nav configuration ─────────────────────────────────────────────

const WORKSPACE_TABS: {
  id: Workspace;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  route: string;
}[] = [
  { id: "investigate", label: "Investigate", icon: Microscope, route: "/simulator/investigate" },
  { id: "discover", label: "Discover", icon: Compass, route: "/simulator/discover" },
  { id: "learn", label: "Learn", icon: GraduationCap, route: "/simulator/learn" },
  { id: "predict", label: "Predict", icon: Network, route: "/simulator/predict" },
  { id: "knowledge", label: "Knowledge Core", icon: Database, route: "/simulator/knowledge" },
  { id: "lab", label: "Simulator Lab", icon: Cpu, route: "/simulator/lab" },
  { id: "benchmarks", label: "Benchmarks", icon: BarChart3, route: "/simulator/benchmarks" },
];

const SCN_TOP_10_IDS = [
  "SCN-001",
  "SCN-002",
  "SCN-003",
  "SCN-004",
  "SCN-005",
  "SCN-006",
  "SCN-007",
  "SCN-008",
  "SCN-009",
  "SCN-010",
];

// ─── Floating Zaki Copilot (used for other workspaces) ────────────────────────

function ZakiCopilot() {
  const {
    activeWorkspace,
    simulationState,
    scenarioId,
    runId,
    selectedEntityId,
    selectedServiceId,
    selectedHypothesisId,
    selectedGapId,
    selectedEvidenceId,
    responseLevel,
    setResponseLevel,
    scenarioRegistry,
    scenarioRegistryLoading,
    syncState,
    theme,
  } = useFikraCore();

  const [expanded, setExpanded] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [chat, setChat] = React.useState<{ sender: "user" | "zaki"; text: string }[]>([]);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const phase = simulationState?.zaki?.phase || "OBSERVING";
  const thought = simulationState?.zaki?.thought;
  const suggestions = getWorkspaceSuggestions(activeWorkspace, selectedEntityId);

  useEffect(() => {
    if (expanded) messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, expanded]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    await sendQuery(query.trim());
    setQuery("");
  };

  const sendQuery = async (userMsg: string) => {
    setChat((prev) => [...prev, { sender: "user", text: userMsg }]);
    setIsLoading(true);

    const envelope = buildZakiContextEnvelope(
      {
        activeWorkspace,
        simulationState,
        scenarioId,
        runId,
        selectedEntityId,
        selectedHypothesisId,
        selectedGapId,
        selectedEvidenceId,
        selectedServiceId,
        responseLevel,
        scenarioRegistry,
        scenarioRegistryLoading,
        syncState,
        connectionState: simulationState?.connectionState || "CONNECTING",
        lastUpdate: simulationState?.lastUpdate || "",
        theme,
      },
      userMsg
    );

    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/zaki/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(envelope),
      });

      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      const reply =
        typeof data.response === "string"
          ? data.response
          : data.response?.response || "Analysis complete.";
      setChat((prev) => [...prev, { sender: "zaki", text: reply }]);
    } catch {
      const fallback = `[${activeWorkspace.toUpperCase()} • ${scenarioId}] ${
        simulationState?.zaki?.thought || "Analyzing current state across telecombrain knowledge graph."
      }`;
      setChat((prev) => [...prev, { sender: "zaki", text: fallback }]);
    } finally {
      setIsLoading(false);
    }
  };

  const phaseConfig = {
    RECOMMENDATION_READY: { label: "Recommendation Ready", color: "emerald", ping: true },
    EVIDENCE_NEEDED: { label: "Needs Evidence", color: "amber", ping: false },
    REASONING: { label: "Reasoning", color: "cyan", ping: true },
    OBSERVING: { label: "Observing", color: "blue", ping: false },
  }[phase] ?? { label: "Idle", color: "slate", ping: false };

  const RESPONSE_LEVELS: { value: ResponseLevel; label: string }[] = [
    { value: "executive", label: "Executive" },
    { value: "operator", label: "Operator" },
    { value: "engineer", label: "Engineer" },
    { value: "deep_technical", label: "Deep Technical" },
  ];

  return (
    <div className="rounded-xl border border-cyan-500/40 bg-gradient-to-br from-[#0a1226] to-[#0e1834] p-3 shadow-xl relative overflow-hidden shrink-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-purple-600 text-white shadow-[0_0_15px_rgba(0,229,255,0.4)]">
            <Activity className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold text-white font-mono tracking-wider">ZAKI AI</span>
              <span
                className={cn(
                  "flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded font-mono font-bold border",
                  phaseConfig.color === "emerald" && "text-emerald-300 bg-emerald-500/20 border-emerald-400/40",
                  phaseConfig.color === "amber" && "text-amber-300 bg-amber-500/20 border-amber-400/40",
                  phaseConfig.color === "cyan" && "text-cyan-300 bg-cyan-500/20 border-cyan-400/40",
                  phaseConfig.color === "blue" && "text-blue-300 bg-blue-500/20 border-blue-400/40",
                  phaseConfig.color === "slate" && "text-slate-300 bg-slate-800 border-slate-700"
                )}
              >
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    phaseConfig.color === "emerald" && "bg-emerald-400",
                    phaseConfig.color === "amber" && "bg-amber-400",
                    phaseConfig.color === "cyan" && "bg-cyan-400",
                    phaseConfig.color === "blue" && "bg-blue-400",
                    phaseConfig.color === "slate" && "bg-slate-400",
                    phaseConfig.ping && "animate-ping"
                  )}
                />
                {phaseConfig.label}
              </span>
            </div>
            <p className="text-[9px] text-slate-400 font-mono">{activeWorkspace.toUpperCase()} context</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <select
            value={responseLevel}
            onChange={(e) => setResponseLevel(e.target.value as ResponseLevel)}
            className="text-[9px] font-mono bg-slate-900 border border-slate-700 text-slate-300 rounded px-1.5 py-0.5 focus:outline-none focus:border-cyan-400 cursor-pointer"
          >
            {RESPONSE_LEVELS.map((l) => (
              <option key={l.value} value={l.value}>
                {l.label}
              </option>
            ))}
          </select>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {thought && (
        <div className="mt-2 px-2.5 py-1.5 rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-[10px] text-cyan-200 flex items-start gap-1.5 leading-snug">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400 shrink-0 mt-0.5" />
          <span className="font-mono">
            <strong className="text-cyan-300">Insight:</strong> {thought}
          </span>
        </div>
      )}

      {expanded && (
        <>
          <div className="mt-2 pt-2 border-t border-slate-800/80 grid grid-cols-2 gap-1 text-[9px] font-mono text-slate-400">
            <span>Scenario: <span className="text-slate-200">{scenarioId || "—"}</span></span>
            <span>Workspace: <span className="text-cyan-300">{activeWorkspace}</span></span>
            <span>Stage: <span className="text-slate-200">{simulationState?.current_stage || "—"}</span></span>
            {selectedEntityId && <span>Entity: <span className="text-amber-300">{selectedEntityId}</span></span>}
            {selectedHypothesisId && <span>Hypothesis: <span className="text-purple-300">{selectedHypothesisId}</span></span>}
            {selectedGapId && <span>Gap: <span className="text-rose-300">{selectedGapId}</span></span>}
          </div>

          <div className="mt-2 flex flex-wrap gap-1">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => sendQuery(s)}
                className="text-[9px] px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 cursor-pointer transition-colors"
              >
                {s}
              </button>
            ))}
          </div>

          <div className="mt-3 pt-3 border-t border-slate-800/80 max-h-48 overflow-y-auto custom-scrollbar space-y-2 text-xs">
            {chat.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  "p-2 rounded-lg leading-relaxed text-[11px]",
                  msg.sender === "user"
                    ? "ml-auto bg-cyan-500/20 border border-cyan-500/40 text-cyan-100 max-w-[90%]"
                    : "mr-auto bg-slate-900 border border-slate-800 text-slate-200 max-w-[95%]"
                )}
              >
                <div className="text-[8px] font-mono text-slate-400 mb-0.5">
                  {msg.sender === "user" ? "OPERATOR" : `ZAKI AI • telecombrain • ${responseLevel.toUpperCase()}`}
                </div>
                <div className="whitespace-pre-wrap">{msg.text}</div>
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center gap-1.5 text-cyan-300 text-[10px] font-mono">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Zaki is synthesizing {activeWorkspace} context...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </>
      )}

      <form onSubmit={handleSubmit} className="mt-2.5 flex items-center gap-1.5">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={`Ask about ${activeWorkspace}...`}
          className="flex-1 bg-[#060b17] border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400"
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="p-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md hover:brightness-110 disabled:opacity-40 cursor-pointer"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </form>
    </div>
  );
}

// ─── 8 Connected Stages Live Simulation Journey Stepper ───────────────────────

const JOURNEY_STAGES = [
  { index: 0, key: "trigger", label: "Trigger", subtitle: "Incident detected", type: "check" },
  { index: 1, key: "signal_flood", label: "Signal Flood", subtitle: "Events ingested", type: "check" },
  { index: 2, key: "correlation", label: "Correlation", subtitle: "Linking domains", type: "check" },
  { index: 3, key: "hypothesis_gen", label: "Hypothesis Gen", subtitle: "Candidate causes", type: "check" },
  { index: 4, key: "hypothesis_testing", label: "Hypothesis Testing", subtitle: "Testing evidence", type: "check" },
  { index: 5, key: "knowledge_gaps", label: "Knowledge Gaps", subtitle: "Finding missing context", type: "question" },
  { index: 6, key: "validation", label: "Validation", subtitle: "Human expertise", type: "number", count: "2" },
  { index: 7, key: "action", label: "Action", subtitle: "Generate next best action", type: "number", count: "8" },
];

function JourneyStepper() {
  const { theme, simulationState } = useFikraCore();
  const isLight = theme === "light";

  const isRunningOrPaused =
    simulationState?.run?.status === "RUNNING" ||
    simulationState?.run_status === "RUNNING" ||
    simulationState?.run?.status === "PAUSED" ||
    simulationState?.run_status === "PAUSED" ||
    simulationState?.run?.status === "COMPLETED" ||
    simulationState?.run_status === "COMPLETED";

  const rawStageIndex =
    simulationState?.stages?.find((s) => s.status === "ACTIVE")?.index ??
    simulationState?.run?.stage_index ??
    (simulationState?.current_stage
      ? JOURNEY_STAGES.findIndex(
          (s) =>
            s.key.toLowerCase() === simulationState.current_stage?.toLowerCase() ||
            s.label.toLowerCase() === simulationState.current_stage?.toLowerCase()
        )
      : -1);

  const currentStageIndex = isRunningOrPaused ? rawStageIndex : -1;

  const isCompleted =
    simulationState?.run?.status === "COMPLETED" ||
    simulationState?.stage_status === "COMPLETED" ||
    (isRunningOrPaused && currentStageIndex >= 7 && simulationState?.terminal_state != null);

  const isBlocked = isRunningOrPaused && simulationState?.stage_status === "BLOCKED";

  // Dynamic progress line percent
  const progressPercent = isCompleted
    ? 100
    : currentStageIndex >= 0
    ? Math.min(100, Math.round(((currentStageIndex + (isBlocked ? 0.5 : 0)) / (JOURNEY_STAGES.length - 1)) * 100))
    : 0;

  return (
    <section
      className={cn(
        "relative flex items-center justify-between px-6 py-2 shrink-0 overflow-x-auto custom-scrollbar border-b transition-colors duration-200",
        isLight ? "bg-slate-50 border-slate-200 text-slate-900" : "bg-[#050c1b] border-cyan-500/15 text-slate-100"
      )}
    >
      <div className="relative flex items-center justify-between w-full max-w-7xl mx-auto px-4">
        {/* Continuous Connecting line */}
        <div
          className={cn(
            "absolute left-8 right-8 top-4 h-[2px] -z-0",
            isLight ? "bg-slate-300" : "bg-slate-800/80"
          )}
        />
        {/* Completed green line driven dynamically by simulation progress */}
        <div
          style={{ width: `${progressPercent}%` }}
          className="absolute left-8 top-4 h-[2px] bg-gradient-to-r from-emerald-400 via-emerald-400 to-cyan-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] -z-0 transition-all duration-500 max-w-[calc(100%-4rem)]"
        />

        {JOURNEY_STAGES.map((st, i) => {
          const isDone = isCompleted || (currentStageIndex >= 0 && i < currentStageIndex);
          const isActive = !isCompleted && i === currentStageIndex;
          const isPending = !isCompleted && (currentStageIndex < 0 ? true : i > currentStageIndex);

          return (
            <div key={st.key} className="relative z-10 flex flex-col items-center text-center group cursor-pointer">
              {/* Circle Icon */}
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full transition-all duration-300 font-mono text-xs font-bold",
                  isDone &&
                    (isLight
                      ? "bg-emerald-100 border-2 border-emerald-500 text-emerald-800"
                      : "bg-[#062c22] border-2 border-emerald-400 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.5)]"),
                  isActive &&
                    (isBlocked
                      ? isLight
                        ? "bg-amber-100 border-2 border-amber-500 text-amber-900 shadow-[0_0_15px_rgba(245,158,11,0.4)] scale-110 animate-pulse"
                        : "bg-[#2d1c07] border-2 border-amber-400 text-amber-200 shadow-[0_0_20px_rgba(251,191,36,0.8)] scale-110 animate-pulse"
                      : isLight
                      ? "bg-cyan-100 border-2 border-cyan-500 text-cyan-900 shadow-[0_0_15px_rgba(6,182,212,0.4)] scale-110 animate-pulse"
                      : "bg-[#073b64] border-2 border-cyan-400 text-cyan-200 shadow-[0_0_20px_rgba(34,211,238,0.9)] scale-110 animate-pulse"),
                  isPending &&
                    (isLight
                      ? "bg-white border border-slate-300 text-slate-500 hover:border-slate-400"
                      : "bg-[#0a1426] border border-slate-700 text-slate-400 hover:border-slate-500")
                )}
              >
                {isDone && <Check className="h-4 w-4 stroke-[3]" />}
                {isActive && (isBlocked ? <span className="font-bold text-sm">?</span> : <span>{i + 1}</span>)}
                {isPending && <span>{st.count || i + 1}</span>}
              </div>

              {/* Label & Subtitle */}
              <div className="mt-1.5">
                <p
                  className={cn(
                    "text-[11px] font-semibold whitespace-nowrap leading-none",
                    isActive
                      ? isLight
                        ? "text-cyan-700 font-bold"
                        : "text-cyan-300 font-bold drop-shadow-[0_0_8px_rgba(34,211,238,0.7)]"
                      : isDone
                      ? isLight
                        ? "text-slate-800 font-semibold"
                        : "text-slate-200"
                      : isLight
                      ? "text-slate-500"
                      : "text-slate-400"
                  )}
                >
                  {st.label}
                </p>
                <p
                  className={cn(
                    "text-[9px] mt-0.5 whitespace-nowrap hidden lg:block",
                    isLight ? "text-slate-500" : "text-slate-500"
                  )}
                >
                  {st.subtitle}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ─── Inner layout (consumes FikraCore context) ─────────────────────────────────

function SimulatorShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const {
    simulationState,
    scenarioId,
    runId,
    scenarioRegistry,
    selectScenario,
    setActiveWorkspace,
    startSimulation,
    pauseSimulation,
    resumeSimulation,
    stopSimulation,
    theme,
    toggleTheme,
  } = useFikraCore();

  const isLight = theme === "light";
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  // Sync active workspace from URL
  useEffect(() => {
    const segment = pathname.split("/")[2] as Workspace;
    if (segment && WORKSPACE_TABS.find((t) => t.id === segment)) {
      setActiveWorkspace(segment);
    }
  }, [pathname, setActiveWorkspace]);

  const isInternalChangeRef = useRef<boolean>(false);

  // Sync from URL only when the URL parameter changes externally (e.g. browser back/forward or initial load)
  useEffect(() => {
    const scenarioFromUrl = searchParams.get("scenario");
    if (isInternalChangeRef.current) {
      isInternalChangeRef.current = false;
      return;
    }
    if (scenarioFromUrl && scenarioFromUrl !== scenarioId) {
      selectScenario(scenarioFromUrl);
    }
  }, [searchParams, scenarioId, selectScenario]);

  const activeWorkspace = (pathname.split("/")[2] || "investigate") as Workspace;

  const displayScenarios = mounted ? scenarioRegistry : DEFAULT_SCENARIO_REGISTRY;

  const filteredScenarios = SCN_TOP_10_IDS.map((id) => {
    return (
      displayScenarios.find((s) => s.id === id || s.aliases?.includes(id)) || {
        id,
        display_name: id,
        description: "",
      }
    );
  });

  const activeScenarioEntry = scenarioId
    ? displayScenarios.find((s) => s.id === scenarioId || s.aliases?.includes(scenarioId)) || null
    : null;

  const handleScenarioChange = (newId: string) => {
    if (!newId) return;
    isInternalChangeRef.current = true;
    selectScenario(newId);
    const params = new URLSearchParams(searchParams.toString());
    params.set("scenario", newId);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const [isStarting, setIsStarting] = useState(false);
  const runStatus = simulationState?.run?.status || simulationState?.run_status;
  const isRunning = runStatus === "RUNNING" || isStarting;
  const isPaused = runStatus === "PAUSED" && !isStarting;

  return (
    <div
      className={cn(
        "relative flex flex-col h-full overflow-hidden font-sans transition-colors duration-200",
        isLight ? "bg-slate-100 text-slate-900 light-theme" : "bg-[#050b18] text-slate-100"
      )}
    >
      {/* ── ROW 1: PRIMARY TOP NAVIGATION BAR ── */}
      <header
        className={cn(
          "flex items-center justify-between px-5 py-2.5 border-b backdrop-blur-md shrink-0 gap-4 transition-colors duration-200",
          isLight ? "bg-white border-slate-200 text-slate-900 shadow-sm" : "bg-[#070f22]/95 border-cyan-500/15 text-slate-100"
        )}
      >
        {/* Left: Brand */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 shadow-[0_0_12px_rgba(0,229,255,0.4)]">
            <Network className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <h1 className={cn("text-sm font-extrabold tracking-wide flex items-center gap-1.5", isLight ? "text-slate-900" : "text-white")}>
              FikraCore
            </h1>
            <p className={cn("text-[9px] font-mono tracking-wider uppercase", isLight ? "text-cyan-700" : "text-cyan-400/80")}>
              AI-Native Telecom Intelligence
            </p>
          </div>
        </div>

        {/* Center: Workspace Navigation Tabs */}
        <nav className="flex items-center gap-1.5 overflow-x-auto custom-scrollbar">
          {WORKSPACE_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeWorkspace === tab.id;

            return (
              <Link
                key={tab.id}
                href={scenarioId ? `${tab.route}?scenario=${scenarioId}` : tab.route}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap",
                  isActive
                    ? isLight
                      ? "bg-cyan-100 text-cyan-900 border border-cyan-400 font-bold shadow-sm"
                      : "bg-[#0d2a4a] text-cyan-300 border border-cyan-400/70 shadow-[0_0_14px_rgba(0,229,255,0.3)] font-bold"
                    : isLight
                    ? "text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent"
                    : "text-slate-400 hover:text-white hover:bg-slate-900/60 border border-transparent"
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{tab.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right: Search, Notifications, Avatar */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="relative flex items-center">
            <Search className="absolute left-2.5 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Search scenarios, events, or ask Zaki..."
              className={cn(
                "w-64 rounded-lg pl-8 pr-9 py-1 text-xs font-sans transition-colors focus:outline-none",
                isLight
                  ? "bg-slate-100 border border-slate-300 text-slate-900 placeholder-slate-400 focus:border-cyan-500"
                  : "bg-[#0a152d] border border-slate-700/80 text-slate-200 placeholder-slate-400 focus:border-cyan-400"
              )}
            />
            <span
              className={cn(
                "absolute right-2 px-1 py-0.2 rounded text-[10px] font-mono border",
                isLight ? "bg-white text-slate-500 border-slate-300" : "bg-slate-800 text-slate-400 border-slate-700"
              )}
            >
              ⌘K
            </span>
          </div>

          {/* Notification bell with red dot */}
          <button
            type="button"
            className={cn(
              "relative p-1.5 rounded-lg transition-colors",
              isLight ? "text-slate-600 hover:text-slate-900 hover:bg-slate-100" : "text-slate-400 hover:text-white hover:bg-slate-800/80"
            )}
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-white dark:ring-[#070f22]" />
          </button>

          {/* Clean Segmented Dark/Light Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${isLight ? "dark" : "light"} mode`}
            title={`Switch to ${isLight ? "dark" : "light"} mode`}
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono font-medium cursor-pointer transition-all duration-200 shadow-sm",
              isLight
                ? "bg-slate-100 hover:bg-slate-200 border-slate-300 text-slate-800"
                : "bg-slate-900/90 hover:bg-slate-800 border-slate-700 text-slate-300"
            )}
          >
            {isLight ? (
              <>
                <Sun className="h-3.5 w-3.5 text-amber-500" />
                <span className="text-[10px] font-bold">LIGHT</span>
              </>
            ) : (
              <>
                <Moon className="h-3.5 w-3.5 text-cyan-400" />
                <span className="text-[10px] font-bold">DARK</span>
              </>
            )}
          </button>

          {/* User Avatar */}
          <div
            className={cn(
              "h-7 w-7 rounded-full text-xs font-bold flex items-center justify-center shadow-inner",
              isLight ? "bg-slate-200 border border-slate-300 text-slate-800" : "bg-slate-800 border border-slate-700 text-slate-200"
            )}
          >
            AS
          </div>
        </div>
      </header>

      {/* ── ROW 2: SCENARIO SUBHEADER & CONTROLS ── */}
      <section
        className={cn(
          "flex items-center justify-between px-5 py-2 border-b backdrop-blur-md shrink-0 gap-4 transition-colors duration-200",
          isLight ? "bg-white border-slate-200 text-slate-900 shadow-sm" : "bg-[#061226]/90 border-cyan-500/10 text-slate-100"
        )}
      >
        {/* Left: Scenario Dropdown & Info */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/15 border border-blue-400/30 text-blue-300 shadow-[0_0_10px_rgba(59,130,246,0.3)]">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={cn("text-[10px] font-mono uppercase tracking-wider font-semibold", isLight ? "text-slate-500" : "text-slate-400")}>
                Scenario
              </span>
              <div
                className={cn(
                  "relative flex items-center rounded-lg border px-2.5 py-1 transition-all duration-150 shadow-sm",
                  isLight
                    ? "bg-slate-50 border-slate-300 hover:border-cyan-500 hover:bg-white text-slate-900"
                    : "bg-[#09152b] border-cyan-500/30 hover:border-cyan-400 hover:bg-[#0c1c38] text-white"
                )}
              >
                <select
                  suppressHydrationWarning
                  value={scenarioId || ""}
                  onChange={(e) => handleScenarioChange(e.target.value)}
                  className="bg-transparent text-xs font-bold cursor-pointer focus:outline-none pr-6 appearance-none max-w-[420px] truncate"
                >
                  <option
                    value=""
                    disabled
                    className={isLight ? "bg-white text-slate-500 font-normal" : "bg-slate-900 text-slate-400 font-normal"}
                  >
                    Select the scenario
                  </option>
                  {filteredScenarios.map((sc) => (
                    <option
                      key={sc.id}
                      value={sc.id}
                      className={isLight ? "bg-white text-slate-900 font-medium" : "bg-slate-900 text-slate-200 font-medium"}
                    >
                      {sc.id} · {sc.display_name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2.5 h-3.5 w-3.5 text-cyan-400 pointer-events-none" />
              </div>
            </div>
            <p className={cn("text-[10px] leading-tight mt-0.5", isLight ? "text-slate-600" : "text-slate-400")}>
              {activeScenarioEntry?.description || "Select a scenario to begin investigation"}
            </p>
          </div>
        </div>

        {/* Center-Left: Run Identifier & Start Time */}
        <div className={cn("hidden md:flex items-center gap-3 pl-4 border-l", isLight ? "border-slate-300" : "border-slate-800/80")}>
          <div>
            <div className={cn("flex items-center gap-1 text-xs font-mono font-semibold", isLight ? "text-slate-900" : "text-white")}>
              <span className={isLight ? "text-slate-500 font-normal" : "text-slate-400 font-normal"}>Run</span>
              <span>{simulationState?.run?.run_id || (simulationState as any)?.run_id || runId || "RUN-LIVE"}</span>
              <span className={cn("px-1 py-0.2 rounded text-[9px] border", isLight ? "bg-slate-100 text-slate-700 border-slate-300" : "bg-slate-800 text-slate-400 border-slate-700")}>B</span>
            </div>
            <p className={cn("text-[10px] font-mono", isLight ? "text-slate-500" : "text-slate-400")}>
              {(() => {
                const started = simulationState?.run?.started_at || (simulationState as any)?.started_at;
                if (!started) return "Active Run Context";
                const d = new Date(started);
                return isNaN(d.getTime())
                  ? `Started ${started}`
                  : `Started ${d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })}, ${d.toLocaleTimeString("en-GB", { hour12: false })}`;
              })()}
            </p>
          </div>
        </div>

        {/* Center: Dynamic Simulation Status Pill */}
        {(() => {
          const status = isStarting ? "RUNNING" : (simulationState?.run?.status || simulationState?.run_status);
          if (status === "RUNNING") {
            return (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-700 dark:text-emerald-300 text-xs font-bold shadow-sm">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Running</span>
              </div>
            );
          }
          if (status === "PAUSED") {
            return (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/40 text-amber-700 dark:text-amber-300 text-xs font-bold shadow-sm">
                <Pause className="h-3 w-3 text-amber-500" />
                <span>Paused</span>
              </div>
            );
          }
          if (status === "BLOCKED") {
            return (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/40 text-amber-700 dark:text-amber-300 text-xs font-bold shadow-sm">
                <span className="h-2 w-2 rounded-full bg-amber-400 animate-ping" />
                <span>Blocked</span>
              </div>
            );
          }
          if (status === "COMPLETED") {
            return (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/15 border border-cyan-500/40 text-cyan-700 dark:text-cyan-300 text-xs font-bold shadow-sm">
                <Check className="h-3 w-3 text-cyan-400" />
                <span>Completed</span>
              </div>
            );
          }
          if (status === "STOPPED") {
            return (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/15 border border-rose-500/40 text-rose-700 dark:text-rose-300 text-xs font-bold shadow-sm">
                <Square className="h-2.5 w-2.5 fill-rose-500 text-rose-500" />
                <span>Stopped</span>
              </div>
            );
          }
          return (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-500/15 border border-slate-500/40 text-slate-500 dark:text-slate-400 text-xs font-bold shadow-sm">
              <span className="h-2 w-2 rounded-full bg-slate-400" />
              <span>Ready</span>
            </div>
          );
        })()}

        {/* Center-Right: Dynamic Stage Label */}
        <div className="hidden lg:flex flex-col">
          <span className={cn("text-[10px] font-mono uppercase tracking-wider", isLight ? "text-slate-500" : "text-slate-400")}>Stage</span>
          <span className={cn("text-xs font-bold", isLight ? "text-slate-900" : "text-slate-200")}>
            {(() => {
              const activeIdx =
                simulationState?.stages?.find((s) => s.status === "ACTIVE")?.index ??
                simulationState?.run?.stage_index ??
                (simulationState?.current_stage
                  ? JOURNEY_STAGES.findIndex(
                      (s) =>
                        s.key.toLowerCase() === simulationState.current_stage?.toLowerCase() ||
                        s.label.toLowerCase() === simulationState.current_stage?.toLowerCase()
                    )
                  : -1);
              return simulationState?.current_stage
                ? JOURNEY_STAGES.find(
                    (s) =>
                      s.key.toLowerCase() === simulationState.current_stage?.toLowerCase() ||
                      s.label.toLowerCase() === simulationState.current_stage?.toLowerCase()
                  )?.label || simulationState.current_stage
                : activeIdx >= 0
                ? JOURNEY_STAGES[activeIdx]?.label || "Trigger"
                : "Trigger";
            })()}
          </span>
        </div>

        {/* Right: Simulation Controls */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Pause / Play */}
          <button
            type="button"
            disabled={!scenarioId || isStarting}
            onClick={async () => {
              if (!scenarioId) return;
              if (isRunning) {
                await pauseSimulation();
              } else if (isPaused) {
                await resumeSimulation();
              } else {
                setIsStarting(true);
                try {
                  await startSimulation(scenarioId);
                } finally {
                  setIsStarting(false);
                }
              }
            }}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shadow-sm border",
              !scenarioId || isStarting
                ? isLight
                  ? "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
                  : "bg-slate-800/40 text-slate-600 border-slate-700/40 cursor-not-allowed"
                : isLight
                ? "bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300 cursor-pointer"
                : "bg-slate-800/90 hover:bg-slate-700 text-slate-200 border-slate-700 cursor-pointer"
            )}
          >
            {isRunning ? (
              <>
                <Pause className="h-3.5 w-3.5 text-cyan-600 dark:text-cyan-300" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-300" />
                <span>Play</span>
              </>
            )}
          </button>

          {/* Stop Button (Active whenever simulation is running/paused or active run exists) */}
          {(() => {
            const hasRun = Boolean(simulationState?.run || simulationState?.run_id);
            const isStopDisabled =
              !hasRun ||
              runStatus === "STOPPED" ||
              runStatus === "COMPLETED";

            return (
              <button
                type="button"
                onClick={stopSimulation}
                disabled={isStopDisabled}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-colors",
                  isStopDisabled
                    ? isLight
                      ? "bg-slate-200 text-slate-400 border border-slate-300 cursor-not-allowed"
                      : "bg-slate-800/40 text-slate-500 border border-slate-700/40 cursor-not-allowed"
                    : "bg-rose-600/90 hover:bg-rose-500 text-white cursor-pointer"
                )}
              >
                <Square className="h-3 w-3 fill-current" />
                <span>Stop</span>
              </button>
            );
          })()}

          {/* More options button */}
          <button
            type="button"
            className={cn(
              "p-1.5 rounded-lg border cursor-pointer",
              isLight ? "bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300" : "bg-slate-800/80 hover:bg-slate-700 text-slate-300 border-slate-700"
            )}
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </div>
      </section>

      {/* ── ROW 3: LIVE SIMULATION JOURNEY STEPPER ── */}
      <JourneyStepper />

      {/* ── ROW 4: MAIN WORKSPACE CONTENT ── */}
      <main className="flex-1 min-h-0 overflow-hidden flex flex-col">
        {children}
      </main>

      {/* Floating Zaki (only active on workspaces other than investigate, since investigate embeds Zaki) */}
      {activeWorkspace !== "investigate" && (
        <div className="absolute bottom-4 right-4 z-40 w-[360px] max-w-[calc(100vw-2rem)] shadow-2xl shadow-cyan-900/20">
          <ZakiCopilot />
        </div>
      )}
    </div>
  );
}

// ─── Exported Layout ──────────────────────────────────────────────────────────

export default function SimulatorLayout({ children }: { children: React.ReactNode }) {
  return (
    <FikraCoreProvider>
      <Suspense fallback={null}>
        <SimulatorShell>{children}</SimulatorShell>
      </Suspense>
    </FikraCoreProvider>
  );
}
