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

export const STAGE_TO_CONCEPT: Record<string, string> = {
  H1: "Understand",
  H2: "Discover",
  H3: "Learn",
  H4: "Anticipate",
};

export const CONCEPT_TO_STAGE: Record<string, string> = {
  Understand: "H1",
  Discover: "H2",
  Learn: "H3",
  Anticipate: "H4",
};

export function getConceptName(stageOrConcept?: string): string {
  if (!stageOrConcept) return "Understand";
  const upper = stageOrConcept.toUpperCase();
  if (upper === "H1" || upper === "UNDERSTAND") return "Understand";
  if (upper === "H2" || upper === "DISCOVER") return "Discover";
  if (upper === "H3" || upper === "LEARN") return "Learn";
  if (upper === "H4" || upper === "ANTICIPATE") return "Anticipate";
  return stageOrConcept;
}

export interface ScenarioRegistryEntry {
  id: string;
  display_name: string;
  description: string;
  stage: string;          // H1 / H2 / H3 / H4
  concept: string;        // Understand / Discover / Learn / Anticipate
  scenario_type?: string; // INCIDENT / KNOWLEDGE_GAP / LEARNING_UNIT / WHAT_IF
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
  advanceStage: () => Promise<void>;
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
    display_name: "Transport N3 Degradation Cascades into Mobile Data Failure",
    description: "Intermittent transport path degradation on PE-RTR-21 N3 backhaul causes UPF reachability starvation and customer ticket surges.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["TWIN-INC-001", "Transport N3 Degradation", "PE-RTR-21 N3 degradation", "H1-INC-001", "SCN-001"],
    tags: ["ip_transport", "sa_5g_core", "crm", "n3_tunnel", "5g"],
    domains: ["IP Transport", "5G SA Core", "CRM"],
    services: ["5G SA Mobile Data (REGION-NORTH)"],
    difficulty: "L1",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "SCN-002",
    display_name: "UPF Failure Cascades into Charging and Customer Impact",
    description: "User Plane Function degradation propagates to online charging systems and degrades prepaid session state.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["SCN-002"],
    tags: ["sa_5g_core", "charging", "crm"],
    domains: ["5G SA Core", "Charging", "CRM"],
    services: ["Online Charging Data"],
    difficulty: "L2",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "SCN-003",
    display_name: "Internal DNS Degradation Cascades Across Core Functions",
    description: "DNS resolution latencies impact service discovery between 5G core network functions.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["SCN-003"],
    tags: ["dns", "sa_5g_core"],
    domains: ["IP Transport", "5G SA Core"],
    services: ["5G Service Discovery"],
    difficulty: "L3",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "SCN-004",
    display_name: "Kubernetes Worker Failure Cascades into Core Degradation",
    description: "Node evictions and worker pod terminations trigger failover storms in cloud-native 5GC.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["SCN-004"],
    tags: ["kubernetes", "cloud_native", "5gc"],
    domains: ["Cloud / NFVI", "5G SA Core"],
    services: ["Core CNF Orchestration"],
    difficulty: "L4",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "SCN-005",
    display_name: "IMS Database Failure Cascades into Voice Degradation",
    description: "Database locks on subscriber profile repository drop SIP registration and VoLTE call completion.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["SCN-005"],
    tags: ["ims", "volte", "database"],
    domains: ["IMS / VoLTE", "Subscriber Data"],
    services: ["VoLTE High Definition Voice"],
    difficulty: "L5",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "SCN-006",
    display_name: "Shared Power Failure Hits RAN and Transport Together",
    description: "Dual utility power drop takes down both cell site edge routers and collocated gNodeB radios.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["SCN-006"],
    tags: ["power", "ran", "transport"],
    domains: ["Facilities", "RAN", "IP Transport"],
    services: ["Cellular Coverage"],
    difficulty: "L1",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "SCN-007",
    display_name: "Shared Timing Source Failure Affects RAN and Transport",
    description: "PTP / SyncE grandmaster clock drift creates phase errors and inter-cell handover collapses.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["SCN-007"],
    tags: ["timing", "synce", "ptp", "ran"],
    domains: ["Synchronization", "RAN", "IP Transport"],
    services: ["5G TDD Synchronization"],
    difficulty: "L2",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "SCN-008",
    display_name: "Shared Storage Failure Impacts Multiple Core CNFs",
    description: "CSI storage volume detachment locks persistent state across UDR and PCF clusters.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["SCN-008"],
    tags: ["storage", "csi", "cloud_native"],
    domains: ["Cloud / NFVI", "5G SA Core"],
    services: ["Subscriber Policy"],
    difficulty: "L3",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "SCN-009",
    display_name: "Shared Firewall Cluster Failure Affects Multiple Services",
    description: "Stateful session exhaustion on Gi-LAN security appliances drops corporate APN traffic.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["SCN-009"],
    tags: ["firewall", "security", "gi_lan"],
    domains: ["Security", "Packet Core"],
    services: ["Corporate APN"],
    difficulty: "L4",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "SCN-010",
    display_name: "Shared Leaf/TOR Dependency Defeats Logical Redundancy",
    description: "Single top-of-rack leaf switch failure disconnects primary and secondary user plane paths.",
    stage: "H1",
    concept: "Understand",
    scenario_type: "INCIDENT",
    aliases: ["SCN-010"],
    tags: ["tor", "fabric", "transport"],
    domains: ["IP Transport", "Cloud / NFVI"],
    services: ["User Plane Conduits"],
    difficulty: "L5",
    status: "READY",
    source: "incident_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "H2-GAP-001",
    display_name: "Missing OCS Charging Dependency",
    description: "Exposes an unmodeled billing/charging dependency boundary causing unexplained service dropouts.",
    stage: "H2",
    concept: "Discover",
    scenario_type: "KNOWLEDGE_GAP",
    aliases: ["TWIN-GAP-001", "missing ocs dependency", "charging gap", "H2-SCN-001"],
    tags: ["charging", "ocs", "knowledge_gap", "boundary"],
    domains: ["Mobile Core", "OCS"],
    services: ["Subscriber Charging", "5G Data Session"],
    difficulty: "INTERMEDIATE",
    status: "READY",
    source: "h2_catalog",
    capabilities: { investigate: true, discover: true, learn: false, predict: false, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "H3-LRN-001",
    display_name: "Validated OCS Charging Dependency Promotion",
    description: "Curated learning unit demonstrating SME validation and promotion of discovered charging path.",
    stage: "H3",
    concept: "Learn",
    scenario_type: "LEARNING_UNIT",
    aliases: ["TWIN-LRN-001", "validated charging dependency", "h3 learning unit", "H3-LU-001"],
    tags: ["learning", "promotion", "curated_learning", "fcaps"],
    domains: ["Mobile Core", "OCS"],
    services: ["Subscriber Charging"],
    difficulty: "ADVANCED",
    status: "READY",
    source: "h3_catalog",
    capabilities: { investigate: true, discover: true, learn: true, predict: false, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
  {
    id: "H4-WI-001",
    display_name: "MPLS Edge Router Shared Power Feed Loss",
    description: "Simulates loss of a shared transport edge and estimates downstream service impact.",
    stage: "H4",
    concept: "Anticipate",
    scenario_type: "WHAT_IF",
    aliases: ["TWIN-WIF-001", "H4-WT-001", "MPLS router failure", "edge router outage", "transport edge failure"],
    tags: ["transport", "routing", "spof", "resilience"],
    domains: ["Transport"],
    services: ["IP Routing"],
    difficulty: "ADVANCED",
    status: "READY",
    source: "h4-registry",
    capabilities: { investigate: true, discover: true, learn: true, predict: true, knowledge: true, lab: true, benchmarks: true },
    demo_enabled: true,
  },
];

const DEFAULT_SCENARIO_ID = "";

export function FikraCoreProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<FikraCoreAppState>({
    activeWorkspace: "investigate",
    scenarioRegistry: DEFAULT_SCENARIO_REGISTRY,
    scenarioRegistryLoading: false,
    scenarioId: null,
    runId: null,
    selectedEntityId: null,
    selectedServiceId: null,
    selectedHypothesisId: null,
    selectedGapId: null,
    selectedEvidenceId: null,
    responseLevel: "engineer",
    simulationState: null,
    syncState: "IDLE",
    connectionState: "DISCONNECTED",
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
        scenarioId: newSimState.scenario?.id || newSimState.scenario_id || prev.scenarioId,
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
          concept?: string;
          scenario_type?: string;
          aliases?: string[];
          tags?: string[];
          domains?: string[];
          services?: string[];
          difficulty?: string;
          capabilities?: ScenarioCapabilities;
          demo_enabled?: boolean;
          source?: string;
        }) => {
          const stage = sc.stage || "H1";
          const concept = sc.concept || getConceptName(stage);
          return {
            id: sc.id,
            display_name: sc.display_name,
            description: sc.description || "",
            stage,
            concept,
            scenario_type: sc.scenario_type || "INCIDENT",
            aliases: sc.aliases || [],
            tags: sc.tags || [],
            domains: sc.domains && sc.domains.length > 0 ? sc.domains : deriveDomains(sc.tags || []),
            services: sc.services && sc.services.length > 0 ? sc.services : deriveServices(sc.tags || []),
            difficulty: sc.difficulty || deriveDifficulty(sc.tags || []),
            status: sc.demo_enabled ? "READY" : "AVAILABLE",
            source: sc.source || "scenario-catalog",
            capabilities: sc.capabilities || deriveCapabilities({ stage, tags: sc.tags || [] }),
            demo_enabled: sc.demo_enabled ?? true,
          };
        }
      );
      setState((prev) => ({
        ...prev,
        scenarioRegistry: entries,
        scenarioRegistryLoading: false,
      }));
    } catch (err) {
      console.warn("Registry fetch failed, using default registry:", err);
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
    if (!scenarioId) {
      setState((prev) => ({
        ...prev,
        scenarioId: null,
        runId: null,
        selectedEntityId: null,
        selectedServiceId: null,
        selectedHypothesisId: null,
        selectedGapId: null,
        selectedEvidenceId: null,
        simulationState: null,
        syncState: "IDLE",
        connectionState: "DISCONNECTED",
      }));
      return;
    }

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
    if (!targetScenario) return;
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

  const advanceStage = useCallback(async () => {
    await simClientRef.current?.advanceStage();
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
    advanceStage,
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
