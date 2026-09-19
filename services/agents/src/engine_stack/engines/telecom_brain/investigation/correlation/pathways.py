"""Phase 2.3: Cross-Domain Pathway Correlation.

Evaluates operational telemetry across 9 multi-domain analytical funnels:
  Operational Evidence, Service Dependency, Subscriber Journey, Change & Configuration,
  Traffic & Capacity, Control & Signaling, Resilience & Failover, Historical Pattern, Knowledge Gap.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..contracts import Evidence, Relationship


@dataclass
class PathwayInfo:
    """Single pathway funnel evaluation result."""
    name: str
    active: bool
    reason: str


@dataclass
class PathwaysResult:
    """Output of Phase 2.3 cross-domain pathway correlation."""
    pathways: list[PathwayInfo]
    active_count: int
    domains: list[str]
    evidence_count: int
    abnormal_count: int
    root_count: int
    relationship_count: int
    knowledge_gap_count: int


# Canonical pathway names (9 funnels)
PATHWAY_NAMES = [
    "Operational Evidence",
    "Service Dependency",
    "Topology & Propagation",
    "Subscriber Journey",
    "Change & Configuration",
    "Traffic & Capacity",
    "Control & Signaling",
    "Resilience & Failover",
    "Historical Pattern",
    "Knowledge Gap",
]

# Domain keyword sets for pathway evaluation
TRANSPORT_DOMAINS = {"IP TRANSPORT", "TRANSPORT", "NETWORK", "IP"}
SUBSCRIBER_DOMAINS = {"CRM", "BILLING", "SUBSCRIBER"}
CAPACITY_DOMAINS = {"TRAFFIC", "CAPACITY", "KPI"}
SIGNALING_DOMAINS = {"RAN", "CORE", "CONTROL", "SIGNALING"}


def evaluate_pathways(
    events: list[Evidence],
    edges: dict[str, Relationship],
    impacted: set[str],
    knowledge_failures: set[str],
) -> PathwaysResult:
    """Evaluate 9 multi-domain analytical funnels against operational evidence.

    This implements Phase 2.3 of the Correlation Engine:
    - Each funnel evaluates a specific analytical dimension
    - Active funnels indicate which reasoning pathways are applicable
    """
    domains = sorted({item.domain for item in events})
    domains_upper = {d.upper() for d in domains}

    evidence_count = len(events)
    abnormal_count = sum(1 for e in events if e.polarity == "abnormal")
    root_count = len({item.canonical_entity for item in events})
    relationship_count = len(edges)
    knowledge_gap_count = len(knowledge_failures & impacted)

    # Check for change events in evidence
    has_change = any(item.evidence_type == "changes" for item in events)
    has_metric = any(item.evidence_type == "metrics" for item in events)
    has_trace = any(item.evidence_type == "traces" for item in events)

    pathways = [
        PathwayInfo(
            name="Operational Evidence",
            active=evidence_count > 0,
            reason=f"{evidence_count} events loaded" if evidence_count > 0 else "No operational evidence",
        ),
        PathwayInfo(
            name="Service Dependency",
            active=bool(domains_upper & TRANSPORT_DOMAINS),
            reason=f"Transport domains detected: {', '.join(d for d in domains if d.upper() in TRANSPORT_DOMAINS)}" if domains_upper & TRANSPORT_DOMAINS else "No transport domain evidence",
        ),
        PathwayInfo(
            name="Topology & Propagation",
            active=relationship_count > 0,
            reason=f"{relationship_count} causal relationships" if relationship_count > 0 else "No topology relationships",
        ),
        PathwayInfo(
            name="Subscriber Journey",
            active=bool(domains_upper & SUBSCRIBER_DOMAINS),
            reason=f"Subscriber domains: {', '.join(d for d in domains if d.upper() in SUBSCRIBER_DOMAINS)}" if domains_upper & SUBSCRIBER_DOMAINS else "No subscriber-facing evidence",
        ),
        PathwayInfo(
            name="Change & Configuration",
            active=has_change,
            reason="Change events detected" if has_change else "No configuration changes",
        ),
        PathwayInfo(
            name="Traffic & Capacity",
            active=bool(domains_upper & CAPACITY_DOMAINS) or has_metric,
            reason="Traffic/capacity evidence" if (domains_upper & CAPACITY_DOMAINS or has_metric) else "No capacity signals",
        ),
        PathwayInfo(
            name="Control & Signaling",
            active=bool(domains_upper & SIGNALING_DOMAINS) or has_trace,
            reason="Signaling evidence" if (domains_upper & SIGNALING_DOMAINS or has_trace) else "No control plane signals",
        ),
        PathwayInfo(
            name="Resilience & Failover",
            active=relationship_count > 0,
            reason="Topology enables resilience analysis" if relationship_count > 0 else "Insufficient topology",
        ),
        PathwayInfo(
            name="Historical Pattern",
            active=evidence_count > 3,
            reason=f"{evidence_count} events enable pattern matching" if evidence_count > 3 else "Insufficient history",
        ),
        PathwayInfo(
            name="Knowledge Gap",
            active=knowledge_gap_count > 0,
            reason=f"{knowledge_gap_count} knowledge gaps in impacted set" if knowledge_gap_count > 0 else "No knowledge gaps detected",
        ),
    ]

    active_count = sum(1 for p in pathways if p.active)

    return PathwaysResult(
        pathways=pathways,
        active_count=active_count,
        domains=domains,
        evidence_count=evidence_count,
        abnormal_count=abnormal_count,
        root_count=root_count,
        relationship_count=relationship_count,
        knowledge_gap_count=knowledge_gap_count,
    )
