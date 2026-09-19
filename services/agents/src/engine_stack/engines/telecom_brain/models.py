"""Shared models for the TelecomBrainEngine service stack."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

if not hasattr(BaseModel, "model_dump"):
    BaseModel.model_dump = lambda self, **kwargs: self.dict(**{k: v for k, v in kwargs.items() if k != "mode"})
if not hasattr(BaseModel, "model_copy"):
    BaseModel.model_copy = lambda self, **kwargs: self.copy(**kwargs)
if not hasattr(BaseModel, "model_validate"):
    BaseModel.model_validate = classmethod(lambda cls, obj, **kwargs: obj if isinstance(obj, cls) else cls.parse_obj(obj))
if not hasattr(BaseModel, "model_validate_json"):
    BaseModel.model_validate_json = classmethod(lambda cls, json_data, **kwargs: cls.parse_raw(json_data, **kwargs))
if not hasattr(BaseModel, "model_dump_json"):
    BaseModel.model_dump_json = lambda self, **kwargs: self.json(**kwargs)


class FCAPSClassification(str, Enum):
    """FCAPS categories used as a learning and enrichment lens."""

    FAULT = "fault"
    CHANGE_REQUEST_CONFIGURATION = "change_request_configuration"
    ACCOUNTING = "accounting"
    PERFORMANCE = "performance"
    SECURITY = "security"


class EvidenceGrade(str, Enum):
    """Narrative claim quality used by the professional storyteller contract."""

    CONFIRMED_FACT = "confirmed_fact"
    INFERRED_RELATION = "inferred_relation"
    WEAK_SIGNAL = "weak_signal"
    MISSING_EVIDENCE = "missing_evidence"
    CONTRADICTION = "contradiction"


class IncidentLifecycleState(str, Enum):
    """Lifecycle states supported by incident-aware storytelling."""

    CANDIDATE = "candidate"
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    REOPENED = "reopened"
    MERGED = "merged"
    SUPPRESSED = "suppressed"
    UNKNOWN = "unknown"


class StoryAudience(str, Enum):
    """Audience profiles for written, spoken, and visual incident outputs."""

    EXECUTIVE = "executive"
    NOC_ENGINEER = "noc_engineer"
    RCA_LEAD = "rca_lead"
    CUSTOMER = "customer"
    POST_INCIDENT_REVIEW = "post_incident_review"


class VisualWidgetType(str, Enum):
    """Visual explanation widget types emitted to the frontend."""

    TIMELINE = "timeline"
    CAUSAL_CHAIN = "causal_chain"
    DOMAIN_IMPACT_MAP = "domain_impact_map"
    EVIDENCE_CONFIDENCE_MATRIX = "evidence_confidence_matrix"
    KPI_TREND = "kpi_trend"
    ALARM_CORRELATION_GRAPH = "alarm_correlation_graph"
    TOPOLOGY_SERVICE_IMPACT = "topology_service_impact"
    MISSING_EVIDENCE = "missing_evidence"
    NEXT_ACTION_TREE = "next_action_tree"


class ProvenanceRef(BaseModel):
    """Traceable source reference for claims and widgets."""

    source: str | None = None
    slug: str | None = None
    timestamp: str | None = None
    relationship: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class EvidenceClaim(BaseModel):
    """One storyteller claim with explicit grade, confidence, and provenance."""

    id: str
    statement: str
    grade: EvidenceGrade
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    fcaps: list[FCAPSClassification] = Field(default_factory=list)
    domain: str | None = None
    service_procedure: str | None = None
    object_ref: str | None = None
    provenance: list[ProvenanceRef] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NarrativeAction(BaseModel):
    """Next best question/action produced by the NOC storyteller."""

    id: str
    label: str
    action_type: str
    priority: int = Field(default=3, ge=1, le=5)
    requires_approval: bool = False
    rationale: str | None = None
    supports_claim_ids: list[str] = Field(default_factory=list)


class IncidentNarrative(BaseModel):
    """Professional, incident-agnostic narrative contract."""

    incident_id: str
    audience: StoryAudience = StoryAudience.EXECUTIVE
    lifecycle_state: IncidentLifecycleState = IncidentLifecycleState.UNKNOWN
    title: str = ""
    executive_summary: str = ""
    impact_summary: str = ""
    rca_status: str = ""
    domains: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    claims: list[EvidenceClaim] = Field(default_factory=list)
    causal_chain: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    next_actions: list[NarrativeAction] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    written_story: str = ""
    spoken_brief: str = ""
    provenance: list[ProvenanceRef] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VisualWidget(BaseModel):
    """One frontend-renderable visual explanation widget."""

    id: str
    title: str
    type: VisualWidgetType
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    provenance: list[ProvenanceRef] = Field(default_factory=list)
    supports_claim_ids: list[str] = Field(default_factory=list)


class VisualExplanation(BaseModel):
    """Structured visual companion to an incident narrative."""

    incident_id: str
    audience: StoryAudience = StoryAudience.EXECUTIVE
    primary_widget: VisualWidgetType | None = None
    widgets: list[VisualWidget] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TelecomTrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    selected_service: str | None = None
    service_confidence: float = 0.0
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IncidentRef(BaseModel):
    id: str
    title: str | None = None
    status: str | None = None
    severity: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlarmEvidence(BaseModel):
    id: str | None = None
    name: str
    severity: str | None = None
    source: str | None = None
    starts_at: datetime | None = None
    labels: dict[str, Any] = Field(default_factory=dict)
    raw_ref: str | None = None
    retained_reason: str | None = None


class KpiEvidence(BaseModel):
    name: str
    value: float | None = None
    unit: str | None = None
    threshold: float | None = None
    breached: bool | None = None
    source: str | None = None
    raw_ref: str | None = None
    labels: dict[str, Any] = Field(default_factory=dict)


class TopologyNode(BaseModel):
    id: str
    name: str
    domain: str | None = None
    role: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ServiceProcedure(BaseModel):
    id: str
    name: str
    domain: str | None = None
    dependencies: list[str] = Field(default_factory=list)


class IntentViolation(BaseModel):
    intent_id: str | None = None
    procedure: str | None = None
    description: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    retained: bool = True


class RCAHypothesis(BaseModel):
    cause: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)
    missing_proof: list[str] = Field(default_factory=list)
    next_diagnostic_step: str | None = None


class RecommendedAction(BaseModel):
    action_type: str
    description: str
    requires_approval: bool = True
    owner: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TelecomRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    incident_refs: list[IncidentRef] = Field(default_factory=list)
    alarms: list[AlarmEvidence] = Field(default_factory=list)
    kpis: list[KpiEvidence] = Field(default_factory=list)
    topology_refs: list[TopologyNode] = Field(default_factory=list)
    service_procedure_refs: list[ServiceProcedure] = Field(default_factory=list)
    source: str = "jarvis"


class TelecomResult(BaseModel):
    text: str
    spoken_response: str | None = None
    service_id: str | None = None
    trace: TelecomTrace = Field(default_factory=TelecomTrace)
    incidents: list[IncidentRef] = Field(default_factory=list)
    alarm_evidence: list[AlarmEvidence] = Field(default_factory=list)
    kpi_evidence: list[KpiEvidence] = Field(default_factory=list)
    intent_violations: list[IntentViolation] = Field(default_factory=list)
    rca_hypotheses: list[RCAHypothesis] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    fcaps: list[FCAPSClassification] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)

    def response_for_mark(self) -> str:
        """Return the concise voice text when present, otherwise the full text."""
        return self.spoken_response or self.text
