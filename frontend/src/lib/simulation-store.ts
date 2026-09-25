/**
 * Normalized Simulation Store & WebSocket / SSE Router (§25, §26).
 *
 * Provides central state management, REST synchronization, and live SSE event routing
 * for the FikraCore Live Simulator UI without hard-coded numbers.
 */

import { API_BASE } from "@/lib/api/config";

export interface ScenarioMeta {
  id: string;
  display_name: string;
  stage: string;
  service: string;
  domains: string[];
  status: string;
}

export interface SimulationRunMeta {
  run_id: string;
  scenario_id: string;
  status: "READY" | "RUNNING" | "PAUSED" | "COMPLETED" | "STOPPED" | "BLOCKED" | "CREATED" | "INITIALIZING" | "FAILED";
  speed: number;
  started_at: string;
  elapsed_seconds: number;
  elapsed_formatted: string;
  terminal_state?: string | null;
  is_replay?: boolean;
  replay_position?: number;
  stage_index?: number;
}

export interface StageExitCondition {
  condition_id: string;
  display_name: string;
  satisfied: boolean;
  expected?: string;
  actual?: string;
  reason?: string;
}

export interface ZakiSuggestedAction {
  action_id: string;
  display_name: string;
  action_type:
    | "SHOW_EVIDENCE"
    | "FOCUS_HYPOTHESIS"
    | "FOCUS_PATHWAY"
    | "REQUEST_EVIDENCE"
    | "SHOW_GAP"
    | "SHOW_ATTRIBUTION"
    | "REQUEST_VALIDATION";
  enabled: boolean;
  disabled_reason?: string;
  target_id?: string;
}

export interface LiveIntentMeta {
  intent_id: string;
  display_name: string;
  service: string;
  scope?: string;
  target: {
    metric: string;
    operator: string;
    threshold: number | string;
  };
  observed: {
    value: number | string;
    observed_at: string;
  };
  severity: string;
  source_system?: string;
  domain_hint?: string;
}

export interface ZakiChatClientRequest {
  query?: string;
  message?: string;
  scenario_id?: string;
  run_id?: string;
  source_mode?: "SIMULATION" | "LIVE_INTENT";
  intent_id?: string | null;
  revision?: number;
  response_level?: "EXECUTIVE" | "OPERATOR" | "ENGINEER" | "DEEP_TECHNICAL";
  selected_context?: Record<string, unknown>;
}

export interface ZakiChatResponse {
  status: string;
  scenario_id: string;
  run_id?: string;
  source_mode?: string;
  intent_id?: string | null;
  revision: number;
  response_level: string;
  query?: string;
  answer: string;
  response: Record<string, unknown>;
  grounded_in?: {
    evidence_ids?: string[];
    pathway_ids?: string[];
    hypothesis_ids?: string[];
    gap_ids?: string[];
    connection_ids?: string[];
    stage?: string;
    source_mode?: string;
    intent_id?: string | null;
  };
  uncertainty?: string[];
  suggested_actions?: ZakiSuggestedAction[];
  sections?: ZakiResponseSection[];
  highlighted_entities?: HighlightedEntity[];
  selected_context?: ZakiSelectedContext;
  copilot_state?: string;
  zaki_v2?: ZakiResponseV2;
}

export type ZakiSelectedContextType =
  | "HYPOTHESIS"
  | "PATHWAY"
  | "CONNECTION"
  | "KNOWLEDGE_GAP"
  | "DOMAIN_ATTRIBUTION"
  | "STAGE"
  | "REASONING_CORE"
  | "NETWORK_ENTITY";

export interface ZakiSelectedContext {
  context_type: ZakiSelectedContextType;
  context_id: string;
  display_name: string;
  summary?: string;
  status?: string;
  source_revision?: number;
  source_run_id?: string;
  metrics?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface HighlightedEntity {
  name: string;
  type: string;
  role: "PRIMARY" | "AFFECTED" | "CONTRIBUTING" | "MONITOR ONLY" | "UNKNOWN";
  visual_role: "STRUCTURE" | "FOCUS" | "CONFIRMED";
  domain?: string;
  description?: string;
}

export interface ZakiResponseSection {
  title: string;
  content: string;
  order: number;
}

export interface ZakiResponseV2 {
  answer: string;
  sections: ZakiResponseSection[];
  grounded_in: {
    stage?: string;
    domain?: string;
    role?: string;
    attribution_basis?: string;
    attribution_status?: string;
    hypothesis_ids?: string[];
    evidence_ids?: string[];
    pathway_ids?: string[];
    connection_ids?: string[];
    gap_ids?: string[];
    run_id?: string;
    revision?: number;
    grounded_in_simulation?: boolean;
    internet_access?: boolean;
    [key: string]: unknown;
  };
  uncertainty?: string[];
  suggested_actions?: Array<{
    action_id: string;
    display_name: string;
    action_type: string;
    enabled: boolean;
    target_id?: string;
  }>;
  highlighted_entities?: HighlightedEntity[];
  selected_context?: ZakiSelectedContext;
  copilot_state?: string;
  revision?: number;
  source_mode?: string;
  timestamp?: string;
}

export interface ZakiRevisionDiff {
  previous_revision: number;
  current_revision: number;
  changed_sections: string[];
  summary: string;
}

export interface ZakiUIState {
  mode: "COMPACT" | "EXPANDED" | "DOCKED";
  selectedContext: ZakiSelectedContext | null;
  responseLevel: "executive" | "operator" | "engineer" | "deep";
  lastResponse: ZakiResponseV2 | null;
  isLoading: boolean;
  error: string | null;
  history: Array<{
    id: string;
    query: string;
    response: ZakiResponseV2;
    timestamp: string;
  }>;
}


export interface SimulationStage {
  index: number;
  key: string;
  label: string;
  summary: string;
  status: "PENDING" | "ACTIVE" | "COMPLETED" | "FAILED";
}

export interface SimulationEvent {
  event_id: string;
  time: string;
  category: "alarm" | "metric" | "log" | "trace" | "change" | "ticket" | "action" | "hypothesis";
  badge: string;
  title: string;
  domain: string;
  entity_id: string;
  severity: "critical" | "high" | "warning" | "info";
  state: "OBSERVED" | "CONFIRMED" | "INVOLVED" | "TESTING" | "REJECTED" | "SYMPTOM";
}

export interface TopologyEntity {
  id: string;
  display_name: string;
  subtitle: string;
  state: "HEALTHY" | "SYMPTOM" | "ROOT_CANDIDATE" | "UNKNOWN" | "IMPACTED";
  icon: "radio" | "alert" | "help" | "server" | "users";
  detail?: string;
}

export interface TopologyDomain {
  name: string;
  subtitle: string;
  entities: TopologyEntity[];
}

export interface TopologyCausalEdge {
  id?: string;
  from: string;
  to: string;
  status: string;
  relation: string;
  role?: string;
  hypothesis_id?: string;
}

export interface SimulationTopology {
  domains: TopologyDomain[];
  causal_path: TopologyCausalEdge[];
  operational_edges?: TopologyCausalEdge[];
  hypothesis_paths?: Array<{
    hypothesis_id: string;
    entity_ids: string[];
    edge_ids: string[];
    role: string;
    confidence: number | null;
  }>;
  confirmed_path_label: string;
  path_confidence: number;
}

export interface SimulationHypothesis {
  id: string;
  hypothesis_id?: string;
  label?: string;
  rank: number | null;
  display_name: string;
  confidence: number | null;
  confidence_state?: "UNRANKED" | "RANKED" | "ROOT_CANDIDATE" | "CONFIRMED" | "REJECTED";
  delta: string;
  status: "LEADING" | "COMPETING" | "REJECTED" | "CANDIDATE";
  lifecycle_state?: "TESTING" | "SUPPORTED" | "NEEDS_MORE_EVIDENCE" | "TESTING_NEW_EVIDENCE" | "WEAKENING" | "CONFIRMED" | "REJECTED" | "CANDIDATE";
  supports: string[];
  against: string[];
  missing: string[];
  support_count?: number;
  contradiction_count?: number;
  missing_evidence_count?: number;
  evidence_count: number;
  evidence_ids?: string[];
  path_entity_ids?: string[];
  path_edge_ids?: string[];
  path_role?: string;
  frontier_ids?: string[];
  last_delta?: number | null;
  last_delta_reason?: string;
  confidence_history?: Array<{
    hypothesis_id: string;
    previous: number | null;
    new: number | null;
    delta: number | null;
    reason: string;
    evidence_ids: string[];
    sequence: number;
    timestamp?: string;
  }>;
  tested: boolean;
}

export interface ReasoningTask {
  id: number;
  name: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
}

export interface ImpactState {
  service: string;
  impact_state?: "UNKNOWN" | "OBSERVED" | "ESTIMATED" | "INFERRED" | "CONFIRMED";
  state?: "UNKNOWN" | "OBSERVED" | "ESTIMATED" | "INFERRED" | "CONFIRMED";
  throughput_impact_pct: number | null;
  degradation_pct?: number | null;
  regions_affected: number | null;
  regions?: unknown[];
  affected_users: number | null;
  affected_services?: string[];
  affected_label: string;
  confidence?: number | null;
  evidence_ids?: string[];
  status_label?: string;
  summary?: string;
  trend_sparkline: number[];
}

export interface KnowledgeGap {
  id: string;
  label: string;
  reason: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
}

export interface EvidenceCluster {
  cluster_id: string;
  label: string;
  event_ids: string[];
  entity_ids: string[];
  signal_count: number;
  noise_count: number;
  confidence: number;
}

export interface UnknownFrontier {
  id?: string;
  frontier_id: string;
  type: "MISSING_EVIDENCE" | "MISSING_TOPOLOGY" | "CANDIDATE_RELATIONSHIP" | "MODEL_INSUFFICIENT" | "UNRESOLVED_DEPENDENCY";
  entity_ids: string[];
  hypothesis_ids: string[];
  description: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  resolvable: boolean;
  required_evidence: string;
}

export interface SearchSpaceState {
  events: number;
  correlated_signals: number;
  relevant_entities: number;
  hypotheses: number;
  plausible_causes: number;
  root_candidates: number;
  open_frontiers: number;
}

export interface ReasoningFocusState {
  entity_id?: string;
  hypothesis_id?: string;
  test_id?: string | null;
  stage?: string;
  reason?: string;
  frontier_id?: string;
  stage_status?: string;
}

export interface ReasoningMapExplain {
  what: string;
  why: string;
  supports: string[];
  affects: string[];
  unknown: string;
  recent: string;
}

export interface ReasoningMapSource {
  id: string;
  display_name: string;
  mode: "LIVE" | "OFFLINE_SIMULATION";
  status: string;
  context?: Record<string, unknown>;
  explain: ReasoningMapExplain;
}

export interface ReasoningMapEvidence {
  id: string;
  evidence_id?: string;
  scenario_id?: string;
  run_id?: string;
  display_name: string;
  type: string;
  evidence_type?: string;
  category?: string;
  source_entity?: string;
  domain?: string;
  timestamp?: string;
  event_time?: string;
  status: string;
  state?: string;
  evidence_ids: string[];
  explain: ReasoningMapExplain;
}

export interface ReasoningMapPathway {
  id: string;
  pathway_id?: string;
  scenario_id?: string;
  run_id?: string;
  display_name: string;
  status: "DORMANT" | "DISCOVERED" | "ACTIVE" | "RESOLVED" | "REJECTED";
  state?: "DORMANT" | "DISCOVERED" | "ACTIVE" | "RESOLVED" | "REJECTED";
  activation_reason: string;
  evidence_ids: string[];
  hypothesis_ids: string[];
  explain: ReasoningMapExplain;
}

export interface ReasoningMapHypothesis {
  id: string;
  hypothesis_id?: string;
  scenario_id?: string;
  run_id?: string;
  display_id: string;
  display_name: string;
  status: string;
  state?: string;
  confidence: number | null;
  supporting_evidence: string[];
  contradicting_evidence?: string[];
  contradictions: string[];
  missing_evidence: string[];
  explain: ReasoningMapExplain;
}

export interface ReasoningMapGap {
  id: string;
  gap_id?: string;
  scenario_id?: string;
  run_id?: string;
  display_name: string;
  status: "OPEN" | "RESOLVED";
  state?: "OPEN" | "NEEDS_EVIDENCE" | "IN_PROGRESS" | "RESOLVED";
  affected_hypothesis_ids?: string[];
  affected_pathway_ids?: string[];
  affected_hypotheses: string[];
  affected_pathways: string[];
  required_evidence: string;
  next_best_evidence_id?: string | null;
  explain: ReasoningMapExplain;
}

export interface ReasoningMapConnection {
  id: string;
  connection_id?: string;
  scenario_id?: string;
  run_id?: string;
  source_id: string;
  target_id: string;
  relation_type: string;
  state: string;
  reason: string;
  sequence: number;
}

export interface ReasoningMapSynthesis {
  id: string;
  display_name: string;
  state: "INSUFFICIENT_EVIDENCE" | "PARTIAL" | "CONFLICTING_EVIDENCE" | "CONVERGING" | "STRONGLY_SUPPORTED" | "ROOT_CANDIDATE" | "MODEL_INSUFFICIENT";
  summary: string;
  dimensions: Array<{ display_name: string; state: string; value?: number }>;
  leading_hypothesis_id?: string | null;
  explain: ReasoningMapExplain;
}

export interface ReasoningMapValidation {
  id: string;
  display_name: string;
  status: "PENDING" | "ACCEPTED" | "REJECTED" | "MODIFIED" | "NEED_MORE_EVIDENCE" | "NOT_READY";
  reviewer_role: string;
  evidence_package_ids: string[];
  explain: ReasoningMapExplain;
}

export interface ReasoningMapLearning {
  id: string;
  display_name: string;
  status: string;
  summary: string;
  explain: ReasoningMapExplain;
}

export interface ReasoningMapDomainAttribution {
  id: string;
  status: "PENDING" | "READY";
  domains: Array<{
    display_name: string;
    role: "PRIMARY" | "CONTRIBUTING" | "AFFECTED" | "INVOLVED" | "MONITOR_ONLY" | "NOT_RELEVANT";
  }>;
  explain: ReasoningMapExplain;
}

export interface ReasoningMapState {
  contract_version: number;
  run_id: string;
  scenario_id: string;
  source_mode: "LIVE" | "OFFLINE_SIMULATION";
  revision: number;
  sequence: number;
  stage: string;
  source: ReasoningMapSource;
  evidence: ReasoningMapEvidence[];
  reasoning_pathways: ReasoningMapPathway[];
  connections: ReasoningMapConnection[];
  hypotheses: ReasoningMapHypothesis[];
  knowledge_gaps: ReasoningMapGap[];
  next_best_evidence: NextBestAction[];
  synthesis: ReasoningMapSynthesis;
  validation: ReasoningMapValidation;
  learning: ReasoningMapLearning;
  domain_attribution: ReasoningMapDomainAttribution;
  reasoning_focus: {
    entity?: string | null;
    pathway?: string | null;
    hypothesis?: string | null;
    test?: string | null;
    reason?: string | null;
  };
}

export interface NextBestAction {
  id: string;
  display_name: string;
  status: "READY" | "RUNNING" | "COMPLETED" | "PENDING";
}

export interface LearningState {
  candidate_count: number;
  summary: string;
  rule: string;
  confidence: number;
  status: "CANDIDATE" | "PROMOTED" | "REJECTED";
  enabled: boolean;
}

export interface ZakiCognitiveState {
  phase: "OBSERVING" | "REASONING" | "EVIDENCE_NEEDED" | "RECOMMENDATION_READY";
  thought: string;
  active_focus_entity: string;
  confidence: number;
}

export interface ReasoningTraceRecord {
  timestamp: string;
  scenario_id: string;
  run_id: string;
  sequence: number;
  stage: string;
  component: string;
  event_type: string;
  entity_ids: string[];
  hypothesis_id?: string;
  message: string;
  details?: Record<string, unknown>;
  provenance: string;
}

export interface SimulationState {
  scenario_id?: string;
  run_id?: string;
  snapshot_version?: number;
  revision?: number;
  sequence?: number;
  updated_at?: string;
  current_stage?: string;
  stage_status?: string;
  entered_at?: string;
  elapsed_ms?: number;
  exit_conditions?: string[];
  exit_conditions_detail?: StageExitCondition[];
  exit_condition_state?: Record<string, unknown>;
  next_stage?: string | null;
  blocking_reason?: string | null;
  waiting_for?: string | null;
  terminal_state?: string | null;
  is_replay?: boolean;
  replay_position?: number;
  run_status?: string;
  scenario: ScenarioMeta | null;
  run: SimulationRunMeta | null;
  stages: SimulationStage[];
  events: SimulationEvent[];
  rawEvents?: SimulationEvent[];
  reasoningTrace?: ReasoningTraceRecord[];
  topology: SimulationTopology | null;
  evidenceClusters?: EvidenceCluster[];
  frontiers?: UnknownFrontier[];
  searchSpace?: SearchSpaceState | null;
  reasoningFocus?: ReasoningFocusState | null;
  reasoningMap?: ReasoningMapState | null;
  hypotheses: SimulationHypothesis[];
  reasoningTasks: ReasoningTask[];
  impact: ImpactState | null;
  knowledgeGaps: KnowledgeGap[];
  nextBestActions: NextBestAction[];
  learning: LearningState | null;
  zaki: ZakiCognitiveState | null;
  storyContext?: Record<string, unknown> | null;
  source_mode?: "SIMULATION" | "LIVE_INTENT";
  intent_id?: string | null;
  live_intents?: LiveIntentMeta[];
  connectionState: "LIVE" | "CONNECTING" | "DEGRADED" | "DISCONNECTED";
  syncState?: "IDLE" | "SWITCHING_SCENARIO" | "LOADING_SNAPSHOT" | "CONNECTING_LIVE_STREAM" | "SYNCED" | "RESYNCING" | "DISCONNECTED" | "ERROR";
  lastUpdate: string;
}

export class SimulationClient {
  private eventSource: EventSource | null = null;
  private onStateChange: (state: SimulationState) => void;
  private state: SimulationState;
  private activeScenarioId: string | null = null;
  private activeRunId: string | null = null;
  private switchVersion = 0;
  private abortController: AbortController | null = null;
  private lastSequence = 0;
  private currentRevision = 0;
  private zakiUIState: ZakiUIState = {
    mode: "COMPACT",
    selectedContext: null,
    responseLevel: "engineer",
    lastResponse: null,
    isLoading: false,
    error: null,
    history: [],
  };

  constructor(onStateChange: (state: SimulationState) => void) {
    this.onStateChange = onStateChange;
    this.state = {
      scenario_id: undefined,
      run_id: undefined,
      source_mode: "SIMULATION",
      intent_id: null,
      live_intents: [],
      snapshot_version: 0,
      revision: 0,
      sequence: 0,
      updated_at: undefined,
      scenario: null,
      run: null,
      stages: [],
      events: [],
      rawEvents: [],
      reasoningTrace: [],
      topology: null,
      evidenceClusters: [],
      frontiers: [],
      searchSpace: null,
      reasoningFocus: null,
      reasoningMap: null,
      hypotheses: [],
      reasoningTasks: [],
      impact: null,
      knowledgeGaps: [],
      nextBestActions: [],
      learning: null,
      zaki: null,
      connectionState: "CONNECTING",
      syncState: "IDLE",
      lastUpdate: new Date().toLocaleTimeString(),
    };
  }


  public getState(): SimulationState {
    return this.state;
  }

  public async loadScenario(scenarioId: string = "SCN-001"): Promise<void> {
    const version = ++this.switchVersion;
    this.abortController?.abort();
    this.abortController = new AbortController();
    this.disconnectLiveStream();
    this.activeScenarioId = scenarioId;
    this.activeRunId = null;
    this.lastSequence = 0;
    this.currentRevision = 0;
    this.resetScenarioScopedState("SWITCHING_SCENARIO");

    try {
      this.state.syncState = "LOADING_SNAPSHOT";
      this.state.connectionState = "CONNECTING";
      this.notify();

      const scenarioRes = await fetch(`${API_BASE}/api/v1/fikracore/scenarios/${scenarioId}`, {
        signal: this.abortController.signal,
      });
      if (!scenarioRes.ok) throw new Error(`Failed to load scenario metadata: ${scenarioRes.statusText}`);
      const scenarioData = await scenarioRes.json();
      const resolvedScenarioId = scenarioData.scenario?.id || scenarioId;
      if (version !== this.switchVersion) return;
      this.activeScenarioId = resolvedScenarioId;
      this.state.scenario_id = resolvedScenarioId;

      // Load static compiled scenario state snapshot without auto-starting run or SSE streaming
      const stateRes = await fetch(`${API_BASE}/api/v1/fikracore/scenarios/${resolvedScenarioId}/state`, {
        signal: this.abortController.signal,
      });
      if (stateRes.ok) {
        const stateData = await stateRes.json();
        if (version === this.switchVersion) {
          if (stateData.run && stateData.run.status !== "PAUSED" && stateData.run.status !== "STOPPED") {
            stateData.run.status = "READY";
          }
          if (stateData.status && stateData.status !== "PAUSED" && stateData.status !== "STOPPED") {
            stateData.status = "READY";
          }
          this.applySnapshot(stateData);
        }
      }

      this.state.syncState = "IDLE";
      this.state.connectionState = "DISCONNECTED";
      this.notify();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      console.warn("REST load failed while preparing scenario:", err);
      this.activeScenarioId = scenarioId;
      this.state.scenario_id = scenarioId;
      this.state.connectionState = "DISCONNECTED";
      this.state.syncState = "IDLE";
      this.notify();
    }
  }

  public async startSimulation(scenarioId?: string): Promise<void> {
    const targetScenarioId = (scenarioId || this.activeScenarioId || "SCN-001").trim();
    const version = ++this.switchVersion;
    this.abortController?.abort();
    this.abortController = new AbortController();
    this.disconnectLiveStream();
    this.activeScenarioId = targetScenarioId;
    this.lastSequence = 0;
    this.currentRevision = 0;
    this.resetScenarioScopedState("LOADING_SNAPSHOT");

    try {
      this.state.syncState = "LOADING_SNAPSHOT";
      this.state.connectionState = "CONNECTING";
      this.notify();

      const scenarioRes = await fetch(`${API_BASE}/api/v1/fikracore/scenarios/${targetScenarioId}`, {
        signal: this.abortController.signal,
      });
      if (!scenarioRes.ok) throw new Error(`Failed to load scenario metadata: ${scenarioRes.statusText}`);
      const scenarioData = await scenarioRes.json();
      const resolvedScenarioId = scenarioData.scenario?.id || targetScenarioId;

      const runRes = await fetch(`${API_BASE}/api/v1/fikracore/scenarios/${resolvedScenarioId}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "live", fresh: true }),
        signal: this.abortController.signal,
      });
      if (!runRes.ok) throw new Error(`Failed to resolve scenario run: ${runRes.statusText}`);
      const runData = await runRes.json();
      const runId = runData.run_id;

      const snapshotRes = await fetch(`${API_BASE}/api/v1/fikracore/runs/${runId}/snapshot`, {
        signal: this.abortController.signal,
      });
      if (!snapshotRes.ok) throw new Error(`Failed to load run snapshot: ${snapshotRes.statusText}`);
      const data = await snapshotRes.json();

      if (version !== this.switchVersion) return;
      this.validateSnapshotIdentity(data, resolvedScenarioId, runId);
      this.applySnapshot(data);
      this.activeScenarioId = resolvedScenarioId;
      this.activeRunId = runId;
      this.state.syncState = "CONNECTING_LIVE_STREAM";
      this.state.connectionState = "CONNECTING";
      this.notify();

      this.connectLiveStream(runId);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      console.warn("Manual simulation start failed:", err);
      this.state.connectionState = "DEGRADED";
      this.state.syncState = "ERROR";
      this.notify();
    }
  }

  public async pauseSimulation(): Promise<void> {
    if (!this.state.run) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/simulations/${this.state.run.run_id}/pause`, {
        method: "POST",
      });
      if (res.ok) {
        this.state.run.status = "PAUSED";
        this.notify();
      }
    } catch {
      this.state.run.status = "PAUSED";
      this.notify();
    }
  }

  public async resumeSimulation(): Promise<void> {
    if (!this.state.run) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/simulations/${this.state.run.run_id}/resume`, {
        method: "POST",
      });
      if (res.ok) {
        this.state.run.status = "RUNNING";
        this.notify();
      }
    } catch {
      this.state.run.status = "RUNNING";
      this.notify();
    }
  }

  public async stopSimulation(): Promise<void> {
    if (!this.state.run) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/simulations/${this.state.run.run_id}/stop`, {
        method: "POST",
      });
      if (res.ok) {
        this.state.run.status = "STOPPED";
        this.state.run_status = "STOPPED";
        this.disconnectLiveStream();
        this.notify();
      }
    } catch {
      this.state.run.status = "STOPPED";
      this.state.run_status = "STOPPED";
      this.disconnectLiveStream();
      this.notify();
    }
  }

  public async replaySimulation(): Promise<void> {
    if (!this.state.run) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/simulations/${this.state.run.run_id}/replay`, {
        method: "POST",
      });
      if (res.ok) {
        const runId = this.state.run.run_id;
        const snapshotRes = await fetch(`${API_BASE}/api/v1/fikracore/runs/${runId}/snapshot`);
        if (snapshotRes.ok) {
          const data = await snapshotRes.json();
          this.applySnapshot(data);
        } else {
          this.state.run.status = "RUNNING";
          this.state.run.elapsed_seconds = 0;
        }
        this.notify();
      }
    } catch (err) {
      console.warn("Replay failed:", err);
    }
  }

  public async executeAction(actionId: string): Promise<void> {
    if (!this.state.run) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/simulations/${this.state.run.run_id}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: actionId }),
      });
      if (res.ok) {
        const result = await res.json();
        if (result.status === "ERROR") {
          console.warn("Evidence action rejected:", result.message);
          return;
        }
        const completedId = (result.action_id as string | undefined) || actionId;
        // Update local action state
        this.state.nextBestActions = this.state.nextBestActions.map((act) =>
          act.id === actionId || act.id === completedId ? { ...act, status: "COMPLETED" } : act
        );
        if (result.hypothesis_update) {
          this.state.hypotheses = this.state.hypotheses.map((h) =>
            h.id === result.hypothesis_update.id ? { ...h, confidence: result.hypothesis_update.confidence, tested: true } : h
          );
        }
        this.notify();
        await this.resyncActiveRun();
      }
    } catch (err) {
      console.warn("Evidence action failed:", err);
    }
  }

  public connectLiveStream(runId: string): void {
    this.disconnectLiveStream();

    try {
      this.eventSource = new EventSource(`${API_BASE}/api/v1/fikracore/simulations/${runId}/live`);
      this.eventSource.onopen = () => {
        this.state.connectionState = "LIVE";
        this.state.syncState = "SYNCED";
        this.notify();
      };

      this.eventSource.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);
          this.handleLiveDelta(payload);
        } catch (err) {
          console.error("Failed to parse live event SSE data:", err);
        }
      };

      this.eventSource.onerror = () => {
        if (this.state.connectionState === "LIVE") {
          this.state.connectionState = "DEGRADED";
          this.notify();
        }
      };
    } catch {
      this.state.connectionState = "DISCONNECTED";
      this.notify();
    }
  }

  public handleLiveDelta(payload: Record<string, unknown>): void {
    if (!this.isLiveMessageForActiveContext(payload)) {
      return;
    }

    const sequence = Number((payload.sequence as number | string | undefined) ?? 0);
    const revision = Number(
      (payload.revision as number | string | undefined) ??
      (payload.snapshot_version as number | string | undefined) ??
      0
    );
    if (revision && this.currentRevision && revision < this.currentRevision) {
      return;
    }
    if (sequence && this.lastSequence && sequence <= this.lastSequence) {
      return;
    }
    if (sequence && this.lastSequence && sequence > this.lastSequence + 1) {
      this.resyncActiveRun();
      return;
    }
    if (sequence) this.lastSequence = sequence;
    if (revision) this.currentRevision = revision;

    this.state.current_stage = payload.current_stage as string | undefined ?? this.state.current_stage;
    this.state.stage_status = payload.stage_status as string | undefined ?? this.state.stage_status;
    this.state.entered_at = payload.entered_at as string | undefined ?? this.state.entered_at;
    this.state.elapsed_ms = payload.elapsed_ms as number | undefined ?? this.state.elapsed_ms;
    this.state.exit_conditions = payload.exit_conditions as string[] | undefined ?? this.state.exit_conditions;
    this.state.exit_condition_state = payload.exit_condition_state as Record<string, unknown> | undefined ?? this.state.exit_condition_state;
    this.state.next_stage = payload.next_stage as string | null | undefined ?? this.state.next_stage;
    this.state.blocking_reason = payload.blocking_reason as string | null | undefined ?? this.state.blocking_reason;

    const runPatch = payload.run as Partial<SimulationRunMeta> | undefined;
    if (runPatch && this.state.run) {
      this.state.run = {
        ...this.state.run,
        ...runPatch,
      };
    }

    const stages = payload.stages as SimulationStage[] | undefined;
    if (stages) {
      this.state.stages = stages;
    }
    const events = (payload.events as SimulationEvent[] | undefined) ?? (payload.raw_events as SimulationEvent[] | undefined);
    if (events) {
      this.state.events = events;
      this.state.rawEvents = (payload.raw_events as SimulationEvent[] | undefined) || events;
    } else if (payload.raw_events) {
      this.state.rawEvents = payload.raw_events as SimulationEvent[];
    }
    const reasoningTrace = payload.reasoning_trace as ReasoningTraceRecord[] | undefined;
    if (reasoningTrace) {
      this.state.reasoningTrace = reasoningTrace;
    }
    const topology = payload.topology as SimulationTopology | undefined;
    if (topology) {
      this.state.topology = topology;
    }
    const evidenceClusters = payload.evidence_clusters as EvidenceCluster[] | undefined;
    if (evidenceClusters) {
      this.state.evidenceClusters = evidenceClusters;
    }
    const frontiers = payload.frontiers as UnknownFrontier[] | undefined;
    if (frontiers) {
      this.state.frontiers = frontiers;
    }
    const searchSpace = payload.search_space as SearchSpaceState | undefined;
    if (searchSpace) {
      this.state.searchSpace = searchSpace;
    }
    const reasoningFocus = payload.reasoning_focus as ReasoningFocusState | undefined;
    if (reasoningFocus) {
      this.state.reasoningFocus = reasoningFocus;
    }
    const reasoningMap = payload.reasoning_map as ReasoningMapState | undefined;
    if (reasoningMap) {
      this.state.reasoningMap = reasoningMap;
    }
    const hypotheses = payload.hypotheses as SimulationHypothesis[] | undefined;
    if (hypotheses) {
      this.state.hypotheses = hypotheses;
    }
    const reasoningTasks = payload.reasoning_tasks as ReasoningTask[] | undefined;
    if (reasoningTasks) {
      this.state.reasoningTasks = reasoningTasks;
    }
    const impact = payload.impact as ImpactState | undefined;
    if (impact) {
      this.state.impact = impact;
    }
    const knowledgeGaps = payload.knowledge_gaps as KnowledgeGap[] | undefined;
    if (knowledgeGaps) {
      this.state.knowledgeGaps = knowledgeGaps;
    }
    const nextBestActions = (payload.next_best_evidence as NextBestAction[] | undefined) ?? (payload.next_best_actions as NextBestAction[] | undefined);
    if (nextBestActions) {
      this.state.nextBestActions = nextBestActions;
    }
    const learning = payload.learning as LearningState | undefined;
    if (learning) {
      this.state.learning = learning;
    }
    const zaki = payload.zaki as ZakiCognitiveState | undefined;
    if (zaki) {
      this.state.zaki = zaki;
    }
    const storyContext = payload.story_context as Record<string, unknown> | undefined;
    if (storyContext) {
      this.state.storyContext = storyContext;
    }
    this.state.scenario_id = (payload.scenario_id as string | undefined) || this.state.scenario_id;
    this.state.run_id = (payload.run_id as string | undefined) || this.state.run_id;
    this.state.sequence = sequence || this.state.sequence;
    this.state.snapshot_version = revision || this.state.snapshot_version;
    this.state.revision = revision || this.state.revision;
    this.state.updated_at = (payload.updated_at as string | undefined) || (payload.timestamp as string | undefined) || this.state.updated_at;
    this.state.lastUpdate = new Date().toLocaleTimeString();
    this.notify();
  }

  public applySnapshot(data: Record<string, unknown>): void {
    const scenarioId = (data.scenario_id as string | undefined) ?? (data.scenario as Record<string, unknown> | undefined)?.id as string | undefined ?? (data.run as Record<string, unknown> | undefined)?.scenario_id as string | undefined;
    const runId = (data.run_id as string | undefined) ?? (data.run as Record<string, unknown> | undefined)?.run_id as string | undefined;
    const nextBestActions = (data.next_best_evidence as NextBestAction[] | undefined) ?? (data.next_best_actions as NextBestAction[] | undefined) ?? [];

    if (scenarioId) this.activeScenarioId = scenarioId;
    if (runId) this.activeRunId = runId;

    this.state = {
      scenario_id: scenarioId,
      run_id: runId,
      snapshot_version: (data.snapshot_version as number | undefined) || 0,
      revision: (data.revision as number | undefined) || (data.snapshot_version as number | undefined) || 0,
      sequence: (data.sequence as number | undefined) || 0,
      updated_at: data.updated_at as string | undefined,
      current_stage: data.current_stage as string | undefined,
      stage_status: data.stage_status as string | undefined,
      entered_at: data.entered_at as string | undefined,
      elapsed_ms: data.elapsed_ms as number | undefined,
      exit_conditions: data.exit_conditions as string[] | undefined,
      exit_conditions_detail: (data.exit_conditions_detail as StageExitCondition[] | undefined) || [],
      exit_condition_state: data.exit_condition_state as Record<string, unknown> | undefined,
      next_stage: data.next_stage as string | null | undefined,
      blocking_reason: data.blocking_reason as string | null | undefined,
      waiting_for: (data.waiting_for as string | null | undefined) ?? null,
      terminal_state: (data.terminal_state as string | null | undefined) ?? (data.run as Record<string, unknown> | undefined)?.terminal_state as string | null | undefined ?? null,
      is_replay: Boolean(data.is_replay ?? (data.run as Record<string, unknown> | undefined)?.is_replay),
      replay_position: (data.replay_position as number | undefined) ?? (data.run as Record<string, unknown> | undefined)?.replay_position as number | undefined ?? 0,
      run_status: (data.status as string | undefined) ?? (data.run as Record<string, unknown> | undefined)?.status as string | undefined ?? undefined,
      scenario: data.scenario as ScenarioMeta | null | undefined ?? null,
      run: data.run as SimulationRunMeta | null | undefined ?? null,
      stages: (data.journey as SimulationStage[] | undefined) ?? (data.stages as SimulationStage[] | undefined) ?? [],
      events: (data.events as SimulationEvent[] | undefined) ?? (data.raw_events as SimulationEvent[] | undefined) ?? [],
      rawEvents: (data.raw_events as SimulationEvent[] | undefined) ?? (data.events as SimulationEvent[] | undefined) ?? [],
      reasoningTrace: (data.reasoning_trace as ReasoningTraceRecord[] | undefined) ?? [],
      topology: (data.topology as SimulationTopology | null | undefined) ?? null,
      evidenceClusters: (data.evidence_clusters as EvidenceCluster[] | undefined) ?? [],
      frontiers: (data.frontiers as UnknownFrontier[] | undefined) ?? [],
      searchSpace: (data.search_space as SearchSpaceState | null | undefined) ?? null,
      reasoningFocus: (data.reasoning_focus as ReasoningFocusState | null | undefined) ?? null,
      reasoningMap: (data.reasoning_map as ReasoningMapState | null | undefined) ?? null,
      hypotheses: (data.hypotheses as SimulationHypothesis[] | undefined) ?? [],
      reasoningTasks: (data.reasoning_tasks as ReasoningTask[] | undefined) ?? [],
      impact: (data.impact as ImpactState | null | undefined) ?? null,
      knowledgeGaps: (data.knowledge_gaps as KnowledgeGap[] | undefined) ?? [],
      nextBestActions,
      learning: (data.learning as LearningState | null | undefined) ?? null,
      zaki: (data.zaki as ZakiCognitiveState | null | undefined) ?? null,
      storyContext: (data.story_context as Record<string, unknown> | undefined) ?? null,
      source_mode: (data.source_mode as "SIMULATION" | "LIVE_INTENT" | undefined) ?? (data.run as Record<string, unknown> | undefined)?.source_mode as "SIMULATION" | "LIVE_INTENT" | undefined ?? this.state.source_mode ?? "SIMULATION",
      intent_id: (data.intent_id as string | undefined) ?? (data.run as Record<string, unknown> | undefined)?.intent_id as string | undefined ?? this.state.intent_id ?? null,
      live_intents: this.state.live_intents || [],
      connectionState: this.state.connectionState,
      syncState: this.state.syncState,
      lastUpdate: new Date().toLocaleTimeString(),
    };
    this.lastSequence = (data.sequence as number | undefined) || 0;
    this.currentRevision =
      (data.revision as number | undefined) ||
      (data.snapshot_version as number | undefined) ||
      0;
    this.notify();
  }

  private notify(): void {
    this.onStateChange({ ...this.state });
  }

  public destroy(): void {
    this.abortController?.abort();
    this.disconnectLiveStream();
  }

  private disconnectLiveStream(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  public switchSourceMode(mode: "SIMULATION" | "LIVE_INTENT"): void {
    const prevMode = this.state.source_mode || "SIMULATION";
    if (prevMode === mode) return;

    this.disconnectLiveStream();
    this.activeRunId = null;
    this.activeScenarioId = null;
    this.lastSequence = 0;
    this.currentRevision = 0;
    this.switchVersion++;

    this.resetScenarioScopedState("IDLE");
    this.state.source_mode = mode;
    this.state.intent_id = null;
    this.state.scenario_id = undefined;
    this.notify();
  }

  public async loadLiveIntents(): Promise<LiveIntentMeta[]> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/live/intents`);
      if (!res.ok) throw new Error(`Failed to load live intents: ${res.statusText}`);
      const data = await res.json();
      const intents = (data.intents as LiveIntentMeta[]) || [];
      this.state.live_intents = intents;
      this.notify();
      return intents;
    } catch (err) {
      console.warn("Failed to load live intents:", err);
      return [];
    }
  }

  public async startLiveInvestigation(intentId: string): Promise<void> {
    const version = ++this.switchVersion;
    this.abortController?.abort();
    this.abortController = new AbortController();
    this.disconnectLiveStream();
    this.lastSequence = 0;
    this.currentRevision = 0;
    this.resetScenarioScopedState("LOADING_SNAPSHOT");
    this.state.source_mode = "LIVE_INTENT";
    this.state.intent_id = intentId;

    try {
      this.state.syncState = "LOADING_SNAPSHOT";
      this.state.connectionState = "CONNECTING";
      this.notify();

      const actRes = await fetch(`${API_BASE}/api/v1/fikracore/live/intents/${intentId}/activate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: this.abortController.signal,
      });
      if (!actRes.ok) throw new Error(`Failed to activate live intent: ${actRes.statusText}`);
      const actData = await actRes.json();
      const runId = actData.run_id;

      const snapshotRes = await fetch(`${API_BASE}/api/v1/fikracore/runs/${runId}/snapshot`, {
        signal: this.abortController.signal,
      });
      if (!snapshotRes.ok) throw new Error(`Failed to load run snapshot: ${snapshotRes.statusText}`);
      const data = await snapshotRes.json();

      if (version !== this.switchVersion) return;
      this.applySnapshot(data);
      this.activeRunId = runId;
      this.state.source_mode = "LIVE_INTENT";
      this.state.intent_id = intentId;
      this.state.syncState = "CONNECTING_LIVE_STREAM";
      this.state.connectionState = "CONNECTING";
      this.notify();

      this.connectLiveStream(runId);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      console.warn("Live investigation start failed:", err);
      this.state.connectionState = "DEGRADED";
      this.state.syncState = "ERROR";
      this.notify();
    }
  }

  public resetScenarioScopedState(syncState: SimulationState["syncState"]): void {
    this.state = {
      scenario_id: this.activeScenarioId || undefined,
      run_id: undefined,
      source_mode: this.state.source_mode || "SIMULATION",
      intent_id: this.state.intent_id || null,
      live_intents: this.state.live_intents || [],
      snapshot_version: 0,
      revision: 0,
      sequence: 0,
      updated_at: undefined,
      current_stage: undefined,
      stage_status: undefined,
      entered_at: undefined,
      elapsed_ms: undefined,
      exit_conditions: [],
      exit_condition_state: {},
      next_stage: null,
      blocking_reason: null,
      scenario: null,
      run: null,
      stages: [],
      events: [],
      rawEvents: [],
      reasoningTrace: [],
      topology: null,
      evidenceClusters: [],
      frontiers: [],
      searchSpace: null,
      reasoningFocus: null,
      reasoningMap: null,
      hypotheses: [],
      reasoningTasks: [],
      impact: null,
      knowledgeGaps: [],
      nextBestActions: [],
      learning: null,
      zaki: null,
      exit_conditions_detail: [],
      waiting_for: null,
      terminal_state: null,
      is_replay: false,
      replay_position: 0,
      run_status: "STOPPED",
      connectionState: "DISCONNECTED",
      syncState,
      lastUpdate: "",
    };
    this.currentRevision = 0;
    this.zakiUIState.selectedContext = null;
    this.zakiUIState.lastResponse = null;
    this.notify();
  }

  public async zakiChat(request: ZakiChatClientRequest): Promise<ZakiChatResponse> {
    const payload = {
      query: request.query || request.message,
      message: request.message || request.query,
      scenario_id: request.scenario_id || this.state.scenario_id,
      run_id: request.run_id || this.state.run_id,
      source_mode: request.source_mode || this.state.source_mode || "SIMULATION",
      intent_id: request.intent_id !== undefined ? request.intent_id : this.state.intent_id,
      revision: request.revision ?? this.state.revision,
      response_level: request.response_level || "ENGINEER",
      selected_context: request.selected_context,
    };

    const res = await fetch(`${API_BASE}/api/v1/fikracore/zaki/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Zaki chat request failed: ${res.statusText}`);
    }
    return res.json();
  }

  public getZakiUIState(): ZakiUIState {
    return { ...this.zakiUIState };
  }

  public setSelectedContext(context: ZakiSelectedContext | null): void {
    this.zakiUIState.selectedContext = context ? { ...context } : null;
    this.notify();
  }

  public clearSelectedContext(): void {
    this.zakiUIState.selectedContext = null;
    this.notify();
  }

  public setZakiMode(mode: "COMPACT" | "EXPANDED" | "DOCKED"): void {
    this.zakiUIState.mode = mode;
    this.notify();
  }

  public setResponseLevel(level: "executive" | "operator" | "engineer" | "deep"): void {
    this.zakiUIState.responseLevel = level;
    this.notify();
  }

  public async askZaki(
    query: string,
    options?: {
      context?: ZakiSelectedContext;
      responseLevel?: "executive" | "operator" | "engineer" | "deep";
    }
  ): Promise<ZakiResponseV2> {
    const ctx = options?.context ?? this.zakiUIState.selectedContext ?? undefined;
    const level = options?.responseLevel ?? this.zakiUIState.responseLevel;
    this.zakiUIState.isLoading = true;
    this.zakiUIState.error = null;
    this.notify();

    try {
      const resp = await this.zakiChat({
        query,
        message: query,
        scenario_id: this.state.scenario_id,
        run_id: this.state.run_id,
        source_mode: this.state.source_mode || "SIMULATION",
        intent_id: this.state.intent_id,
        revision: this.state.revision,
        response_level: (level.toUpperCase() as "EXECUTIVE" | "OPERATOR" | "ENGINEER" | "DEEP_TECHNICAL"),
        selected_context: ctx as Record<string, unknown> | undefined,
      });

      const zakiResp = (resp.zaki_v2 || resp) as unknown as ZakiResponseV2;
      this.zakiUIState.lastResponse = zakiResp;
      this.zakiUIState.isLoading = false;
      this.zakiUIState.history.push({
        id: `zaki-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        query,
        response: zakiResp,
        timestamp: new Date().toISOString(),
      });
      this.notify();
      return zakiResp;
    } catch (err: unknown) {
      this.zakiUIState.isLoading = false;
      this.zakiUIState.error = (err as Error).message;
      this.notify();
      throw err;
    }
  }

  public validateSnapshotIdentity(data: Record<string, unknown>, scenarioId: string, runId: string): void {
    const snapshotScenarioId = (data.scenario_id as string | undefined) ?? ((data.scenario as Record<string, unknown> | undefined)?.id as string | undefined) ?? ((data.run as Record<string, unknown> | undefined)?.scenario_id as string | undefined);
    const snapshotRunId = (data.run_id as string | undefined) ?? ((data.run as Record<string, unknown> | undefined)?.run_id as string | undefined);
    if (snapshotScenarioId !== scenarioId || snapshotRunId !== runId) {
      throw new Error(
        `STATE OUT OF SYNC: expected ${scenarioId}/${runId}, received ${snapshotScenarioId}/${snapshotRunId}`
      );
    }
  }

  public isLiveMessageForActiveContext(payload: Record<string, unknown>): boolean {
    const scenarioId = (payload.scenario_id as string | undefined) ?? ((payload.run as Record<string, unknown> | undefined)?.scenario_id as string | undefined);
    const runId = (payload.run_id as string | undefined) ?? ((payload.run as Record<string, unknown> | undefined)?.run_id as string | undefined);
    if (!this.activeRunId || runId !== this.activeRunId) {
      return false;
    }
    if (scenarioId && this.activeScenarioId && scenarioId !== this.activeScenarioId) {
      return false;
    }
    return true;
  }

  private async resyncActiveRun(): Promise<void> {
    if (!this.activeScenarioId || !this.activeRunId) return;
    this.state.syncState = "RESYNCING";
    this.notify();
    try {
      const res = await fetch(`${API_BASE}/api/v1/fikracore/runs/${this.activeRunId}/snapshot`);
      if (!res.ok) throw new Error(`Failed to resync snapshot: ${res.statusText}`);
      const data = await res.json();
      this.validateSnapshotIdentity(data, this.activeScenarioId, this.activeRunId);
      this.applySnapshot(data);
      this.state.connectionState = "LIVE";
      this.state.syncState = "SYNCED";
      this.notify();
    } catch {
      this.state.connectionState = "DEGRADED";
      this.state.syncState = "ERROR";
      this.notify();
    }
  }
}
