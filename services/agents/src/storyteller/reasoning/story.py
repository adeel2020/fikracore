"""Deterministic story dataclasses.

Layer 2 (Reasoning / Storytelling) contract. The pipeline produces:

    IncidentContext (L1)  →  IncidentStory (deterministic)  →  StoryResponse

The deterministic ``IncidentStory`` is the artifact that tests target: every
causal step, hypothesis assessment, remediation, and recovery event keeps its
provenance and claim classification. ``StoryResponse`` is the *presentation*
wrapper around it; narrative text is only added by the optional LLM
synthesizer (``llm.py``) and is never required for correctness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..knowledge.provenance import ProvenanceFact


@dataclass
class CausalStep:
    """One link in the causal chain.

    ``claim_type`` is a member of the shared claim taxonomy (see provenance.py);
    ``fact`` carries the provenance of the underlying retrieval so the step can
    cite where the value came from.
    """

    label: str
    claim_type: str
    fact: ProvenanceFact | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "claim_type": self.claim_type,
            "fact": self.fact.to_dict() if self.fact else None,
        }


@dataclass
class CausalChain:
    """Ordered KPI-degradation → … → root-cause chain, deterministic."""

    steps: list[CausalStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"steps": [s.to_dict() for s in self.steps]}


@dataclass
class HypothesisAssessment:
    """Assessment of a single hypothesis.

    ``status`` is one of confirmed / plausible / insufficient-evidence /
    conflicting-evidence. Ranking never fabricates: if a hypothesis has no
    status, no evidence, or no confidence, the assessment reflects that.
    """

    hypothesis: ProvenanceFact
    status: str
    score: float
    evidence: list[ProvenanceFact] = field(default_factory=list)
    explains: list[ProvenanceFact] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis.to_dict(),
            "status": self.status,
            "score": self.score,
            "evidence": [e.to_dict() for e in self.evidence],
            "explains": [e.to_dict() for e in self.explains],
            "explanation": self.explanation,
        }


@dataclass
class IncidentStory:
    """The deterministic incident narrative (structure only)."""

    incident_id: str
    summary: str = ""
    severity: str = ""
    status: str = ""
    impact: list[ProvenanceFact] = field(default_factory=list)
    timeline: list[ProvenanceFact] = field(default_factory=list)
    services: list[ProvenanceFact] = field(default_factory=list)
    network_functions: list[ProvenanceFact] = field(default_factory=list)
    kpis: list[ProvenanceFact] = field(default_factory=list)
    kpi_events: list[ProvenanceFact] = field(default_factory=list)
    symptoms: list[ProvenanceFact] = field(default_factory=list)
    hypotheses: list[HypothesisAssessment] = field(default_factory=list)
    causal_chain: CausalChain | None = None
    root_cause: ProvenanceFact | None = None
    remediations: list[ProvenanceFact] = field(default_factory=list)
    recovery_events: list[ProvenanceFact] = field(default_factory=list)
    similar_incidents: list[ProvenanceFact] = field(default_factory=list)
    correlation_metadata: dict[str, Any] = field(default_factory=dict)
    unresolved_questions: list[str] = field(default_factory=list)
    generated_by: str = "deterministic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "summary": self.summary,
            "severity": self.severity,
            "status": self.status,
            "impact": [f.to_dict() for f in self.impact],
            "timeline": [f.to_dict() for f in self.timeline],
            "services": [f.to_dict() for f in self.services],
            "network_functions": [f.to_dict() for f in self.network_functions],
            "kpis": [f.to_dict() for f in self.kpis],
            "kpi_events": [f.to_dict() for f in self.kpi_events],
            "symptoms": [f.to_dict() for f in self.symptoms],
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "causal_chain": self.causal_chain.to_dict() if self.causal_chain else None,
            "root_cause": self.root_cause.to_dict() if self.root_cause else None,
            "remediations": [f.to_dict() for f in self.remediations],
            "recovery_events": [f.to_dict() for f in self.recovery_events],
            "similar_incidents": [f.to_dict() for f in self.similar_incidents],
            "correlation_metadata": self.correlation_metadata,
            "unresolved_questions": self.unresolved_questions,
            "generated_by": self.generated_by,
        }


@dataclass
class StoryResponse:
    """Presentation wrapper around an IncidentStory.

    ``story`` is always the deterministic artifact. ``narrative`` is populated
    only when the optional LLM synthesizer is enabled (``llm.py``); callers can
    check ``synthesized`` to know whether narrative text is real or absent.
    """

    story: IncidentStory
    narrative: str = ""
    synthesized: bool = False
    model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "story": self.story.to_dict(),
            "narrative": self.narrative,
            "synthesized": self.synthesized,
            "model": self.model,
        }
