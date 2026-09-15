"use client";

/**
 * FikraCore Shared Application State (spec §4, §8, §14, §20).
 *
 * Single source of truth across all 7 workspace routes:
 * - Scenario registry (backend-discovered, never hardcoded)
 * - Active scenario/run context
 * - Selection state (entity, hypothesis, gap, evidence)
 * - Zaki context auto-update on selection changes
 * - Cross-panel synchronization
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { API_BASE } from "@/lib/api/config";
import {
  SimulationClient,
  SimulationState,
} from "@/lib/simulation-store";

// ─── Workspace Types ─────────────────────────────────────────────────────────

export type Workspace =
  | "investigate"
  | "discover"
  | "learn"
  | "predict"
  | "knowledge"
  | "lab"
  | "benchmarks";

export type ResponseLevel = "executive" | "operator" | "engineer" | "deep_technical";

export type SyncState =
  | "IDLE"
  | "SWITCHING_SCENARIO"
  | "LOADING_SNAPSHOT"
  | "CONNECTING_LIVE_STREAM"
  | "SYNCED"
  | "RESYNCING"
  | "DISCONNECTED"
  | "ERROR";

// ─── Scenario Registry (§5, §6) ──────────────────────────────────────────────

export interface ScenarioCapabilities {
  investigate: boolean;
  discover: boolean;
  learn: boolean;
  predict: boolean;
  knowledge: boolean;
  lab: boolean;
  benchmarks: boolean;
}

export interface ScenarioRegistryEntry {
  id: string;
  display_name: string;
  description: string;
  stage: string;          // H1 / H2 / H3 / H4
  aliases: string[];
  tags: string[];
  domains: string[];
  services: string[];
  difficulty: string;
  status: string;
  source: string;
  capabilities: ScenarioCapabilities;
  demo_enabled: boolean;
}

// ─── Full Application State (§4) ─────────────────────────────────────────────

export interface FikraCoreAppState {
  activeWorkspace: Workspace;

  // Scenario registry (all available scenarios)
  scenarioRegistry: ScenarioRegistryEntry[];
  scenarioRegistryLoading: boolean;

  // Active context (shared across workspaces)
  scenarioId: string | null;
  runId: string | null;

  // Selection state (cross-panel sync §14)
  selectedEntityId: string | null;
  selectedServiceId: string | null;
  selectedHypothesisId: string | null;
  selectedGapId: string | null;
  selectedEvidenceId: string | null;

  // Zaki response level (§19)
  responseLevel: ResponseLevel;

  // Live simulation state (from SimulationClient SSE)
  simulationState: SimulationState | null;

  // Sync state machine (spec §13)
  syncState: SyncState;

  // Connection status
  connectionState: "LIVE" | "CONNECTING" | "DEGRADED" | "DISCONNECTED";
  lastUpdate: string;

  // Theme state
  theme?: "dark" | "light";
}

// ─── Context Actions ──────────────────────────────────────────────────────────

export interface FikraCoreActions {
  setActiveWorkspace: (workspace: Workspace) => void;
  selectScenario: (scenarioId: string) => Promise<void>;
  selectEntity: (entityId: string | null) => void;
  selectService: (serviceId: string | null) => void;
  selectHypothesis: (hypothesisId: string | null) => void;
  selectGap: (gapId: string | null) => void;
  selectEvidence: (evidenceId: string | null) => void;
  setResponseLevel: (level: ResponseLevel) => void;
  refreshRegistry: () => Promise<void>;
  startSimulation: (scenarioId?: string) => Promise<void>;
  pauseSimulation: () => Promise<void>;
  resumeSimulation: () => Promise<void>;
  stopSimulation: () => Promise<void>;
  replaySimulation: () => Promise<void>;
  executeAction: (actionId: string) => Promise<void>;
  toggleTheme: () => void;
  setTheme: (theme: "dark" | "light") => void;
}

// ─── Context Definition ───────────────────────────────────────────────────────

const FikraCoreStateCtx = createContext<FikraCoreAppState | null>(null);
const FikraCoreActionsCtx = createContext<FikraCoreActions | null>(null);

// ─── Capability derivation from stage tag (§7) ───────────────────────────────

function deriveCapabilities(entry: {
  stage: string;
  tags: string[];
}): ScenarioCapabilities {
  const s = entry.stage.toUpperCase();
  const tags = entry.tags || [];
  const hasModelInsufficient = tags.includes("model_insufficient");

  // All stages support investigate (H1 is the base)
  // H2+ adds discover; H3+ adds learn; H4 adds predict
  const isH1orHigher = true;
  const isH2orHigher = ["H2", "H3", "H4"].includes(s);
  const isH3orHigher = ["H3", "H4"].includes(s);
  const isH4 = s === "H4";

  return {
    investigate: isH1orHigher,
    discover: isH2orHigher,
    learn: isH3orHigher && !hasModelInsufficient,
    predict: isH4,
    knowledge: true,  // always available
    lab: true,        // always available
    benchmarks: true, // always available
  };
}

// ─── Default Scenario Registry (Ensures 100% SSR/Client hydration parity) ───

export const DEFAULT_SCENARIO_REGISTRY: ScenarioRegistryEntry[] = [
  {
    id: "SCN-001",
    display_name: "SGi Throughput Degradation & MTU Blackhole",
    description: "Simulates an MTU blackhole on SGi transport interface causing TCP degradation while control plane remains healthy.",
    stage: "H4",
    aliases: ["SGi MTU Blackhole", "MTU Mismatch", "SGi Throughput Degradation", "tr-01 MTU drop"],
    tags: ["transport", "mobile_core", "mtu", "tcp", "4g"],
    domains: ["Transport", "Mobile Core"],
    services: ["SGi-LAN", "Data Services"],
    difficulty: "INTERMEDIATE",
    status: "READY",
    source: "h4-registry",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "H4-WI-001",
    display_name: "MPLS Edge Router Failure",
    description: "Simulates loss of a shared transport edge and estimates downstream service impact.",
    stage: "H4",
    aliases: ["H4-WT-001", "MPLS router failure", "edge router outage", "transport edge failure"],
    tags: ["transport", "routing", "spof", "resilience"],
    domains: ["Transport"],
    services: ["IP Routing"],
    difficulty: "ADVANCED",
    status: "READY",
    source: "h4-registry",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "H4-WI-002",
    display_name: "Data Center Gateway Failure",
    description: "Simulates complete outage of primary DC gateway interconnecting core services.",
    stage: "H4",
    aliases: ["DC gateway outage", "DC-GW failure", "core dc gateway down"],
    tags: ["core", "dc", "spof"],
    domains: ["Cloud / NFVI", "Mobile Core"],
    services: ["Core Infrastructure"],
    difficulty: "ADVANCED",
    status: "AVAILABLE",
    source: "h4-registry",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: false,
  },
  {
    id: "H4-WI-003",
    display_name: "Packet Gateway User Plane Failure",
    description: "Simulates user plane packet forwarder collapse affecting mobile internet traffic.",
    stage: "H4",
    aliases: ["PGW-U failure", "UPF outage", "packet core user plane down"],
    tags: ["packet_core", "5g", "spof"],
    domains: ["Packet Core", "5G Core"],
    services: ["5G SA Mobile Data", "VoNR High Definition Voice"],
    difficulty: "ADVANCED",
    status: "AVAILABLE",
    source: "h4-registry",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: false,
  },
  {
    id: "H4-WI-011",
    display_name: "Dual Router Shared Power Feed Loss",
    description: "Simulates utility feed failure affecting two routers sharing the same PDU rack.",
    stage: "H4",
    aliases: ["site power feed failure", "shared power loss"],
    tags: ["common_cause", "power", "shared_dependency"],
    domains: ["Transport", "Facilities"],
    services: ["Transmission"],
    difficulty: "ADVANCED",
    status: "READY",
    source: "h4-registry",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
];

const DEFAULT_SCENARIO_ID = "H4-WI-001";

export function FikraCoreProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<FikraCoreAppState>({
    activeWorkspace: "investigate",
    scenarioRegistry: DEFAULT_SCENARIO_REGISTRY,
    scenarioRegistryLoading: false,
    scenarioId: DEFAULT_SCENARIO_ID,
    runId: null,
    selectedEntityId: null,
    selectedServiceId: null,
    selectedHypothesisId: null,
    selectedGapId: null,
    selectedEvidenceId: null,
    responseLevel: "engineer",
    simulationState: null,
    syncState: "IDLE",
    connectionState: "CONNECTING",
    lastUpdate: "",
    theme: "dark",
  });

  const simClientRef = useRef<SimulationClient | null>(null);

  // Sync theme on mount
  useEffect(() => {
    const saved = localStorage.getItem("fikracore-theme") as "dark" | "light" | null;
    const initial = saved === "light" || saved === "dark" ? saved : "dark";
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState((prev) => ({ ...prev, theme: initial }));
    document.documentElement.classList.toggle("dark", initial === "dark");
    document.documentElement.classList.toggle("light", initial === "light");
  }, []);

  // Initialize simulation client once without auto-starting the run.
  useEffect(() => {
    const client = new SimulationClient((newSimState) => {
      setState((prev) => ({
        ...prev,
        simulationState: newSimState,
        runId: newSimState.run ? newSimState.run.run_id : null,
        syncState: newSimState.syncState || "IDLE",
        connectionState: newSimState.connectionState,
        lastUpdate: newSimState.lastUpdate,
      }));
    });
    simClientRef.current = client;

    return () => {
      client.destroy();
    };
  }, []);

  const fetchRegistryInternal = useCallback(async () => {
    setState((prev) => ({ ...prev, scenarioRegistryLoading: true }));
    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/scenarios`);
      if (!res.ok) throw new Error(`Registry fetch failed: ${res.statusText}`);
      const data = await res.json();
      const entries: ScenarioRegistryEntry[] = (data.scenarios || []).map(
        (sc: {
          id: string;
          display_name: string;
          description?: string;
          stage?: string;
          aliases?: string[];
          tags?: string[];
          capabilities?: ScenarioCapabilities;
          demo_enabled?: boolean;
        }) => ({
          id: sc.id,
          display_name: sc.display_name,
          description: sc.description || "",
          stage: sc.stage || "H4",
          aliases: sc.aliases || [],
          tags: sc.tags || [],
          domains: deriveDomains(sc.tags || []),
          services: deriveServices(sc.tags || []),
          difficulty: deriveDifficulty(sc.tags || []),
          status: sc.demo_enabled ? "READY" : "AVAILABLE",
          source: "h4-registry",
          capabilities: sc.capabilities || deriveCapabilities({ stage: sc.stage || "H4", tags: sc.tags || [] }),
          demo_enabled: sc.demo_enabled ?? true,
        })
      );
      setState((prev) => ({
        ...prev,
        scenarioRegistry: entries,
        scenarioRegistryLoading: false,
      }));
    } catch (err) {
      console.warn("Registry fetch failed, using empty registry:", err);
      setState((prev) => ({ ...prev, scenarioRegistryLoading: false }));
    }
  }, []);

  // Load scenario registry on mount
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchRegistryInternal();
  }, [fetchRegistryInternal]);

  // ─── Scenario switching lifecycle (§8) ──────────────────────────────────────
  const selectScenario = useCallback(async (scenarioId: string) => {
    setState((prev) => ({
      ...prev,
      scenarioId,
      runId: null,
      selectedEntityId: null,
      selectedServiceId: null,
      selectedHypothesisId: null,
      selectedGapId: null,
      selectedEvidenceId: null,
      simulationState: null,
      syncState: "SWITCHING_SCENARIO",
      connectionState: "DISCONNECTED",
    }));

    if (simClientRef.current) {
      await simClientRef.current.loadScenario(scenarioId);
    }
  }, []);

  // ─── Selection actions (§14, §20) ────────────────────────────────────────────
  const selectEntity = useCallback((entityId: string | null) => {
    setState((prev) => ({ ...prev, selectedEntityId: entityId }));
  }, []);

  const selectService = useCallback((serviceId: string | null) => {
    setState((prev) => ({ ...prev, selectedServiceId: serviceId }));
  }, []);

  const selectHypothesis = useCallback((hypothesisId: string | null) => {
    setState((prev) => ({ ...prev, selectedHypothesisId: hypothesisId }));
  }, []);

  const selectGap = useCallback((gapId: string | null) => {
    setState((prev) => ({ ...prev, selectedGapId: gapId }));
  }, []);

  const selectEvidence = useCallback((evidenceId: string | null) => {
    setState((prev) => ({ ...prev, selectedEvidenceId: evidenceId }));
  }, []);

  const setActiveWorkspace = useCallback((workspace: Workspace) => {
    setState((prev) => ({ ...prev, activeWorkspace: workspace }));
  }, []);

  const setResponseLevel = useCallback((level: ResponseLevel) => {
    setState((prev) => ({ ...prev, responseLevel: level }));
  }, []);

  const refreshRegistry = useCallback(async () => {
    await fetchRegistryInternal();
  }, [fetchRegistryInternal]);

  // ─── Simulation controls ──────────────────────────────────────────────────────
  const startSimulation = useCallback(async (scenarioId?: string) => {
    const targetScenario = scenarioId ?? state.scenarioId ?? DEFAULT_SCENARIO_ID;
    await simClientRef.current?.startSimulation(targetScenario);
  }, [state.scenarioId]);

  const pauseSimulation = useCallback(async () => {
    await simClientRef.current?.pauseSimulation();
  }, []);

  const resumeSimulation = useCallback(async () => {
    await simClientRef.current?.resumeSimulation();
  }, []);

  const stopSimulation = useCallback(async () => {
    await simClientRef.current?.stopSimulation();
  }, []);

  const replaySimulation = useCallback(async () => {
    await simClientRef.current?.replaySimulation();
  }, []);

  const executeAction = useCallback(async (actionId: string) => {
    await simClientRef.current?.executeAction(actionId);
  }, []);

  const toggleTheme = useCallback(() => {
    setState((prev) => {
      const next = prev.theme === "dark" ? "light" : "dark";
      localStorage.setItem("fikracore-theme", next);
      document.documentElement.classList.toggle("dark", next === "dark");
      document.documentElement.classList.toggle("light", next === "light");
      return { ...prev, theme: next };
    });
  }, []);

  const setTheme = useCallback((next: "dark" | "light") => {
    localStorage.setItem("fikracore-theme", next);
    document.documentElement.classList.toggle("dark", next === "dark");
    document.documentElement.classList.toggle("light", next === "light");
    setState((prev) => ({ ...prev, theme: next }));
  }, []);

  const actions: FikraCoreActions = {
    setActiveWorkspace,
    selectScenario,
    selectEntity,
    selectService,
    selectHypothesis,
    selectGap,
    selectEvidence,
    setResponseLevel,
    refreshRegistry,
    startSimulation,
    pauseSimulation,
    resumeSimulation,
    stopSimulation,
    replaySimulation,
    executeAction,
    toggleTheme,
    setTheme,
  };

  return (
    <FikraCoreStateCtx.Provider value={state}>
      <FikraCoreActionsCtx.Provider value={actions}>
        {children}
      </FikraCoreActionsCtx.Provider>
    </FikraCoreStateCtx.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useFikraCore(): FikraCoreAppState & FikraCoreActions {
  const state = useContext(FikraCoreStateCtx);
  const actions = useContext(FikraCoreActionsCtx);
  if (!state || !actions) {
    throw new Error("useFikraCore() must be used inside <FikraCoreProvider>");
  }
  return { ...state, ...actions };
}

// ─── Utility: Zaki context envelope (§17) ─────────────────────────────────────

export function buildZakiContextEnvelope(
  state: FikraCoreAppState,
  query: string
): Record<string, unknown> {
  const simState = state.simulationState;
  return {
    query,
    scenario_id: state.scenarioId,
    scenario_name:
      state.scenarioRegistry.find((s) => s.id === state.scenarioId)?.display_name ?? "",
    run_id: state.runId,
    workspace: state.activeWorkspace,
    simulation_stage: simState?.run?.status ?? "RUNNING",
    response_level: state.responseLevel,
    selected_entity_id: state.selectedEntityId,
    selected_hypothesis_id: state.selectedHypothesisId,
    selected_gap_id: state.selectedGapId,
    selected_evidence_id: state.selectedEvidenceId,
    knowledge_source: "live_telecombrain",
    mode: "INVESTIGATION",
    step: 1,
  };
}

// ─── Workspace suggestion chips (§25) ─────────────────────────────────────────

export function getWorkspaceSuggestions(
  workspace: Workspace,
  selectedEntity?: string | null
): string[] {
  const entityCtx = selectedEntity ? ` for ${selectedEntity}` : "";
  const chips: Record<Workspace, string[]> = {
    investigate: [
      "Why is Transport ranked first?",
      "What contradicts this hypothesis?",
      "What evidence is missing?",
      `What is the causal path${entityCtx}?`,
    ],
    discover: [
      "Where does known topology stop?",
      "What evidence can resolve this gap?",
      "Why is this relationship only a candidate?",
    ],
    learn: [
      "What knowledge is awaiting validation?",
      "What improved after learning?",
      "Can this knowledge be promoted safely?",
    ],
    predict: [
      "Show the blast radius.",
      "Why does failover fail?",
      "Which mitigation reduces the risk most?",
    ],
    knowledge: [
      "What does FikraCore know about Transport?",
      "Which knowledge is stale?",
      "What are the top coverage gaps?",
    ],
    lab: [
      "What scenarios are available?",
      "What is the current simulation status?",
      "Compare this run with the previous.",
    ],
    benchmarks: [
      "What is the H4 benchmark result?",
      "Is MCP parity passing?",
      "What are the top regression failures?",
    ],
  };
  return chips[workspace] || [];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function deriveDomains(tags: string[]): string[] {
  const domainMap: Record<string, string> = {
    transport: "Transport",
    mobile_core: "Mobile Core",
    packet_core: "Packet Core",
    ran: "RAN",
    ims: "IMS",
    bss: "BSS",
    oss: "OSS",
    database: "Database",
    dns: "DNS",
    security: "Security",
    signaling: "Signaling",
  };
  return tags
    .filter((t) => domainMap[t])
    .map((t) => domainMap[t])
    .filter((v, i, a) => a.indexOf(v) === i);
}

function deriveServices(tags: string[]): string[] {
  const serviceMap: Record<string, string> = {
    "4g": "4G LTE Data",
    "5g": "5G Core",
    volte: "VoLTE",
    routing: "IP Routing",
    charging: "Charging",
  };
  return tags
    .filter((t) => serviceMap[t])
    .map((t) => serviceMap[t])
    .filter((v, i, a) => a.indexOf(v) === i);
}

function deriveDifficulty(tags: string[]): string {
  if (tags.includes("multi_failure") || tags.includes("cascade")) return "L4";
  if (tags.includes("common_cause") || tags.includes("change_risk")) return "L3";
  if (tags.includes("capacity") || tags.includes("failover")) return "L2";
  return "L1";
}
