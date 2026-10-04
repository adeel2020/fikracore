/**
 * Barrel export for the investigate workspace lib layer.
 * Import from this file for a clean API surface.
 */

// Types
export type {
  EvidenceItem,
  PathwayItem,
  HypothesisItem,
  GapItem,
  NextBestEvidenceItem,
  Conduit,
  HypValidationConduit,
  EventStreamItem,
  DomainClassification,
  OperationalDomainDef,
  DomainAttributionInfo,
  ScenarioAttributionProfile,
  TraceTarget,
  DetailedConduitTelemetry,
  DetailedEntityModal,
  ZakiCopilotResponse,
  ZakiApiSection,
  ZakiApiSuggestedAction,
  ZakiChatApiResponse,
  ZakiJourneyStage,
  ZakiJourneyStatus,
  ZakiSelectedContext,
  ZakiFocusContext,
  ZakiPromptAction,
  ZakiQuickPrompt,
  ZakiContextExplanation,
  ZakiConversationMessage,
} from "./types";

// Constants & SVG math
export {
  EVIDENCE_LIST,
  PATHWAYS_LIST,
  EVIDENCE_TO_PATHWAY_CONDUITS,
  HYP_TO_VALIDATION_CONDUITS,
  PATHWAYS_TO_HYPS,
  HYP_TO_PATHWAYS,
  evidenceY,
  pathwayY,
  hypY,
  pathwayDotX,
  pathwayOutDotX,
  hypInDotX,
  hypOutDotX,
  valInDotX,
  VALIDATION_INTAKE_TARGETS,
  synthInRimPoints,
  synthOutRimPoints,
  HYPOTHESES_LIST,
  HYPOTHESIS_COLORS,
  HYPOTHESIS_PROGRESS,
  OPERATIONAL_DOMAINS_CATALOG,
  TELECOM_DOMAINS_CATALOG,
  SERVICE_IMPACTS,
  TIMELINE_EVENTS,
} from "./conduit-math";

// Transform functions
export {
  getScenarioAttributionProfile,
  buildEvidenceItems,
  buildPathwayItems,
  buildEventStreamItems,
  buildHypothesisItems,
  buildGapItems,
  buildNextBestEvidenceItems,
  resolveConduitTelemetry,
  resolveEntityModal,
  renderStyledMessage,
} from "./transforms";
