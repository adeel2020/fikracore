"""IncidentContext — the single Layer 1 → Layer 2 contract.

Requirements §4: a normalized internal representation that the reasoning layer
can consume. It is a *temporary reasoning context*, NOT a replacement for
gbrain, NOT a graph copy.

Every element is provenance-wrapped (ProvenanceFact) so the reasoning layer can
cite sources, timestamps, confidence, and the typed relationship that produced
each fact — never silently discarding provenance (§5).

Kinds map to the mobile-core schema types (unchanged — no new schema types):
incident, network-function, service, kpi, kpi-event, symptom, hypothesis,
evidence, remediation, observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .provenance import ProvenanceFact


@dataclass
class IncidentContext:
    """Normalized retrieval result for one incident."""

    incident: dict[str, Any] | None = None
    timeline: list[ProvenanceFact] = field(default_factory=list)
    services: list[ProvenanceFact] = field(default_factory=list)
    network_functions: list[ProvenanceFact] = field(default_factory=list)
    kpis: list[ProvenanceFact] = field(default_factory=list)
    kpi_events: list[ProvenanceFact] = field(default_factory=list)
    symptoms: list[ProvenanceFact] = field(default_factory=list)
    hypotheses: list[ProvenanceFact] = field(default_factory=list)
    evidence: list[ProvenanceFact] = field(default_factory=list)
    remediations: list[ProvenanceFact] = field(default_factory=list)
    recovery_events: list[ProvenanceFact] = field(default_factory=list)
    similar_incidents: list[ProvenanceFact] = field(default_factory=list)
    correlation_metadata: dict[str, Any] = field(default_factory=dict)
    lookup_trace: list[str] = field(default_factory=list)

    @property
    def incident_id(self) -> str | None:
        if self.incident:
            return self.incident.get("slug")
        return None

    def summary(self) -> dict[str, int]:
        """Counts per kind — useful for tests and debugging."""
        return {
            "incident": 1 if self.incident else 0,
            "timeline": len(self.timeline),
            "services": len(self.services),
            "network_functions": len(self.network_functions),
            "kpis": len(self.kpis),
            "kpi_events": len(self.kpi_events),
            "symptoms": len(self.symptoms),
            "hypotheses": len(self.hypotheses),
            "evidence": len(self.evidence),
            "remediations": len(self.remediations),
            "recovery_events": len(self.recovery_events),
            "similar_incidents": len(self.similar_incidents),
            "correlation": 1 if self.correlation_metadata else 0,
            "lookup_trace": len(self.lookup_trace),
        }
