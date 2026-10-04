/**
 * Shared type definitions for the Investigate workspace.
 * Extracted from page.tsx to keep the lib layer pure and testable.
 */

import type React from "react";
import type { StorytellerPayload } from "@/lib/api/qna";
import type {
  ZakiResponseV2,
  ZakiSelectedContext as StoreZakiSelectedContext,
} from "@/lib/simulation-store";

// ─── Evidence ────────────────────────────────────────────────────────────────

export interface EvidenceItem {
  id: string;
  name: string;
  countLabel: string;
  count: number;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color: string;
  bgGlow: string;
  borderColor: string;
}

// ─── Reasoning Pathways ───────────────────────────────────────────────────────

export interface PathwayItem {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color: string;
  active: boolean;
  reason: string;
}

// ─── Hypotheses ───────────────────────────────────────────────────────────────

export interface HypothesisItem {
  id: string;
  code: string;
  name: string;
  confidence: number | null;
  delta: string;
  deltaIsPos: boolean;
  status: "LEADING" | "COMPETING" | "REJECTED" | "CANDIDATE";
  color: string;
  progressColor: string;
}

// ─── Knowledge Gaps ───────────────────────────────────────────────────────────

export interface GapItem {
  id: string;
  title: string;
  subtitle: string;
  severity: "High" | "Medium";
}

// ─── Next Best Evidence ───────────────────────────────────────────────────────

export interface NextBestEvidenceItem {
  id: string;
  label: string;
  status: "Ready" | "Running" | "Pending" | "Completed";
  isReady: boolean;
}

// ─── Conduits ─────────────────────────────────────────────────────────────────

export interface Conduit {
  fromIdx: number; // 0..6 (evidence index)
  toIdx: number;   // 0..8 (pathway index)
  color: string;
  reason: string;
}

export interface HypValidationConduit {
  fromIdx: number; // 0..3 (H1..H4)
  targetY: number;
  color: string;
  strokeWidth: number;
  pulse?: boolean;
}

// ─── Event Stream ─────────────────────────────────────────────────────────────

export interface EventStreamItem {
  id: string;
  time: string;
  type: "ALARM" | "METRIC" | "TICKET" | "TRACE" | "LOG" | "CHANGE";
  title: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color: string;
  explanation?: string;
  observation?: string;
  impactScope?: string;
  classification?: string;
  classificationLabel?: string;
  deduplication?: string;
  sourceNativeEntity?: string;
  canonicalEntity?: string;
  sourceSystem?: string;
  severity?: string;
  separationRationale?: string;
  correlationScore?: number;
  rawData?: Record<string, unknown>;
}

// ─── Domain Attribution ───────────────────────────────────────────────────────

export type DomainClassification =
  | "PRIMARY"
  | "CONTRIBUTING"
  | "AFFECTED"
  | "INVOLVED"
  | "MONITOR ONLY"
  | "NOT RELEVANT";

export interface OperationalDomainDef {
  id: string;
  name: string;
  shortName: string;
  category: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color: string;
  subtext: string;
}

export interface DomainAttributionInfo {
  classification: DomainClassification;
  weight: number; // 0..100
  detail: string;
  attributionBasis?: string;
  supportingHypothesisIds?: string[];
  sourceRevision?: number;
}

export interface ScenarioAttributionProfile {
  primaryDomainId: string;
  primaryDomainName: string;
  primaryAttribution: number;
  primarySummary: string;
  domainWeights: Record<string, number>;
  domainClassifications: Record<string, DomainAttributionInfo>;
  services: {
    name: string;
    status: "Severe" | "Degraded" | "Nominal";
    drop: string;
    icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  }[];
  attributionStatus?: "CONSISTENT" | "PARTIAL" | "UNRESOLVED" | "CONFLICT";
  conflictReasons?: string[];
  revision?: number;
  sequence?: number;
}

// ─── Causal Trace Target ──────────────────────────────────────────────────────

export type TraceTarget =
  | { type: "evidence"; idx: number }
  | { type: "pathway"; idx: number }
  | { type: "core" }
  | { type: "hypothesis"; idx: number }
  | { type: "root-cause" }
  | { type: "domain"; id: string }
  | { type: "service"; id: string; idx: number }
  | { type: "conduit-ev-p"; from: number; to: number; conduitIdx?: number }
  | { type: "conduit-p-core"; pathwayIdx: number }
  | { type: "conduit-core-hyp"; hypIdx: number }
  | { type: "conduit-hyp-val"; conduitIdx: number }
  | null;

// ─── Conduit Telemetry Modal Data ─────────────────────────────────────────────

export interface DetailedConduitTelemetry {
  source: string;
  target: string;
  currentState: string;
  whyActive: string;
  backendReason: string;
  evidence: string;
  pathway: string;
  hypothesisAffected: string;
  supportType: "SUPPORTS" | "CONTRADICTS" | "NEUTRAL";
  confidenceDelta: string;
  provenance: {
    stream: string;
    sourceAgent: string;
    ingestId: string;
    timestamp: string;
    hash: string;
  };
}

export interface DetailedEntityModal {
  category: string;
  title: string;
  subtitle: string;
  canonicalId: string;
  status: string;
  statusColor?: string;
  color?: string;
  description: string;
  metrics: { label: string; value: string }[];
  technicalDetails: {
    canonicalId: string;
    internalDomain: string;
    subsystem: string;
    telecomStandard?: string;
    telemetrySource?: string;
  };
  causalFlow: {
    upstream: string[];
    downstream: string[];
  };
}

// ─── Zaki types ───────────────────────────────────────────────────────────────

export type ZakiCopilotResponse = ZakiResponseV2 & {
  storyteller?: StorytellerPayload | null;
  spoken_answer?: string;
  spoken_response?: string;
  spoken_message?: string;
  spoken_reply?: string;
};

export type ZakiApiSection = ZakiResponseV2["sections"][number];
export type ZakiApiSuggestedAction = NonNullable<ZakiResponseV2["suggested_actions"]>[number];

export interface ZakiChatApiResponse {
  answer?: string;
  sections?: ZakiApiSection[];
  highlighted_entities?: import("@/lib/simulation-store").HighlightedEntity[];
  selected_context?: StoreZakiSelectedContext;
  copilot_state?: string;
  grounded_in?: Record<string, unknown>;
  uncertainty?: string[];
  suggested_actions?: ZakiApiSuggestedAction[];
  response?: {
    response?: string;
    sections?: ZakiApiSection[];
    highlighted_entities?: import("@/lib/simulation-store").HighlightedEntity[];
    grounded_in?: Record<string, unknown>;
    uncertainty?: string[];
    suggested_actions?: ZakiApiSuggestedAction[];
    copilot?: {
      message?: string;
      conversation_starters?: Array<{ label?: string; prompt?: string }>;
    };
  };
  conversation?: {
    reply?: string;
    followups?: Array<{ label?: string; prompt?: string }>;
  };
  copilot?: {
    message?: string;
    conversation_starters?: Array<{ label?: string; prompt?: string }>;
  };
  zaki_v2?: ZakiCopilotResponse;
}

export interface ZakiJourneyStage {
  index: number;
  label: string;
  summary: string;
  status: "PENDING" | "ACTIVE" | "COMPLETED" | "FAILED" | string;
}

export interface ZakiJourneyStatus {
  title: string;
  story: string;
  currentStage: string;
  currentStatus: string;
  finalizedThrough: string;
  confidence: string;
  terminalState: string;
  nextAction: string;
  advice: string;
  stages: ZakiJourneyStage[];
}

export type ZakiSelectedContext = StoreZakiSelectedContext & {
  run_id: string;
  revision: number;
  metadata?: Record<string, unknown>;
};

export type ZakiFocusContext = Pick<ZakiSelectedContext, "context_type" | "context_id" | "display_name"> & {
  metadata?: Record<string, unknown>;
  summary?: string;
  status?: string;
};

export type ZakiPromptAction = "status" | "explain" | "story";

export interface ZakiQuickPrompt {
  label: string;
  prompt: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  action?: ZakiPromptAction;
}

export interface ZakiContextExplanation {
  title: string;
  summary: string;
  currentContext: Array<{ label: string; value: string }>;
  evidence: string[];
  hypotheses: string[];
  gaps: string[];
  nextMove: string;
}

export interface ZakiConversationMessage {
  id: string;
  sender: "user" | "zaki";
  text: string;
  journeyStatus?: ZakiJourneyStatus;
  contextExplanation?: ZakiContextExplanation;
  zaki_v2?: ZakiCopilotResponse;
  storyteller?: StorytellerPayload | null;
  storyOnly?: boolean;
}
