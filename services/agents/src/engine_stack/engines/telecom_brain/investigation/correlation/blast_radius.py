"""Phase 2.4: Service & Blast Radius Correlation.

Primary impacted customer service identification, coincidental alarm filtering, and damage envelope boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from ..contracts import Evidence


def _quality(evidence: Evidence) -> float:
    """Compute evidence quality score for filtering."""
    observed = 1 if evidence.observed_or_inferred in {"OBSERVED", "CONFIRMED"} else 0.4
    return evidence.source_reliability * evidence.freshness * observed


@dataclass
class BlastRadiusResult:
    """Output of Phase 2.4 service and blast radius correlation."""
    abnormal: list[Evidence]
    healthy: list[Evidence]
    impacted: set[str]
    unrelated: list[Evidence]
    roots: list[str]
    impacted_service: str | None
    service_entities: dict[str, set[str]]
    domains: list[str]


def analyze_blast_radius(
    events: list[Evidence],
    graph: nx.DiGraph,
) -> BlastRadiusResult:
    """Analyze blast radius and partition evidence into abnormal/healthy sets.

    This implements Phase 2.4 of the Correlation Engine:
    - Identify primary impacted customer service
    - Filter coincidental/unrelated alarms
    - Partition telemetry into abnormal vs healthy
    - Compute blast radius (impacted entities)
    - Find candidate root entities via graph ancestors
    """
    # Group abnormal entities by service
    service_entities: dict[str, set[str]] = {}
    for item in events:
        if item.polarity == "abnormal":
            for service in item.service:
                service_entities.setdefault(service, set()).add(item.canonical_entity)

    # Primary impacted service: most entities, then alphabetical
    impacted_service = (
        min(service_entities, key=lambda s: (-len(service_entities[s]), s))
        if service_entities else None
    )

    # Filter coincidental evidence (different service than primary)
    unrelated = [
        item for item in events
        if item.service and impacted_service not in item.service
    ]

    # Partition abnormal (quality >= 0.3, not unrelated)
    abnormal = [
        item for item in events
        if item.polarity == "abnormal" and _quality(item) >= 0.3 and item not in unrelated
    ]

    # Partition healthy (quality >= 0.5)
    healthy = [
        item for item in events
        if item.polarity == "healthy" and _quality(item) >= 0.5
    ]

    # Blast radius: unique impacted entities
    impacted = {item.canonical_entity for item in abnormal}

    # Candidate roots: all entities + graph ancestors of impacted
    roots = sorted({item.canonical_entity for item in events})
    roots = sorted(
        set(roots) | {ancestor for entity in impacted for ancestor in nx.ancestors(graph, entity)}
    )

    domains = sorted({item.domain for item in events})

    return BlastRadiusResult(
        abnormal=abnormal,
        healthy=healthy,
        impacted=impacted,
        unrelated=unrelated,
        roots=roots,
        impacted_service=impacted_service,
        service_entities=service_entities,
        domains=domains,
    )
