"""CorrelationEngine: Coordinates the 4-Dimension Correlation Pipeline.

Runs Phases 2.1-2.4 sequentially, emitting structured telemetry for each phase
via step_callback. Produces a CorrelationResult consumed by downstream
Hypothesis Generation and Testing stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import networkx as nx

from ..contracts import Evidence, Relationship
from ..knowledge import CanonicalKnowledge
from .temporal_identity import TemporalIdentityResult, normalize_evidence
from .topological import TopologicalResult, build_knowledge_graph
from .pathways import PathwaysResult, evaluate_pathways
from .blast_radius import BlastRadiusResult, analyze_blast_radius


@dataclass
class CorrelationResult:
    """Composite output of all 4 correlation phases."""
    temporal: TemporalIdentityResult
    topological: TopologicalResult
    pathways: PathwaysResult
    blast_radius: BlastRadiusResult
    events: list[Evidence] = field(default_factory=list)
    abnormal: list[Evidence] = field(default_factory=list)
    healthy: list[Evidence] = field(default_factory=list)
    impacted: set[str] = field(default_factory=set)
    roots: list[str] = field(default_factory=list)
    edges: dict[str, Relationship] = field(default_factory=dict)
    graph: nx.DiGraph = field(default_factory=lambda: nx.DiGraph())


class CorrelationEngine:
    """4-Dimension Correlation Engine coordinator.

    Runs Phases 2.1-2.4 sequentially:
      2.1 Temporal & Identity (normalization, freshness, collapse)
      2.2 Topological (graph traversal, DiGraph inversion)
      2.3 Cross-Domain Pathways (9 analytical funnels)
      2.4 Service & Blast Radius (damage envelope, noise isolation)
    """

    def __init__(self, knowledge: CanonicalKnowledge):
        self.knowledge = knowledge

    def run(
        self,
        evidence: list[Evidence],
        step_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> CorrelationResult:
        """Execute all 4 correlation phases and return composite result."""
        cb = step_callback or (lambda t, d: None)

        # Phase 2.1: Temporal & Identity Correlation
        temporal = normalize_evidence(evidence, self.knowledge)
        cb("correlation_2_1", {
            "raw_count": temporal.raw_count,
            "normalized_count": temporal.normalized_count,
            "collapsed_count": temporal.collapsed_count,
            "sources": temporal.sources,
            "types": temporal.types,
            "time_span": temporal.time_span,
            "avg_freshness": temporal.avg_freshness,
            "max_age_hours": temporal.max_age_hours,
            "min_time": temporal.min_time,
            "max_time": temporal.max_time,
        })

        # Phase 2.2: Topological Correlation
        topological = build_knowledge_graph(temporal.events, self.knowledge)
        cb("correlation_2_2", {
            "provider_name": topological.provider_name,
            "entities_traversed": len(topological.traversed_entities),
            "relationships_found": len(topological.edges),
            "node_count": topological.graph.number_of_nodes(),
            "edge_count": topological.graph.number_of_edges(),
            "reads_count": topological.reads_count,
            "failures_count": len(topological.failures),
        })

        # Phase 2.3: Cross-Domain Pathway Correlation
        from .blast_radius import _quality
        preliminary_abnormal = [
            item for item in temporal.events
            if item.polarity == "abnormal" and _quality(item) >= 0.3
        ]
        preliminary_impacted = {item.canonical_entity for item in preliminary_abnormal}

        pathways = evaluate_pathways(
            temporal.events,
            topological.edges,
            preliminary_impacted,
            topological.failures,
        )
        cb("correlation_2_3", {
            "active_count": pathways.active_count,
            "pathways": [
                {"name": p.name, "active": p.active, "reason": p.reason}
                for p in pathways.pathways
            ],
            "domains": pathways.domains,
            "evidence_count": pathways.evidence_count,
            "abnormal_count": pathways.abnormal_count,
        })

        # Phase 2.4: Service & Blast Radius Correlation
        blast = analyze_blast_radius(temporal.events, topological.graph)
        cb("correlation_2_4", {
            "abnormal_count": len(blast.abnormal),
            "healthy_count": len(blast.healthy),
            "impacted_count": len(blast.impacted),
            "impacted_service": blast.impacted_service,
            "service_entities": {k: list(v) for k, v in blast.service_entities.items()},
            "domains": blast.domains,
            "unrelated_count": len(blast.unrelated),
            "roots_count": len(blast.roots),
        })

        return CorrelationResult(
            temporal=temporal,
            topological=topological,
            pathways=pathways,
            blast_radius=blast,
            events=temporal.events,
            abnormal=blast.abnormal,
            healthy=blast.healthy,
            impacted=blast.impacted,
            roots=blast.roots,
            edges=topological.edges,
            graph=topological.graph,
        )
