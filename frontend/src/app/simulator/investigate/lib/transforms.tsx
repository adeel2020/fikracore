/**
 * Pure data transform functions for the Investigate workspace.
 * These functions derive UI-ready data from raw simulation state.
 * No JSX. No React hooks. Fully testable in isolation.
 *
 * Extracted from page.tsx (L416–L1821).
 */

import type { SimulationState } from "@/lib/simulation-store";
import {
  AlertTriangle,
  Activity,
  FileText,
  GitBranch,
  Layers,
  Ticket,
  Users,
  Settings,
  Database,
  UserCheck,
  FileCode,
  BarChart3,
  Wifi,
  ShieldAlert,
  History,
  BookOpen,
  Cloud,
  Globe,
  Lock,
  Radio,
} from "lucide-react";
import type {
  EvidenceItem,
  PathwayItem,
  HypothesisItem,
  GapItem,
  NextBestEvidenceItem,
  ScenarioAttributionProfile,
  DomainClassification,
  DomainAttributionInfo,
  TraceTarget,
  DetailedConduitTelemetry,
  DetailedEntityModal,
} from "./types";
import {
  OPERATIONAL_DOMAINS_CATALOG,
  EVIDENCE_TO_PATHWAY_CONDUITS,
  PATHWAYS_TO_HYPS,
  HYP_TO_PATHWAYS,
  HYP_TO_VALIDATION_CONDUITS,
  HYPOTHESES_LIST,
  HYPOTHESIS_COLORS,
  HYPOTHESIS_PROGRESS,
  EVIDENCE_LIST,
  PATHWAYS_LIST,
} from "./conduit-math";

// ─── Event Icon Helper ────────────────────────────────────────────────────────

type EventStreamType = "ALARM" | "METRIC" | "TICKET" | "TRACE" | "LOG" | "CHANGE";

function eventIconForType(type: EventStreamType) {
  switch (type) {
    case "ALARM": return AlertTriangle;
    case "METRIC": return Activity;
    case "TICKET": return Ticket;
    case "TRACE": return GitBranch;
    case "LOG": return FileText;
    case "CHANGE": return Layers;
  }
}

// ─── Domain Attribution Profile ───────────────────────────────────────────────

export function getScenarioAttributionProfile(
  scenarioId: string | null | undefined,
  registryEntry?: { tags?: string[]; domains?: string[]; description?: string; services?: string[] } | null,
  simulationState?: SimulationState | {
    run?: { status?: string } | null;
    scenario_id?: string;
    current_stage?: string;
    revision?: number;
    sequence?: number;
    domain_attribution?: {
      status?: string;
      attribution_status?: "CONSISTENT" | "PARTIAL" | "UNRESOLVED" | "CONFLICT";
      conflict_reasons?: string[];
      revision?: number;
      sequence?: number;
      domains?: Array<{
        domain_id?: string;
        display_name: string;
        role: string;
        confidence?: number;
        reason?: string;
        attribution_basis?: string;
        supporting_hypothesis_ids?: string[];
        source_revision?: number;
      }>;
    };
    reasoningMap?: {
      domain_attribution?: {
        status?: string;
        attribution_status?: "CONSISTENT" | "PARTIAL" | "UNRESOLVED" | "CONFLICT";
        conflict_reasons?: string[];
        revision?: number;
        sequence?: number;
        domains?: Array<{
          domain_id?: string;
          display_name: string;
          role: string;
          confidence?: number;
          reason?: string;
          attribution_basis?: string;
          supporting_hypothesis_ids?: string[];
          source_revision?: number;
        }>;
      };
    } | null;
    impact?: {
      service?: string;
      impact_state?: string;
      state?: string;
      throughput_impact_pct?: number | null;
      affected_services?: string[];
      affected_users?: number | null;
    } | null;
  } | null | Record<string, unknown>
): ScenarioAttributionProfile {
  const stateObj = simulationState as Record<string, unknown> | null | undefined;
  const reasoningMapObj = (stateObj?.reasoningMap || stateObj?.reasoning_map) as Record<string, unknown> | null | undefined;
  const backendAttr = (stateObj?.domain_attribution || reasoningMapObj?.domain_attribution) as {
    status?: string;
    attribution_status?: "CONSISTENT" | "PARTIAL" | "UNRESOLVED" | "CONFLICT";
    conflict_reasons?: string[];
    revision?: number;
    sequence?: number;
    domains?: Array<{
      domain_id?: string;
      display_name: string;
      role: string;
      confidence?: number;
      reason?: string;
      attribution_basis?: string;
      supporting_hypothesis_ids?: string[];
      source_revision?: number;
    }>;
  } | undefined;
  const backendDomains = backendAttr?.domains || [];

  const classifications: Record<string, DomainAttributionInfo> = {};
  const weights: Record<string, number> = {};

  // Initialize all catalog domains
  OPERATIONAL_DOMAINS_CATALOG.forEach((d) => {
    classifications[d.id] = {
      classification: "MONITOR ONLY",
      weight: 0,
      detail: `${d.name} telemetry within nominal baseline`,
    };
    weights[d.id] = 0;
  });

  let primaryDomainId = "";
  let primaryDomainName = "Attribution Pending";
  let primaryAttribution = 0;
  let primarySummary = "Domain attribution pending validation readiness";

  backendDomains.forEach((bd) => {
    const role = bd.role.toUpperCase();
    const matched = OPERATIONAL_DOMAINS_CATALOG.find((d) => {
      if (bd.domain_id && (d.id === bd.domain_id || d.id === bd.domain_id.toLowerCase())) {
        return true;
      }
      const dName = d.name.toLowerCase();
      const dShort = d.shortName.toLowerCase();
      const bName = bd.display_name.toLowerCase().trim();
      if (dName === bName || dShort === bName || d.id === bName.replace(/[\s/]+/g, "_")) {
        return true;
      }
      if (bName === "transport" && d.id === "transport") return true;
      if (bName === "ip transport" && d.id === "transport") return true;
      if (bName === "ran" && d.id === "ran") return true;
      if ((bName === "mobile core" || bName === "packet core" || bName === "core") && d.id === "mobile_core") return true;
      if ((bName === "ims" || bName === "ims / volte" || bName === "ims/volte" || bName === "voice") && d.id === "ims_voice") return true;
      const words = dName.split(/[\s/]+/);
      return words.some((w) => w.length > 2 && w === bName);
    });

    if (matched) {
      if (classifications[matched.id]?.classification === "PRIMARY" && role !== "PRIMARY") {
        return;
      }

      let classification: DomainClassification = "MONITOR ONLY";
      let weight = 0;
      if (role === "PRIMARY") {
        classification = "PRIMARY";
        weight = bd.confidence ?? 88;
        primaryDomainId = matched.id;
        primaryDomainName = matched.name;
        primaryAttribution = weight;
        primarySummary = bd.reason || `${matched.name} identified as primary cause`;
      } else if (role === "CONTRIBUTING") {
        classification = "CONTRIBUTING";
        weight = bd.confidence ?? 65;
      } else if (role === "AFFECTED") {
        classification = "AFFECTED";
        weight = bd.confidence ?? 45;
      } else if (role === "INVOLVED") {
        classification = "INVOLVED";
        weight = bd.confidence ?? 25;
      } else if (role === "NOT_RELEVANT") {
        classification = "NOT RELEVANT";
        weight = 0;
      }

      classifications[matched.id] = {
        classification,
        weight,
        detail: bd.reason || `${matched.name} ${classification.toLowerCase()} in active incident`,
        attributionBasis: bd.attribution_basis,
        supportingHypothesisIds: bd.supporting_hypothesis_ids,
        sourceRevision: bd.source_revision,
      };
      weights[matched.id] = weight;
    }
  });

  if (primaryAttribution > 0 && primaryDomainId) {
    const secondaryDomainMap: Record<string, Array<{ id: string; role: DomainClassification; weight: number; reason: string }>> = {
      ran: [
        { id: "transport", role: "CONTRIBUTING", weight: 62, reason: "Backhaul transport degradation impacting cell site connectivity" },
        { id: "mobile_core", role: "AFFECTED", weight: 38, reason: "Session drops and bearer teardown on User Plane (UPF)" },
      ],
      transport: [
        { id: "mobile_core", role: "CONTRIBUTING", weight: 60, reason: "Core gateway ingress packet loss and routing divergence" },
        { id: "ran", role: "AFFECTED", weight: 42, reason: "Downstream eNodeB/gNodeB backhaul capacity starvation" },
      ],
      mobile_core: [
        { id: "policy_subscriber", role: "CONTRIBUTING", weight: 58, reason: "PCF/UDM session authentication retry storm" },
        { id: "ims_voice", role: "AFFECTED", weight: 40, reason: "VoLTE/VoNR SIP session establishment timeouts" },
      ],
      ims_voice: [
        { id: "mobile_core", role: "CONTRIBUTING", weight: 55, reason: "IMS APN bearer allocation delays on SMF/UPF" },
        { id: "transport", role: "AFFECTED", weight: 35, reason: "RTP voice media stream packet jitter" },
      ],
      security: [
        { id: "transport", role: "CONTRIBUTING", weight: 55, reason: "Security gateway (SEGW) IPsec tunnel re-key storm" },
        { id: "mobile_core", role: "AFFECTED", weight: 36, reason: "Control plane signaling throttling" },
      ],
      cloud_k8s: [
        { id: "mobile_core", role: "CONTRIBUTING", weight: 58, reason: "NFVI container CNI network namespace packet loss" },
        { id: "transport", role: "AFFECTED", weight: 35, reason: "Underlay top-of-rack switch link saturation" },
      ],
    };

    const secondaryList = secondaryDomainMap[primaryDomainId] || [
      { id: "transport", role: "CONTRIBUTING" as DomainClassification, weight: 55, reason: "Transport path impacted" },
      { id: "mobile_core", role: "AFFECTED" as DomainClassification, weight: 35, reason: "Core network control plane impact" },
    ];

    secondaryList.forEach((sec) => {
      if (
        classifications[sec.id] &&
        (classifications[sec.id].classification === "MONITOR ONLY" || classifications[sec.id].classification === "NOT RELEVANT")
      ) {
        classifications[sec.id] = { classification: sec.role, weight: sec.weight, detail: sec.reason };
        weights[sec.id] = sec.weight;
      }
    });
  }

  const runObj = stateObj?.run as { status?: string } | null | undefined;
  const impactObj = stateObj?.impact as {
    service?: string;
    impact_state?: string;
    state?: string;
    throughput_impact_pct?: number | null;
    affected_services?: string[];
    affected_users?: number | null;
  } | null | undefined;

  const isStopped = runObj != null && runObj.status === "STOPPED";
  const isScenarioMismatch = Boolean(scenarioId && stateObj?.scenario_id && stateObj.scenario_id !== scenarioId);
  const hasNoRun = stateObj != null && "run" in stateObj && stateObj.run === null;

  const hasImpactExecution = Boolean(
    !isStopped && !isScenarioMismatch && !hasNoRun &&
    impactObj != null &&
    impactObj.impact_state !== "UNKNOWN" && impactObj.state !== "UNKNOWN" &&
    (
      (typeof impactObj.throughput_impact_pct === "number" && impactObj.throughput_impact_pct > 0) ||
      (Array.isArray(impactObj.affected_services) && impactObj.affected_services.length > 0) ||
      (typeof impactObj.affected_users === "number" && impactObj.affected_users > 0)
    )
  );

  let services: ScenarioAttributionProfile["services"] = [];

  if (hasImpactExecution && impactObj) {
    const dropPct = impactObj.throughput_impact_pct;
    const dropText = typeof dropPct === "number" ? `${dropPct}% drop` : "Degraded";
    const primarySvc = impactObj.service || registryEntry?.services?.[0] || "Primary Telecom Service";

    const svcList: string[] = [];
    if (primarySvc) svcList.push(primarySvc);
    if (Array.isArray(impactObj.affected_services)) {
      impactObj.affected_services.forEach((s) => { if (!svcList.includes(s)) svcList.push(s); });
    }

    const icons = [Cloud, Globe, Lock, Radio];
    services = svcList.map((svcName, idx) => {
      const isFirst = idx === 0;
      const status: "Severe" | "Degraded" | "Nominal" =
        isFirst && typeof dropPct === "number" && dropPct >= 40 ? "Severe" :
        isFirst ? "Degraded" :
        idx === 1 ? "Degraded" : "Nominal";
      return {
        name: svcName,
        status,
        drop: isFirst ? dropText : "Impaired",
        icon: icons[idx % icons.length] || Cloud,
      };
    });
  }

  return {
    primaryDomainId: primaryDomainId || "transport",
    primaryDomainName,
    primaryAttribution,
    primarySummary,
    domainWeights: weights,
    domainClassifications: classifications,
    services,
    attributionStatus: backendAttr?.attribution_status || (primaryAttribution > 0 ? "CONSISTENT" : "PARTIAL"),
    conflictReasons: backendAttr?.conflict_reasons || [],
    revision: backendAttr?.revision ?? (typeof stateObj?.revision === "number" ? (stateObj.revision as number) : undefined),
    sequence: backendAttr?.sequence ?? (typeof stateObj?.sequence === "number" ? (stateObj.sequence as number) : undefined),
  };
}

// ─── Evidence Items ───────────────────────────────────────────────────────────

export function buildEvidenceItems(
  simulationState?: SimulationState | null | Record<string, unknown>,
  currentScenarioId?: string | null
): EvidenceItem[] {
  const stateObj = simulationState as Record<string, unknown> | null | undefined;
  const isStopped = stateObj?.run != null && (stateObj.run as { status?: string }).status === "STOPPED";
  const isReady = stateObj?.run != null && (stateObj.run as { status?: string }).status === "READY";
  const isScenarioMismatch = Boolean(currentScenarioId && stateObj?.scenario_id && stateObj.scenario_id !== currentScenarioId);
  const hasNoRun = stateObj != null && "run" in stateObj && stateObj.run === null;
  const isInactive = !stateObj || isStopped || isReady || isScenarioMismatch || hasNoRun;

  const reasoningMap = stateObj?.reasoningMap as Record<string, unknown> | null | undefined;
  const mapEvidence = reasoningMap?.evidence as Record<string, unknown>[] | undefined;
  const rawEvents = stateObj?.rawEvents as Record<string, unknown>[] | undefined;
  const stateEvents = stateObj?.events as Record<string, unknown>[] | undefined;

  const events: Record<string, unknown>[] = !isInactive
    ? mapEvidence?.length ? mapEvidence : rawEvents?.length ? rawEvents : stateEvents || []
    : [];

  const counts: Record<string, number> = { alarms: 0, logs: 0, metrics: 0, traces: 0, changes: 0, tickets: 0, users: 0 };

  events.forEach((ev) => {
    const cat = String(ev.category || ev.type || ev.evidence_type || "").toLowerCase();
    if (cat.includes("alarm")) counts.alarms++;
    else if (cat.includes("log")) counts.logs++;
    else if (cat.includes("metric") || cat.includes("kpi")) counts.metrics++;
    else if (cat.includes("trace")) counts.traces++;
    else if (cat.includes("change")) counts.changes++;
    else if (cat.includes("ticket")) counts.tickets++;
    else if (cat.includes("user")) counts.users++;
  });

  const impact = (simulationState as SimulationState | null | undefined)?.impact;
  const affectedUsers = impact?.affected_users;
  if (typeof affectedUsers === "number" && affectedUsers > 0) {
    counts.users = Math.max(counts.users, Math.round(affectedUsers / 1000) || 1);
  }

  return [
    { id: "alarms", name: "Alarms", countLabel: counts.alarms === 1 ? "1 active" : `${counts.alarms} active`, count: counts.alarms, icon: AlertTriangle, color: "#f43f5e", bgGlow: "rgba(244,63,94,0.3)", borderColor: "border-rose-500" },
    { id: "logs", name: "Logs", countLabel: counts.logs === 1 ? "1 event" : `${counts.logs} events`, count: counts.logs, icon: FileText, color: "#38bdf8", bgGlow: "rgba(56,189,248,0.3)", borderColor: "border-sky-400" },
    { id: "metrics", name: "Metrics", countLabel: counts.metrics === 1 ? "1 anomaly" : `${counts.metrics} anomalies`, count: counts.metrics, icon: Activity, color: "#34d399", bgGlow: "rgba(52,211,153,0.3)", borderColor: "border-emerald-400" },
    { id: "traces", name: "Traces", countLabel: counts.traces === 1 ? "1 trace" : `${counts.traces} traces`, count: counts.traces, icon: GitBranch, color: "#c084fc", bgGlow: "rgba(192,132,252,0.3)", borderColor: "border-purple-400" },
    { id: "changes", name: "Changes", countLabel: counts.changes === 1 ? "1 recent" : `${counts.changes} recent`, count: counts.changes, icon: Layers, color: "#fbbf24", bgGlow: "rgba(251,191,36,0.3)", borderColor: "border-amber-400" },
    { id: "tickets", name: "Tickets", countLabel: counts.tickets === 1 ? "1 customer" : `${counts.tickets} tickets`, count: counts.tickets, icon: Ticket, color: "#60a5fa", bgGlow: "rgba(96,165,250,0.3)", borderColor: "border-blue-400" },
    {
      id: "users", name: "User Impact",
      countLabel: typeof affectedUsers === "number" && affectedUsers > 0
        ? `${(affectedUsers / 1000).toFixed(1)}k impacted`
        : counts.users > 0 ? `${counts.users} reports` : "Monitoring",
      count: counts.users, icon: Users, color: "#f472b6", bgGlow: "rgba(244,114,182,0.3)", borderColor: "border-pink-400",
    },
  ];
}

// ─── Pathway Items ────────────────────────────────────────────────────────────

export function buildPathwayItems(
  simulationState?: {
    scenario_id?: string;
    run?: unknown;
    reasoningMap?: {
      reasoning_pathways?: Array<{
        id?: string;
        pathway_id?: string;
        display_name: string;
        state?: string;
        status?: string;
        activation_reason?: string;
        explain?: { why?: string };
      }>;
    } | null;
  } | null,
  currentScenarioId?: string | null,
  activeStageIndex: number = -1
): PathwayItem[] {
  const isStopped = simulationState?.run != null && (simulationState.run as { status?: string }).status === "STOPPED";
  const isReady = simulationState?.run != null && (simulationState.run as { status?: string }).status === "READY";
  const isScenarioMismatch = Boolean(currentScenarioId && simulationState?.scenario_id && simulationState.scenario_id !== currentScenarioId);
  const hasNoRun = simulationState != null && "run" in simulationState && simulationState.run === null;
  const isInactive = !simulationState || isStopped || isReady || isScenarioMismatch || hasNoRun;

  const backendPathways = !isInactive ? simulationState?.reasoningMap?.reasoning_pathways || [] : [];

  const templatePathways: Array<{
    id: string;
    name: string;
    aliases: string[];
    icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
    color: string;
    defaultReason: string;
  }> = [
    { id: "operational", name: "Operational Evidence", aliases: ["operational", "evidence"], icon: Settings, color: "#38bdf8", defaultReason: "Raw alarms, telemetry anomalies and interface status admitted." },
    { id: "dependency", name: "Service Dependency", aliases: ["service dependency", "dependency"], icon: Database, color: "#fbbf24", defaultReason: "Dependent services mapped to upstream failure path." },
    { id: "subscriber", name: "Subscriber Journey", aliases: ["subscriber journey", "subscriber"], icon: UserCheck, color: "#c084fc", defaultReason: "Customer impact reports correlated with service degradation." },
    { id: "config", name: "Change & Configuration", aliases: ["change & configuration", "change", "config"], icon: FileCode, color: "#fb923c", defaultReason: "Recent configuration or maintenance changes evaluated." },
    { id: "traffic", name: "Traffic & Capacity", aliases: ["traffic & capacity", "traffic", "capacity"], icon: BarChart3, color: "#34d399", defaultReason: "Throughput metrics and capacity degradation evaluated." },
    { id: "signaling", name: "Control & Signaling", aliases: ["control & signaling", "signaling", "control"], icon: Wifi, color: "#22d3ee", defaultReason: "Control-plane and signaling adjacency evaluated." },
    { id: "resilience", name: "Resilience & Failover", aliases: ["resilience & failover", "resilience", "failover"], icon: ShieldAlert, color: "#14b8a6", defaultReason: "Redundant link status and standby path failover state." },
    { id: "historical", name: "Historical Pattern", aliases: ["historical pattern", "historical"], icon: History, color: "#f472b6", defaultReason: "Matching incident patterns from historical knowledge corpus." },
    { id: "enrichment", name: "Knowledge Gap", aliases: ["knowledge gap", "knowledge enrichment", "gap", "enrichment"], icon: BookOpen, color: "#818cf8", defaultReason: "Knowledge graph query for topological relationships and missing evidence." },
  ];

  return templatePathways.map((tmpl) => {
    const backendMatch = backendPathways.find((bp) => {
      const bName = bp.display_name.toLowerCase();
      return tmpl.aliases.some((a) => bName.includes(a));
    });

    if (backendMatch) {
      const state = String(backendMatch.state || backendMatch.status || "DORMANT").toUpperCase();
      // Pathways remain dormant during Trigger (0) and Signal Flood (1); if not restricted (-1), respect backend status
      const isStageGated = activeStageIndex !== -1 ? activeStageIndex >= 2 : true;
      const active = isStageGated && (state === "ACTIVE" || state === "RESOLVED" || state === "SUPPORTING" || state === "CONFIRMED");
      const reason = backendMatch.activation_reason || backendMatch.explain?.why || tmpl.defaultReason;
      return { id: tmpl.id, name: backendMatch.display_name, icon: tmpl.icon, color: tmpl.color, active, reason };
    }

    return { id: tmpl.id, name: tmpl.name, icon: tmpl.icon, color: tmpl.color, active: false, reason: "Reasoning pathway is dormant; awaiting backend evidence correlation." };
  });
}

// ─── Event Stream Items ───────────────────────────────────────────────────────

export function buildEventStreamItems(
  simulationState?: SimulationState | null | Record<string, unknown>,
  mode: "AFTER" | "BEFORE" | "NOISE" = "AFTER",
  currentScenarioId?: string | null,
  activeStageIndex: number = -1
) {
  const stateObj = simulationState as Record<string, unknown> | null | undefined;
  const runMeta = stateObj?.run as { status?: string; stage_index?: number } | undefined;
  const isStopped = runMeta != null && runMeta.status === "STOPPED";
  const isReady = runMeta != null && runMeta.status === "READY";
  const isScenarioMismatch = Boolean(currentScenarioId && stateObj?.scenario_id && stateObj.scenario_id !== currentScenarioId);
  const hasNoRun = stateObj != null && "run" in stateObj && stateObj.run === null;
  const isRunningOrPaused = runMeta?.status === "RUNNING" || runMeta?.status === "PAUSED" || runMeta?.status === "COMPLETED";
  const isInactive = !stateObj || isStopped || isReady || isScenarioMismatch || hasNoRun || !isRunningOrPaused;

  // Signals only show at Stage 2 (Signal Flood, activeStageIndex >= 1) and never before
  if (isInactive || activeStageIndex < 1) return [];
  // Correlated events / noise separation only produced during/after Stage 3 (Correlation)
  if ((mode === "AFTER" || mode === "NOISE") && activeStageIndex < 2) return [];

  const rawEvents = (stateObj?.raw_events || stateObj?.rawEvents) as Record<string, unknown>[] | undefined;
  const stateEvents = stateObj?.events as Record<string, unknown>[] | undefined;
  const noiseEvents = (stateObj?.noise_events || stateObj?.noiseEvents) as Record<string, unknown>[] | undefined;

  let backendEvents: Record<string, unknown>[] = [];
  if (mode === "BEFORE") {
    backendEvents = rawEvents?.length ? rawEvents : (stateEvents || []);
  } else if (mode === "NOISE") {
    backendEvents = noiseEvents?.length ? noiseEvents : [];
  } else {
    backendEvents = stateEvents?.length ? stateEvents : (rawEvents || []);
  }

  if (!backendEvents?.length) return [];
  return backendEvents.map((event, idx) => {
    const type = String(event.badge || event.category || "LOG").toUpperCase() as EventStreamType;
    const safeType: EventStreamType = ["ALARM", "METRIC", "TICKET", "TRACE", "LOG", "CHANGE"].includes(type) ? type : "LOG";
    const native = String(event.source_native_entity || event.source_native_entity_name || event.entity_id || "");
    const canonical = String(event.canonical_entity || event.canonical_entity_id || event.entity_id || "");

    let classification = String(event.classification || "");
    let classificationLabel = String(event.classification_label || "");
    let deduplication = String(event.deduplication || "");
    let explanation = String(event.explanation_text || event.explanation || event.message || "");
    let observation = String(event.observation || event.explanation_text || event.explanation || event.message || "");
    let impactScope = String(event.impact_scope || event.classification_label || "");

    if (mode === "BEFORE") {
      classification = "EVENT_FLOOD";
      classificationLabel = "Unprocessed Telemetry";
      deduplication = "Uncollapsed Stream";
      if (!observation) observation = `Signal recorded on ${native || "device"}. Pre-correlation telemetry stream.`;
      if (!explanation) explanation = observation;
    } else if (mode === "NOISE") {
      classification = classification || "COINCIDENTAL_NOISE";
      classificationLabel = classificationLabel || "Decoupled Background Noise";
      deduplication = deduplication || "Isolated from Anomaly Envelope";
      if (!impactScope) impactScope = "Background Noise";
    } else {
      if (!classification || classification === "RAW_UNPROCESSED" || classification === "ROOT_CAUSE_CANDIDATE") {
        classification = "CORRELATED_ANOMALY";
      }
      if (!deduplication || deduplication === "RAW") {
        deduplication = "Canonical Resolved (3GPP R17)";
      }
      if (!impactScope) {
        impactScope = classification === "HEALTHY_NEGATIVE" ? "Nominal Compute Baseline" : "Correlated Impact";
      }
      classificationLabel = impactScope;
    }

    const signalTitle = String(event.alarm_name || event.metric_name || event.kpi_name || event.signal || event.title || event.display_name || "Telemetry");

    return {
      id: String(event.event_id || event.id || `event-${idx}`),
      time: String(event.time || ""),
      type: safeType,
      title: signalTitle,
      subtitle: mode === "BEFORE"
        ? `Source: ${String(event.source_system || "IP_NMS")} · Native Port: ${native}`
        : String(event.domain || event.entity_id || event.state || ""),
      icon: eventIconForType(safeType),
      color: safeType === "ALARM" ? "#f43f5e" : safeType === "METRIC" ? "#38bdf8" : safeType === "TICKET" ? "#fbbf24" : safeType === "TRACE" ? "#c084fc" : safeType === "CHANGE" ? "#34d399" : "#60a5fa",
      explanation,
      observation,
      impactScope,
      classification,
      classificationLabel,
      deduplication,
      sourceNativeEntity: native,
      canonicalEntity: canonical,
      sourceSystem: String(event.source_system || "NMS"),
      severity: String(event.severity || "INFO"),
      separationRationale: event.separation_rationale ? String(event.separation_rationale) : undefined,
      correlationScore: typeof event.correlation_score === "number" ? (event.correlation_score as number) : undefined,
      rawData: (event.raw_data || event) as Record<string, unknown>,
    };
  });
}

// ─── Hypothesis Status Mapping ────────────────────────────────────────────────

function statusToHypothesisStatus(status?: string, confidence?: number | null, index?: number): HypothesisItem["status"] {
  const normalized = (status || "").toUpperCase();
  if (normalized === "REJECTED" || normalized === "DISPROVED") return "REJECTED";
  if (
    normalized === "CONFIRMED" || normalized === "ROOT_CANDIDATE" || normalized === "SUPPORTED" ||
    normalized === "TESTING" || normalized === "NEEDS_MORE_EVIDENCE" || normalized === "ACTIVE" ||
    (index === 0 && typeof confidence === "number" && confidence >= 50)
  ) return "LEADING";
  if (normalized === "CANDIDATE" || normalized === "UNRANKED") return "CANDIDATE";
  return "COMPETING";
}

// ─── Hypothesis Items ─────────────────────────────────────────────────────────

export function buildHypothesisItems(
  simulationState?: SimulationState | null | Record<string, unknown>,
  currentScenarioId?: string | null
): HypothesisItem[] {
  const stateObj = simulationState as Record<string, unknown> | null | undefined;
  const isStopped = stateObj?.run != null && (stateObj.run as { status?: string }).status === "STOPPED";
  const isReady = stateObj?.run != null && (stateObj.run as { status?: string }).status === "READY";
  const isScenarioMismatch = Boolean(currentScenarioId && stateObj?.scenario_id && stateObj.scenario_id !== currentScenarioId);
  const hasNoRun = stateObj != null && "run" in stateObj && stateObj.run === null;
  const isInactive = !stateObj || isStopped || isReady || isScenarioMismatch || hasNoRun;

  const reasoningMap = stateObj?.reasoningMap as Record<string, unknown> | null | undefined;
  const mapHypotheses = reasoningMap?.hypotheses as Record<string, unknown>[] | undefined;
  const stateHypotheses = stateObj?.hypotheses as Record<string, unknown>[] | undefined;

  const backendHypotheses: Record<string, unknown>[] = !isInactive
    ? mapHypotheses?.length ? mapHypotheses : stateHypotheses || []
    : [];

  if (!backendHypotheses?.length) {
    return [0, 1, 2, 3].map((idx) => ({
      id: `HYP-00${idx + 1}`,
      code: `Rank #${idx + 1}`,
      name: `Awaiting Twin Analysis Candidate #${idx + 1}`,
      confidence: null,
      delta: "Unranked",
      deltaIsPos: true,
      status: "CANDIDATE" as const,
      color: HYPOTHESIS_COLORS[idx] || "#60a5fa",
      progressColor: HYPOTHESIS_PROGRESS[idx] || "bg-blue-400",
    }));
  }

  const mapped = backendHypotheses.slice(0, 4).map((hyp, idx) => {
    const confidence = typeof hyp.confidence === "number" ? hyp.confidence : null;
    const displayId = String(hyp.display_id || `Rank #${idx + 1}`);
    const status = statusToHypothesisStatus(String(hyp.state || hyp.status || ""), confidence, idx);
    const delta = String(hyp.delta || hyp.last_delta || (confidence === null ? "Unranked" : ""));
    const hypName = String(hyp.display_name || hyp.label || `Candidate Hypothesis ${idx + 1}`);

    return {
      id: String(hyp.hypothesis_id || hyp.id || displayId),
      code: displayId,
      name: hypName,
      confidence,
      delta: delta || "Backend scored",
      deltaIsPos: !delta.trim().startsWith("-"),
      status,
      color: HYPOTHESIS_COLORS[idx] || "#60a5fa",
      progressColor: HYPOTHESIS_PROGRESS[idx] || "bg-blue-400",
    };
  });

  while (mapped.length < 4) {
    const idx = mapped.length;
    mapped.push({
      id: `HYP-00${idx + 1}`,
      code: `Rank #${idx + 1}`,
      name: `Awaiting Twin Candidate #${idx + 1}`,
      confidence: null,
      delta: "Unranked",
      deltaIsPos: true,
      status: "CANDIDATE" as const,
      color: HYPOTHESIS_COLORS[idx] || "#60a5fa",
      progressColor: HYPOTHESIS_PROGRESS[idx] || "bg-blue-400",
    });
  }
  return mapped;
}

// ─── Gap Items ────────────────────────────────────────────────────────────────

export function buildGapItems(simulationState?: SimulationState | null | Record<string, unknown>): GapItem[] {
  const stateObj = simulationState as Record<string, unknown> | null | undefined;
  const reasoningMap = stateObj?.reasoningMap as Record<string, unknown> | null | undefined;
  const mapGaps = reasoningMap?.knowledge_gaps as Record<string, unknown>[] | undefined;
  const stateGaps = stateObj?.knowledgeGaps as Record<string, unknown>[] | undefined;

  const backendGaps: Record<string, unknown>[] = mapGaps?.length ? mapGaps : stateGaps || [];
  if (!backendGaps?.length) return [];
  return backendGaps.map((gap) => {
    const status = String(gap.state || gap.status || "OPEN").toUpperCase();
    return {
      id: String(gap.gap_id || gap.id),
      title: String(gap.display_name || gap.label || "Knowledge gap"),
      subtitle: String(gap.required_evidence || gap.reason || "Additional evidence required"),
      severity: status === "NEEDS_EVIDENCE" || status === "OPEN" ? "High" : "Medium",
    };
  });
}

// ─── Next Best Evidence Items ─────────────────────────────────────────────────

export function buildNextBestEvidenceItems(
  simulationState?: SimulationState | null | Record<string, unknown>,
  scenarioId?: string | null,
  scenarioRegistry?: Array<{ id: string; display_name?: string; services?: string[]; domains?: string[] }>,
  profile?: ScenarioAttributionProfile
): NextBestEvidenceItem[] {
  const stateObj = simulationState as Record<string, unknown> | null | undefined;
  const reasoningMap = stateObj?.reasoningMap as Record<string, unknown> | null | undefined;
  const mapActions = (reasoningMap?.next_best_evidence || reasoningMap?.next_best_actions) as Record<string, unknown>[] | undefined;
  const stateActions = (stateObj?.nextBestActions || stateObj?.next_best_evidence || stateObj?.next_best_actions) as Record<string, unknown>[] | undefined;

  const backendActions: Record<string, unknown>[] = (mapActions && mapActions.length > 0)
    ? mapActions : (stateActions && stateActions.length > 0 ? stateActions : []);

  if (backendActions.length > 0) {
    return backendActions.map((nba) => {
      const rawStatus = String(nba.status || "").toUpperCase();
      const isCompleted = rawStatus === "COMPLETED";
      const isReady = rawStatus === "READY";
      const isRunning = rawStatus === "RUNNING";
      const status: NextBestEvidenceItem["status"] = isCompleted ? "Completed" : isReady ? "Ready" : isRunning ? "Running" : "Pending";
      return { id: String(nba.id || nba.request_id || "NBA-001"), label: String(nba.display_name || nba.label || "Evaluate next-best evidence"), status, isReady };
    });
  }

  const entry = scenarioRegistry?.find((s) => s.id === scenarioId);
  const targetEntity =
    (stateObj?.run as Record<string, unknown> | undefined)?.active_entity_id as string | undefined ||
    (stateObj?.reasoningFocus as Record<string, unknown> | undefined)?.entity as string | undefined ||
    (entry?.display_name ? entry.display_name.split(" - ")[0].split(" / ")[0] : (scenarioId || "Target Element"));
  const primaryService = entry?.services?.[0] || (profile?.services?.length ? profile.services[0].name : "Primary Service");
  const domainName = (entry?.domains?.[0]) || (profile?.primaryDomainName && profile.primaryDomainName !== "Attribution Pending" ? profile.primaryDomainName : "Network Core");

  const currentRun = stateObj?.run as Record<string, unknown> | undefined;
  const isRunningOrExecuted = Boolean(currentRun && (currentRun.status === "RUNNING" || currentRun.status === "PAUSED" || currentRun.status === "COMPLETED"));
  const stages = stateObj?.stages as Array<{ status?: string; index?: number }> | undefined;
  const currentStageIndex = typeof (currentRun as { stage_index?: number })?.stage_index === "number"
    ? (currentRun as { stage_index: number }).stage_index
    : (stages?.findIndex((s) => s.status === "ACTIVE" || s.status === "CURRENT") ?? 0);
  const isGapStage = isRunningOrExecuted && currentStageIndex >= 5;
  const isValidationStage = isRunningOrExecuted && currentStageIndex >= 6;
  const isActionStage = isRunningOrExecuted && currentStageIndex >= 7;
  const executedActions = ((currentRun as { executed_actions?: string[] })?.executed_actions || []) as string[];
  const nba1Completed = executedActions.includes("NBA-001");
  const hitlCompleted = executedActions.includes("HITL-001") || (stateObj?.reasoningMap as { validation?: { status?: string } })?.validation?.status === "ACCEPTED";
  const actCompleted = executedActions.includes("ACT-001") || executedActions.includes("REMEDIATE-001") || currentRun?.terminal_state === "RESOLVED";

  return [
    { id: "NBA-001", label: `Get ${targetEntity} detailed telemetry & health stats`, status: nba1Completed ? "Completed" : (isGapStage ? "Ready" : "Pending"), isReady: isGapStage && !nba1Completed },
    { id: "HITL-001", label: "HITL SME Validation & Knowledge Promotion", status: hitlCompleted ? "Completed" : (isValidationStage ? "Ready" : "Pending"), isReady: isValidationStage && !hitlCompleted },
    { id: "ACT-001", label: `Execute Remediation: Reroute traffic & isolate ${targetEntity}`, status: actCompleted ? "Completed" : (isActionStage ? "Ready" : "Pending"), isReady: isActionStage && !actCompleted },
    { id: "NBA-002", label: `Validate ${primaryService} end-to-end path status`, status: "Pending", isReady: false },
    { id: "NBA-003", label: `Assess change window for recent modifications`, status: "Pending", isReady: false },
    { id: "NBA-004", label: `Query historical incidents in ${domainName}`, status: "Pending", isReady: false },
  ];
}

// ─── Conduit Telemetry Resolver ───────────────────────────────────────────────

export function resolveConduitTelemetry(
  target: TraceTarget,
  hypothesesList: HypothesisItem[] = HYPOTHESES_LIST,
  simulationState?: {
    scenario_id?: string;
    run_id?: string;
    revision?: number;
    sequence?: number;
    updated_at?: string;
    reasoningMap?: {
      connections?: Array<{
        id?: string;
        connection_id?: string;
        source_id?: string;
        target_id?: string;
        relation_type?: string;
        state?: string;
        reason?: string;
        sequence?: number;
      }>;
      synthesis?: { summary?: string; state?: string };
      validation?: { status?: string; display_name?: string; explain?: { why?: string } };
    } | null;
  } | null,
  evidenceList: EvidenceItem[] = EVIDENCE_LIST,
  pathwaysList: PathwayItem[] = PATHWAYS_LIST
): DetailedConduitTelemetry | null {
  if (!target) return null;

  const runId = simulationState?.run_id || "RUN-LIVE";
  const scnId = simulationState?.scenario_id || "SCN-LIVE";
  const rev = simulationState?.revision ?? 1;
  const seq = simulationState?.sequence ?? 0;
  const timestamp = simulationState?.updated_at || new Date().toISOString();

  if (target.type === "conduit-ev-p") {
    const c = target.conduitIdx !== undefined && EVIDENCE_TO_PATHWAY_CONDUITS[target.conduitIdx]
      ? EVIDENCE_TO_PATHWAY_CONDUITS[target.conduitIdx]
      : EVIDENCE_TO_PATHWAY_CONDUITS.find((item) => item.fromIdx === target.from && item.toIdx === target.to) || EVIDENCE_TO_PATHWAY_CONDUITS[0];
    const ev = evidenceList[c.fromIdx] || evidenceList[0];
    const pw = pathwaysList[c.toIdx] || pathwaysList[0];
    const targetHypIdx = PATHWAYS_TO_HYPS[c.toIdx]?.[0] ?? 0;
    const hyp = hypothesesList[targetHypIdx] || hypothesesList[0];
    const backendConn = simulationState?.reasoningMap?.connections?.find(
      (conn) => (conn.relation_type === "CONTRIBUTES_TO" || conn.relation_type === "EMITS_EVIDENCE") &&
        (conn.source_id?.toLowerCase().includes(ev.id) || conn.target_id?.toLowerCase().includes(pw.id))
    );
    const reason = backendConn?.reason || c.reason;
    const state = backendConn?.state || (ev.count > 0 ? "TRANSMITTING TELEMETRY (Active)" : "DORMANT");
    return {
      source: `Evidence: ${ev.name} (${ev.countLabel})`,
      target: `Pathway: ${pw.name}`,
      currentState: state,
      whyActive: reason,
      backendReason: reason,
      evidence: `${ev.name} — ${ev.count} operational signals admitted for run ${runId}`,
      pathway: pw.name,
      hypothesisAffected: `${hyp.code}: ${hyp.name} (${hyp.confidence === null ? "Unranked" : `${hyp.confidence}% confidence`})`,
      supportType: c.fromIdx === 4 ? "NEUTRAL" : "SUPPORTS",
      confidenceDelta: hyp.confidence === null ? "Unranked" : `${hyp.delta} on ${hyp.code}`,
      provenance: {
        stream: `telecom.telemetry.${scnId}.events`,
        sourceAgent: "FikraCore Telemetry Ingestion Worker",
        ingestId: backendConn?.id || `ingest-ev${c.fromIdx}-pw${c.toIdx}`,
        timestamp,
        hash: `rev:${rev}#seq:${backendConn?.sequence ?? seq}`,
      },
    };
  }

  if (target.type === "conduit-p-core") {
    const pw = pathwaysList[target.pathwayIdx] || pathwaysList[0];
    const targetHypIdx = PATHWAYS_TO_HYPS[target.pathwayIdx]?.[0] ?? 0;
    const hyp = hypothesesList[targetHypIdx] || hypothesesList[0];
    const backendReason = pw.reason || "Analytical pathway contributing to intelligence synthesis.";
    return {
      source: `Pathway: ${pw.name}`,
      target: `Reasoning Core (Intake Socket #${target.pathwayIdx + 1})`,
      currentState: pw.active ? "SYNTHESIZING (Multi-Domain Convergence)" : "DORMANT",
      whyActive: backendReason,
      backendReason,
      evidence: `Admitted signal cluster from ${pw.name}`,
      pathway: pw.name,
      hypothesisAffected: `${hyp.code}: ${hyp.name} (${hyp.confidence === null ? "Unranked" : `${hyp.confidence}% confidence`})`,
      supportType: "SUPPORTS",
      confidenceDelta: hyp.confidence === null ? "Unranked" : `${hyp.delta} confidence convergence`,
      provenance: {
        stream: `fikracore.reasoning.${scnId}.pathways`,
        sourceAgent: "FikraCore Synthesis Engine",
        ingestId: `synth-p${target.pathwayIdx}-core`,
        timestamp,
        hash: `rev:${rev}#seq:${seq}`,
      },
    };
  }

  if (target.type === "conduit-core-hyp") {
    const hyp = hypothesesList[target.hypIdx] || hypothesesList[0];
    const synthSummary = simulationState?.reasoningMap?.synthesis?.summary || "Bayesian belief evaluation across active pathways.";
    return {
      source: `Reasoning Core (Output Socket #${target.hypIdx + 1})`,
      target: `Hypothesis: ${hyp.code} - ${hyp.name}`,
      currentState: hyp.status === "LEADING" ? "DOMINANT CANDIDATE (Rank 1)" : (hyp.status === "CANDIDATE" ? "CANDIDATE (Unranked)" : "EVALUATED (Alternative)"),
      whyActive: hyp.confidence === null ? `Reasoning core has not ranked ${hyp.code} yet.` : `Reasoning core posterior probability evaluation scored ${hyp.code} at ${hyp.confidence}%.`,
      backendReason: synthSummary,
      evidence: `Multi-modal telemetry convergence for ${hyp.code}: ${hyp.name}`,
      pathway: "Multi-Domain Causal Convergence",
      hypothesisAffected: `${hyp.code}: ${hyp.name} (${hyp.confidence === null ? "Unranked" : `${hyp.confidence}% confidence`})`,
      supportType: hyp.deltaIsPos ? "SUPPORTS" : "CONTRADICTS",
      confidenceDelta: hyp.confidence === null ? "Unranked" : `${hyp.delta} (${hyp.confidence}% current confidence)`,
      provenance: {
        stream: `fikracore.hypothesis.${scnId}.ranking`,
        sourceAgent: "Bayesian Hypothesis Arbiter",
        ingestId: `hyp-eval-${hyp.id}`,
        timestamp,
        hash: `rev:${rev}#seq:${seq}`,
      },
    };
  }

  if (target.type === "conduit-hyp-val") {
    const c = HYP_TO_VALIDATION_CONDUITS[target.conduitIdx] || HYP_TO_VALIDATION_CONDUITS[0];
    const hyp = hypothesesList[c.fromIdx] || hypothesesList[0];
    const valState = simulationState?.reasoningMap?.validation;
    const valStatus = valState?.status || "PENDING";
    const valFact = valState?.display_name || "Domain engineer validation required before promotion.";
    return {
      source: `Hypothesis: ${hyp.code} - ${hyp.name}`,
      target: c.targetY === 68 ? "Root Cause Card (Confirmed RC)" : c.targetY < 200 ? "Operational Domain Attribution" : "Affected Services Validation",
      currentState: `OPERATIONAL VALIDATION (${valStatus})`,
      whyActive: valState?.explain?.why || "Downstream operational verification mapping hypothesis to physical network infrastructure and impacted customer services.",
      backendReason: valFact,
      evidence: `${hyp.code} causality assessed by backend validation engine`,
      pathway: "Operational Verification & Remediation Mapping",
      hypothesisAffected: `${hyp.code}: ${hyp.name}`,
      supportType: "SUPPORTS",
      confidenceDelta: hyp.confidence === null ? "Unranked" : `${hyp.delta} post-validation weight`,
      provenance: {
        stream: `fikracore.validation.${scnId}.impact`,
        sourceAgent: "Network Impact & Validation Engine",
        ingestId: `val-h${c.fromIdx}-t${c.targetY}`,
        timestamp,
        hash: `rev:${rev}#seq:${seq}`,
      },
    };
  }

  return null;
}

// ─── Entity Modal Resolver ────────────────────────────────────────────────────

export function resolveEntityModal(
  target: TraceTarget,
  scenarioId: string | null | undefined,
  profile: ScenarioAttributionProfile,
  hypothesesList: HypothesisItem[] = HYPOTHESES_LIST,
  simulationState?: {
    reasoningMap?: {
      validation?: { status?: string; state?: string; display_name?: string; reviewer_role?: string; explain?: { why?: string } };
    } | null;
  } | null,
  evidenceList: EvidenceItem[] = EVIDENCE_LIST,
  pathwaysList: PathwayItem[] = PATHWAYS_LIST
): DetailedEntityModal | null {
  if (!target) return null;

  if (target.type === "evidence") {
    const ev = evidenceList[target.idx] || evidenceList[0];
    return {
      category: "Evidence Signal",
      title: ev.name,
      subtitle: `${ev.countLabel} — Admitted Telemetry Observation`,
      canonicalId: `EVIDENCE-${ev.id}`,
      status: ev.count > 0 ? "ADMITTED & ACTIVE" : "DORMANT",
      statusColor: ev.count > 0 ? "text-emerald-400" : "text-slate-500",
      color: ev.color,
      description: `${ev.name} telemetry observations admitted into FikraCore reasoning to evaluate baseline anomalies and structural failure propagation.`,
      metrics: [
        { label: "Admitted Signals", value: `${ev.count} observations` },
        { label: "Correlation Weight", value: ev.count > 0 ? "0.94" : "0.00" },
        { label: "Primary Domain", value: profile.primaryDomainName },
        { label: "Evaluation State", value: ev.count > 0 ? "Admitted & Correlated" : "Monitoring" },
      ],
      technicalDetails: {
        canonicalId: `EVIDENCE-${ev.id}`,
        internalDomain: profile.primaryDomainName,
        subsystem: `${profile.primaryDomainName} Ingestion`,
        telecomStandard: "3GPP Telecom Telemetry Framework",
        telemetrySource: `FikraCore Simulation Engine (${scenarioId || "SCN-001"})`,
      },
      causalFlow: {
        upstream: ["Operational Telemetry Ingestion", `${ev.name} Collector`],
        downstream: EVIDENCE_TO_PATHWAY_CONDUITS.filter((c) => c.fromIdx === target.idx).map((c) => pathwaysList[c.toIdx]?.name).filter(Boolean),
      },
    };
  }

  if (target.type === "pathway") {
    const pw = pathwaysList[target.idx] || pathwaysList[0];
    const incomingFeedsCount = EVIDENCE_TO_PATHWAY_CONDUITS.filter((c) => c.toIdx === target.idx).length;
    return {
      category: "Reasoning Pathway",
      title: pw.name,
      subtitle: pw.active ? "Active Pathway — Correlating Operational Telemetry" : "Dormant Pathway — Monitoring Network Signals",
      canonicalId: `PATHWAY-${pw.id}`,
      status: pw.active ? "ACTIVE CORRELATION" : "DORMANT",
      statusColor: pw.active ? "text-cyan-400" : "text-slate-500",
      color: pw.color,
      description: pw.reason || "Evaluates admitted operational telemetry to determine candidate causal propagation across topology.",
      metrics: [
        { label: "Active Evidence Feeds", value: `${incomingFeedsCount} incoming feeds` },
        { label: "Correlation Weight", value: pw.active ? "0.89" : "0.00" },
        { label: "Primary Domain", value: profile.primaryDomainName },
        { label: "Status", value: pw.active ? "Active Correlation" : "Monitoring (Dormant)" },
      ],
      technicalDetails: {
        canonicalId: `PATHWAY-${pw.id}`,
        internalDomain: `${profile.primaryDomainName} Architecture`,
        subsystem: "FikraCore Reasoning Engine",
        telecomStandard: "3GPP Operational Correlation Standard",
        telemetrySource: `FikraCore Simulation Engine (${scenarioId || "SCN-001"})`,
      },
      causalFlow: {
        upstream: EVIDENCE_TO_PATHWAY_CONDUITS.filter((c) => c.toIdx === target.idx).map((c) => evidenceList[c.fromIdx]?.name).filter(Boolean),
        downstream: ["Reasoning Core Central Synthesis", ...(PATHWAYS_TO_HYPS[target.idx] || []).map((h) => hypothesesList[h]?.name).filter(Boolean)],
      },
    };
  }

  if (target.type === "hypothesis") {
    const hyp = hypothesesList[target.idx] || hypothesesList[0];
    return {
      category: "Evaluated Hypothesis",
      title: `${hyp.code}: ${hyp.name}`,
      subtitle: hyp.status === "LEADING" ? "Leading Candidate Root Cause (#1)" : "Alternative Competing Hypothesis",
      canonicalId: `HYPOTHESIS-${hyp.id}`,
      status: hyp.status === "LEADING" ? "CONFIRMED LEADING" : "COMPETING ALTERNATIVE",
      statusColor: hyp.status === "LEADING" ? "text-emerald-400" : "text-sky-400",
      color: hyp.color,
      description: `${hyp.name} is evaluated against admitted operational telemetry across transport and core links.`,
      metrics: [
        { label: "Posterior Confidence", value: hyp.confidence === null ? "Unranked" : `${hyp.confidence}%` },
        { label: "Confidence Trend", value: hyp.delta },
        { label: "Evaluated Rank", value: target.idx === 0 ? "#1 (Leading Root Cause)" : `#${target.idx + 1}` },
        { label: "Primary Domain", value: profile.primaryDomainName },
      ],
      technicalDetails: {
        canonicalId: `HYPOTHESIS-${hyp.id}`,
        internalDomain: profile.primaryDomainName,
        subsystem: "Hypothesis Validation Arbiter",
        telecomStandard: "3GPP Telecom Root Cause Standard",
        telemetrySource: `FikraCore Diagnostic Inference Engine (${scenarioId || "SCN-001"})`,
      },
      causalFlow: {
        upstream: ["Reasoning Core Central Synthesis", ...(HYP_TO_PATHWAYS[target.idx] || []).map((p) => pathwaysList[p]?.name).filter(Boolean)],
        downstream: ["Root Cause Validation Card", `${profile.primaryDomainName} Attribution`, "Service Impact Analysis"],
      },
    };
  }

  if (target.type === "root-cause") {
    const valState = simulationState?.reasoningMap?.validation;
    const isConfirmed = valState?.status === "ACCEPTED" || valState?.state === "ACCEPTED";
    const leadHyp = hypothesesList[0];
    const rootTitle = isConfirmed
      ? (valState?.display_name || `${leadHyp?.name || "Incident Root Cause"} Confirmed`)
      : (leadHyp?.name ? `${leadHyp.name} (Leading Candidate)` : "Awaiting Root Cause Confirmation");
    return {
      category: "Root Cause Attribution",
      title: rootTitle,
      subtitle: `${profile.primaryDomainName} — ${profile.primaryAttribution}% primary attribution weight`,
      canonicalId: `ROOT-CAUSE-${leadHyp?.id || "PRIMARY"}`,
      status: isConfirmed ? "CONFIRMED & VALIDATED" : "VALIDATION PENDING",
      statusColor: isConfirmed ? "text-emerald-400" : "text-amber-400",
      color: isConfirmed ? "#10b981" : "#fbbf24",
      description: valState?.explain?.why || profile.primarySummary || "Causal root cause identified and subject to domain engineering review.",
      metrics: [
        { label: "Attribution Weight", value: `${profile.primaryAttribution}%` },
        { label: "Primary Domain", value: profile.primaryDomainName },
        { label: "Validation Status", value: isConfirmed ? "CONFIRMED & VALIDATED" : "VALIDATION PENDING" },
        { label: "Reviewer Role", value: valState?.reviewer_role || "Domain SME / Engineer" },
      ],
      technicalDetails: {
        canonicalId: `ROOT-CAUSE-${leadHyp?.id || "PRIMARY"}`,
        internalDomain: profile.primaryDomainName,
        subsystem: `${profile.primaryDomainName} Diagnostic Inference Engine`,
        telecomStandard: "3GPP Fault & Root Cause Governance",
        telemetrySource: `Authoritative Multi-Domain Synthesis (${scenarioId || "SCN-001"})`,
      },
      causalFlow: {
        upstream: [`Hypothesis ${leadHyp?.code || "H1"} (${leadHyp?.name || "Candidate"})`],
        downstream: [`${profile.primaryDomainName} Remediation`, "Customer Service Impact"],
      },
    };
  }

  if (target.type === "domain") {
    const d = OPERATIONAL_DOMAINS_CATALOG.find((item) => item.id === target.id) || OPERATIONAL_DOMAINS_CATALOG[0];
    const info = profile.domainClassifications[d.id];
    const cls = info?.classification || "MONITOR ONLY";
    const weight = info?.weight ?? profile.domainWeights[d.id] ?? 0;
    return {
      category: "Operational Telecom Domain",
      title: d.name,
      subtitle: `${cls} Domain — ${d.category} Infrastructure`,
      canonicalId: `DOMAIN-${d.id}`,
      status: cls,
      statusColor: cls === "PRIMARY" ? "text-rose-400" : cls === "CONTRIBUTING" ? "text-purple-300" : "text-amber-300",
      color: d.color,
      description: info?.detail || d.subtext,
      metrics: [
        { label: "Attribution Score", value: `${weight}%` },
        { label: "Classification", value: cls },
        { label: "Functional Scope", value: d.subtext },
        { label: "Telemetry Health", value: cls === "MONITOR ONLY" ? "Nominal (0 active alerts)" : "Active Signal Correlation" },
      ],
      technicalDetails: {
        canonicalId: `DOMAIN-${d.id}`,
        internalDomain: d.name,
        subsystem: d.category,
        telecomStandard: "3GPP / ETSI Telecommunication Domain Architecture",
        telemetrySource: "NMS & Domain Telemetry Aggregator",
      },
      causalFlow: {
        upstream: [`Hypothesis ${hypothesesList[0]?.code || "H1"} (${hypothesesList[0]?.name || "Leading Candidate"})`],
        downstream: ["Affected Services Plane", "Cross-Domain Incident Remediation"],
      },
    };
  }

  if (target.type === "service") {
    const s = profile.services[target.idx] || profile.services[0];
    return {
      category: "Affected Telecom Service",
      title: s.name,
      subtitle: `${s.status} Degradation — Customer Service Impact`,
      canonicalId: `SERVICE-${s.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
      status: s.status,
      statusColor: s.status === "Severe" ? "text-rose-400" : "text-amber-400",
      color: s.status === "Severe" ? "#f43f5e" : "#fbbf24",
      description: `Service SLA degraded due to active incident in ${profile.primaryDomainName}. User plane traffic impacted.`,
      metrics: [
        { label: "Degradation Severity", value: s.status },
        { label: "Active SLA Impact", value: s.status === "Severe" ? "Critical Impact" : "Degraded Performance" },
        { label: "Root Domain", value: profile.primaryDomainName },
        { label: "Resolution Status", value: "Remediation pending evidence verification" },
      ],
      technicalDetails: {
        canonicalId: `SERVICE-${s.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
        internalDomain: "User Plane Services",
        subsystem: "Customer Edge Delivery",
        telecomStandard: "3GPP User Plane & Service Management",
        telemetrySource: "BSS/OSS SLA Telemetry Probe",
      },
      causalFlow: {
        upstream: [profile.primaryDomainName, hypothesesList[0]?.name || "Leading Hypothesis"],
        downstream: ["Customer Service Assurance Ticketing", "Customer Impact Dashboard"],
      },
    };
  }

  return null;
}

// ─── Import React for component type refs ────────────────────────────────────
import React from "react";

export function renderStyledMessage(text: string, isLight: boolean = false): React.ReactNode {
  if (!text) return null;

  const isNerToken = (str: string): boolean => {
    const trimmed = str.trim();
    return (
      /^(?:IP:[A-Z0-9:]+|UPF-\d+|GNB-[A-Z0-9-]+|IMS-[A-Z0-9-]+|PE-RTR-\d+|RTR-\d+|INFRA:[A-Z0-9:-]+|CORE-K8S-[A-Z0-9-]+|CORE-KUBERNETES-[A-Z0-9-]+|EVT-[A-Z0-9-]+|SCN-\d+|[A-Z][A-Z0-9]+-(?:[A-Z0-9]+-?)+)$/i.test(trimmed) ||
      /^(?:INFRA K8S Core-A|User Plane Function-\d+|Customer Ticket-\d+|CORE-KUBERNETES-CLUSTER-A|RTR-\d+)$/i.test(trimmed)
    );
  };

  return (
    <div className="space-y-1.5 whitespace-pre-wrap font-sans">
      {text.split("\n\n").map((para, pIdx) => {
        const parts = para.split(
          /(\*\*[^*]+\*\*|`[^`]+`|\bH\d+(?:-WI-\d+)?\b|\b(?:GAP|TKT|VAL|SYNTHESIS|ACT)-\d+\b|\b(?:IP:[A-Z0-9:]+|UPF-\d+|GNB-[A-Z0-9-]+|IMS-[A-Z0-9-]+|PE-RTR-\d+|RTR-\d+|INFRA:[A-Z0-9:-]+|CORE-K8S-[A-Z0-9-]+|CORE-KUBERNETES-[A-Z0-9-]+|EVT-[A-Z0-9-]+|SCN-\d+|[A-Z][A-Z0-9]+-(?:[A-Z0-9]+-?)+)\b|──►|→|[-+]?\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b(?:\s*(?:subscribers|users|sessions|calls))?|\b(?:PAUSED|MAJOR|CRITICAL|ACTIVE|NOMINAL|DIVERGENT|CAUTION)\b)/g
        );

        return (
          <p
            key={pIdx}
            className={
              isLight
                ? "font-medium text-slate-800 leading-relaxed text-xs"
                : "font-medium text-slate-200 leading-relaxed text-xs"
            }
          >
            {parts.map((part, idx) => {
              if (!part) return null;

              if (part === "──►" || part === "→") {
                return (
                  <span key={idx} className="text-cyan-400 font-bold px-1 select-none">
                    {part}
                  </span>
                );
              }

              if (part.startsWith("**") && part.endsWith("**")) {
                const inner = part.slice(2, -2).trim();
                const isFieldLabel =
                  /^(?:Incident ID|Status|Severity|Impact|Service|Component|Leading hypothesis|Correlation|Causal chain|Supporting evidence|Remediation|Still open|Mitigation strategy|Mandatory Prechecks|Domains|Blast radius):?$/i.test(
                    inner
                  ) || inner.endsWith(":");

                if (isFieldLabel) {
                  return (
                    <span
                      key={idx}
                      className={
                        isLight
                          ? "font-medium text-slate-500 mr-1 select-none"
                          : "font-medium text-slate-400 mr-1 select-none"
                      }
                    >
                      {inner}
                    </span>
                  );
                }

                if (isNerToken(inner)) {
                  return (
                    <span
                      key={idx}
                      className="[font-family:Consolas,Monaco,'Courier_New',monospace] text-[11px] font-semibold text-fuchsia-400 tracking-tight"
                    >
                      {inner}
                    </span>
                  );
                }

                if (
                  /[-+]?\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b(?:\s*(?:subscribers|users|sessions|calls))?|\b(?:PAUSED|MAJOR|CRITICAL|ACTIVE|NOMINAL|DIVERGENT|CAUTION)\b/i.test(
                    inner
                  )
                ) {
                  return (
                    <strong key={idx} className="font-mono font-bold text-cyan-400">
                      {inner}
                    </strong>
                  );
                }

                const isDomain = /transport|core|ran|ims|database|security|cloud|optical|router/i.test(inner);
                if (isDomain) {
                  return (
                    <strong
                      key={idx}
                      className={isLight ? "text-cyan-700 font-semibold" : "text-cyan-300 font-semibold"}
                    >
                      {inner}
                    </strong>
                  );
                }

                return (
                  <strong
                    key={idx}
                    className={isLight ? "text-slate-900 font-semibold" : "text-slate-100 font-semibold"}
                  >
                    {inner}
                  </strong>
                );
              }

              if (part.startsWith("`") && part.endsWith("`")) {
                const codeInner = part.slice(1, -1).trim();
                if (
                  isNerToken(codeInner) ||
                  /^[A-Z0-9]+(?:-[A-Z0-9]+)+$/i.test(codeInner) ||
                  /^SCN-\d+$/i.test(codeInner)
                ) {
                  return (
                    <code
                      key={idx}
                      className="[font-family:Consolas,Monaco,'Courier_New',monospace] text-[11px] font-semibold text-fuchsia-400 tracking-tight"
                    >
                      {codeInner}
                    </code>
                  );
                }
                if (
                  /^(?:PAUSED|MAJOR|CRITICAL|ACTIVE|NOMINAL|DIVERGENT|CAUTION|\d+(?:\.\d+)?%?)$/i.test(
                    codeInner
                  )
                ) {
                  return (
                    <code
                      key={idx}
                      className="inline-flex items-center px-1.5 py-0.5 rounded font-mono text-[11px] font-bold text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 tracking-tight shadow-sm"
                    >
                      {codeInner}
                    </code>
                  );
                }
                return (
                  <code
                    key={idx}
                    className="inline-flex items-center px-1.5 py-0.5 rounded [font-family:Consolas,Monaco,'Courier_New',monospace] text-[11px] text-slate-300 bg-white/5 border border-white/10"
                  >
                    {codeInner}
                  </code>
                );
              }

              if (
                /^H\d+(?:-WI-\d+)?$/i.test(part) ||
                /^(?:GAP|TKT|VAL|SYNTHESIS|ACT)-\d+$/i.test(part)
              ) {
                return (
                  <span
                    key={idx}
                    className="[font-family:Consolas,Monaco,'Courier_New',monospace] text-[11px] font-semibold text-fuchsia-400 tracking-tight"
                  >
                    {part}
                  </span>
                );
              }

              if (isNerToken(part)) {
                return (
                  <span
                    key={idx}
                    className="[font-family:Consolas,Monaco,'Courier_New',monospace] text-[11px] font-semibold text-fuchsia-400 tracking-tight"
                  >
                    {part}
                  </span>
                );
              }

              if (
                /[-+]?\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b(?:\s*(?:subscribers|users|sessions|calls))?|\b(?:PAUSED|MAJOR|CRITICAL|ACTIVE|NOMINAL|DIVERGENT|CAUTION)\b/i.test(
                  part
                )
              ) {
                return (
                  <span key={idx} className="font-mono font-bold text-cyan-400">
                    {part}
                  </span>
                );
              }

              return <span key={idx}>{part}</span>;
            })}
          </p>
        );
      })}
    </div>
  );
}
