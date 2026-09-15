export type MarkCapabilityKind = "engine" | "service" | "connector" | "namespace";

export type MarkCapabilityStatus = "online" | "standby" | "degraded" | "requires_approval";

export type MarkVisualState =
  | "idle"
  | "listening"
  | "processing"
  | "speaking"
  | "investigating"
  | "waiting_for_approval"
  | "learning";

export type MarkCapabilityNode = {
  id: string;
  label: string;
  shortLabel: string;
  kind: MarkCapabilityKind;
  parentId?: string;
  color: string;
  role: string;
  handles: string[];
  namespaces?: string[];
  connectors?: string[];
  actions?: string[];
  status: MarkCapabilityStatus;
};

export type MarkRouteTrace = {
  state: MarkVisualState;
  activeEngineId?: string;
  activeServiceIds?: string[];
  activeConnectorIds?: string[];
  activeNamespaces?: string[];
  claimIds?: string[];
  summary?: string;
};

export const MARK_ENGINE_NODES: MarkCapabilityNode[] = [
  {
    id: "telecom_brain",
    label: "Telecom Brain",
    shortLabel: "Telecom",
    kind: "engine",
    color: "#00e5ff",
    role: "Telecom incidents, alarms, KPIs, topology projections, intents, RCA, storytelling, and FCAPS learning.",
    handles: ["Incident operations", "RCA", "Semantic telecom reasoning", "Learning loop"],
    namespaces: ["domains/*", "incidents/*", "correlation/*", "storytelling/*", "learning/*"],
    connectors: ["gbrain", "grafana_lgtm", "nautobot"],
    actions: ["Tell the incident story", "Run RCA", "Review service intent"],
    status: "online",
  },
  {
    id: "knowledge_base",
    label: "Knowledge Base",
    shortLabel: "Knowledge",
    kind: "engine",
    color: "#7dd3fc",
    role: "Metadata-first knowledge answering with selective document and vector retrieval.",
    handles: ["Document inventory", "Knowledge search", "Context narrowing"],
    namespaces: ["knowledge/*", "assets/*"],
    connectors: ["metadata_db", "vector_db", "office"],
    actions: ["Search similar history", "Inspect assets", "Summarize documents"],
    status: "online",
  },
  {
    id: "automation",
    label: "Automation",
    shortLabel: "Automation",
    kind: "engine",
    color: "#f5a623",
    role: "Approved diagnostics, pre-checks, health checks, and remediation proposals.",
    handles: ["Diagnostics", "Pre-checks", "Approval-gated remediation"],
    connectors: ["gbrain"],
    actions: ["Run health check", "Prepare remediation", "Validate change"],
    status: "requires_approval",
  },
  {
    id: "collaboration",
    label: "Collaboration",
    shortLabel: "Collab",
    kind: "engine",
    color: "#a78bfa",
    role: "Turns Mark analysis into controlled stakeholder communication.",
    handles: ["Email drafts", "WhatsApp updates", "Teams handovers"],
    connectors: ["gmail", "whatsapp", "teams"],
    actions: ["Draft stakeholder update", "Prepare handover", "Summarize bridge"],
    status: "standby",
  },
  {
    id: "calendar",
    label: "Calendar",
    shortLabel: "Calendar",
    kind: "engine",
    color: "#34d399",
    role: "Incident bridge scheduling, maintenance-window context, and reminders.",
    handles: ["Bridge scheduling", "Maintenance context", "Follow-up timing"],
    connectors: ["google_calendar"],
    actions: ["Schedule bridge", "Check maintenance window", "Set reminder"],
    status: "standby",
  },
  {
    id: "codex_engineering",
    label: "Codex Engineering",
    shortLabel: "Codex",
    kind: "engine",
    color: "#60a5fa",
    role: "Controlled coding, debugging, test execution, and sandboxed implementation work.",
    handles: ["Code inspection", "Implementation", "Tests", "Repository tasks"],
    connectors: ["codex"],
    actions: ["Inspect repository", "Implement fix", "Run tests"],
    status: "online",
  },
];

export const TELECOM_SERVICE_NODES: MarkCapabilityNode[] = [
  {
    id: "correlation",
    label: "Correlation Service",
    shortLabel: "Correlation",
    kind: "service",
    parentId: "telecom_brain",
    color: "#00e5ff",
    role: "Groups related alarms and evidence using time, service relevance, topology, telemetry support, and intent violation.",
    handles: ["Alarm grouping", "Hypothesis scoring", "Correlation reasons"],
    namespaces: ["correlation/*", "incidents/*", "grafana/*", "twin/*", "domains/*"],
    connectors: ["gbrain", "grafana_lgtm"],
    actions: ["Run RCA", "Show grouped evidence", "Explain correlation score"],
    status: "online",
  },
  {
    id: "topology",
    label: "Topology Service",
    shortLabel: "Topology",
    kind: "service",
    parentId: "telecom_brain",
    color: "#7dd3fc",
    role: "Resolves topology objects, dependencies, affected services, and digital twin projections.",
    handles: ["Dependency path", "Affected service", "Twin projection"],
    namespaces: ["twin/*", "domains/*"],
    connectors: ["nautobot", "gbrain"],
    actions: ["Show dependency path", "Inspect affected services", "Open twin projection"],
    status: "online",
  },
  {
    id: "telemetry_evidence",
    label: "Telemetry Evidence Service",
    shortLabel: "Telemetry",
    kind: "service",
    parentId: "telecom_brain",
    color: "#38bdf8",
    role: "Retrieves operational evidence from Grafana LGTM and projects relevant facts into gbrain.",
    handles: ["Metrics", "Logs", "Traces", "Alerts", "Dashboards"],
    namespaces: ["grafana/*"],
    connectors: ["grafana_lgtm", "gbrain"],
    actions: ["Fetch KPI history", "Inspect logs", "List dashboards"],
    status: "online",
  },
  {
    id: "storytelling",
    label: "Storytelling Service",
    shortLabel: "Story",
    kind: "service",
    parentId: "telecom_brain",
    color: "#f5a623",
    role: "Explains incidents deterministically from gbrain facts, links, claims, and provenance.",
    handles: ["Written story", "Spoken brief", "Visual explanation", "Audience views"],
    namespaces: ["storytelling/*", "incidents/*", "correlation/*"],
    connectors: ["gbrain"],
    actions: ["Render NOC brief", "Render executive summary", "Open investigation"],
    status: "online",
  },
  {
    id: "incident_registry",
    label: "Incident Registry Service",
    shortLabel: "Registry",
    kind: "service",
    parentId: "telecom_brain",
    color: "#fb7185",
    role: "Resolves canonical incident identity, aliases, lifecycle state, and active incident lists.",
    handles: ["Incident lookup", "Lifecycle state", "Candidate queue"],
    namespaces: ["incidents/*"],
    connectors: ["gbrain"],
    actions: ["List current incidents", "Resolve incident ID", "Inspect lifecycle"],
    status: "online",
  },
  {
    id: "intent",
    label: "Intent Service",
    shortLabel: "Intent",
    kind: "service",
    parentId: "telecom_brain",
    color: "#c4b5fd",
    role: "Maps service procedures to measurable objectives and detects intent violation.",
    handles: ["Service objectives", "KPI targets", "Intent state"],
    namespaces: ["domains/*/intents/*", "domains/*/service-procedures/*"],
    connectors: ["gbrain", "grafana_lgtm"],
    actions: ["Show violated intent", "Inspect KPI target", "Review procedure mapping"],
    status: "online",
  },
  {
    id: "fcaps_learning",
    label: "FCAPS Learning Service",
    shortLabel: "Learning",
    kind: "service",
    parentId: "telecom_brain",
    color: "#fbbf24",
    role: "Uses FCAPS as a learning lens to create reviewable notes and asset update proposals.",
    handles: ["Learning notes", "Asset gaps", "Proposed context improvements"],
    namespaces: ["learning/*", "assets/*"],
    connectors: ["gbrain"],
    actions: ["Review learning note", "Inspect asset gap", "Approve context update"],
    status: "requires_approval",
  },
];

export const MARK_CONNECTOR_NODES: MarkCapabilityNode[] = [
  {
    id: "gbrain",
    label: "gbrain MCP",
    shortLabel: "gbrain",
    kind: "connector",
    color: "#00e5ff",
    role: "Semantic telecom brain for knowledge, observations, learnings, projections, incidents, and story traces.",
    handles: ["Semantic graph", "Page retrieval", "Typed links", "Learning notes"],
    namespaces: ["knowledge/*", "assets/*", "domains/*", "twin/*", "grafana/*", "correlation/*", "incidents/*", "storytelling/*", "learning/*"],
    actions: ["List pages", "Get page", "Get links"],
    status: "online",
  },
  {
    id: "grafana_lgtm",
    label: "Grafana LGTM",
    shortLabel: "Grafana",
    kind: "connector",
    color: "#f5a623",
    role: "Runtime telemetry evidence source for metrics, logs, traces, alerts, dashboards, and panels.",
    handles: ["Prometheus metrics", "Loki logs", "Traces", "Alerts"],
    namespaces: ["grafana/*"],
    actions: ["Query metric", "Query logs", "List dashboards"],
    status: "online",
  },
  {
    id: "nautobot",
    label: "Nautobot / Topology DB",
    shortLabel: "Nautobot",
    kind: "connector",
    color: "#7dd3fc",
    role: "Topology and digital twin authority. gbrain stores only projections from this source.",
    handles: ["Devices", "Interfaces", "Links", "Sites", "Circuits"],
    namespaces: ["twin/*"],
    actions: ["Resolve topology", "Trace dependency", "Inspect ownership"],
    status: "standby",
  },
];

export const MARK_CAPABILITY_NODES: MarkCapabilityNode[] = [
  ...MARK_ENGINE_NODES,
  ...TELECOM_SERVICE_NODES,
  ...MARK_CONNECTOR_NODES,
];

export function getCapabilityNode(id?: string | null): MarkCapabilityNode | undefined {
  if (!id) return undefined;
  return MARK_CAPABILITY_NODES.find((node) => node.id === id);
}

export function getTelecomServiceNodes(): MarkCapabilityNode[] {
  return TELECOM_SERVICE_NODES;
}

export function getEngineNodes(): MarkCapabilityNode[] {
  return MARK_ENGINE_NODES;
}

