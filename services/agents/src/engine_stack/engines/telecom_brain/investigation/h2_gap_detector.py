"""Operational Knowledge-Gap Discovery, Causal Boundary Localization, and Next-Best-Evidence Utility Ranking.

Enforces H2 principles:
- Unknown-unknown discovery != guessing hidden truth
- Never hallucinate unobserved topology entities
- Candidate knowledge is immutable and never automatically promoted
- Strictly truth-blind operational reasoning
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from .contracts import (
    CandidateRelationship,
    Hypothesis,
    KnowledgeGap,
    KnowledgeGapType,
    KnowledgeState,
    ModelContradiction,
    NextBestEvidenceRequest,
    SuspectedMissingRelation,
    UnexplainedResidual,
)
from ..presentation.naming import default_naming_resolver


def localize_knowledge_gap(
    events: list[Any],
    graph: nx.DiGraph,
    abnormal: list[Any],
    impacted: set[str],
    known_pairs: set[frozenset[str]],
    best_hypothesis: Hypothesis | None = None,
) -> tuple[list[KnowledgeGap], list[CandidateRelationship], list[UnexplainedResidual], list[ModelContradiction]]:
    """Analyze operational evidence and graph topology to detect and localize knowledge gaps."""
    gaps: list[KnowledgeGap] = []
    candidates: list[CandidateRelationship] = []
    residuals: list[UnexplainedResidual] = []
    contradictions: list[ModelContradiction] = []

    # 1. Unverified path adjacencies observed in telemetry
    candidate_id_seq = 1
    unrelated_services = {item.service[0] for item in events if item.service and item.polarity == "healthy"}

    for item in events:
        if item.service and any(s in unrelated_services for s in item.service):
            continue
        for source, target in zip(item.observed_path, item.observed_path[1:]):
            if frozenset((source, target)) not in known_pairs and source != target:
                pair = (source, target)
                if not any((c.source, c.target) == pair for c in candidates):
                    candidate_rel = CandidateRelationship(
                        candidate_id=f"REL-H2-{candidate_id_seq:03d}",
                        source=source,
                        target=target,
                        proposed_type="routes-through",
                        state=KnowledgeState.CANDIDATE,
                        supporting_evidence=[item.evidence_id],
                        reason="Observed telemetry path adjacency is absent from operational knowledge; requires validation",
                    )
                    candidates.append(candidate_rel)

                    # Create corresponding KnowledgeGap
                    gap_type = _classify_gap_type(source, target, item)
                    from_name = default_naming_resolver.to_display_name(source)
                    to_name = default_naming_resolver.to_display_name(target)
                    gaps.append(
                        KnowledgeGap(
                            gap_id=f"KG-{len(gaps)+1:03d}",
                            gap_type=gap_type,
                            status=KnowledgeState.CANDIDATE,
                            affected_entities=[source, target],
                            suspected_missing_relation=SuspectedMissingRelation(
                                from_entity=source,
                                relation="ROUTES_THROUGH",
                                to_entity=target,
                            ),
                            reason=f"Observed telemetry indicates traffic routes from {from_name} to {to_name}, but operational topology lacks this relationship.",
                            supporting_evidence=[item.evidence_id],
                            contradicting_evidence=[],
                            unexplained_residual=[],
                            confidence=0.75,
                            required_validation=True,
                            display_name=f"Missing path between {from_name} and {to_name}",
                        )
                    )
                    candidate_id_seq += 1

    # 2. Structural boundary exhaustion: known path ends, but downstream symptoms persist
    # If the best hypothesis cannot reach all impacted nodes, localize where reachable ends
    if best_hypothesis and impacted:
        reachable = set(best_hypothesis.root_entities)
        for r in best_hypothesis.root_entities:
            if r in graph:
                reachable.update(nx.descendants(graph, r))

        unreached = impacted - reachable
        if unreached:
            if len(best_hypothesis.root_entities) > 1:
                boundary_node = best_hypothesis.root_entities[0]
                unreached_targets = set(best_hypothesis.root_entities[1:]) | unreached
            else:
                # Check if degradation began at an unreached entity earlier than reachable
                earliest_impacted = min(abnormal, key=lambda item: item.event_time).canonical_entity
                if earliest_impacted in unreached:
                    boundary_node = earliest_impacted
                    unreached_targets = reachable
                else:
                    # Find frontier boundary in reachable
                    boundary_nodes = [n for n in reachable if n in graph and any(item.canonical_entity == n for item in abnormal)]
                    if not boundary_nodes:
                        boundary_nodes = list(best_hypothesis.root_entities)
                    boundary_node = min(boundary_nodes, key=lambda n: graph.out_degree(n) if n in graph else 0)
                    unreached_targets = unreached

            boundary_name = default_naming_resolver.to_display_name(boundary_node)
            residual_evidence = [item.evidence_id for item in abnormal if item.canonical_entity in unreached_targets]
            affected_services = sorted({s for item in abnormal if item.canonical_entity in unreached_targets for s in item.service})

            residual_record = UnexplainedResidual(
                residual_id=f"RES-{len(residuals)+1:03d}",
                evidence_ids=residual_evidence,
                affected_services=affected_services,
                known_path_exhausted_at=boundary_node,
                severity=0.85,
                structural_suspicion=True,
            )
            residuals.append(residual_record)

            # Contradiction: known model predicts effects terminate at boundary, but downstream alarms exist
            contradictions.append(
                ModelContradiction(
                    contradiction_id=f"MOD-CONTRA-{len(contradictions)+1:03d}",
                    expected_behavior=f"Operational topology predicts degradation contained within reachable subgraph of {boundary_name}.",
                    observed_behavior=f"Degradation observed across unlinked components ({', '.join(sorted(unreached_targets)[:3])}) without known causal path.",
                    evidence_ids=residual_evidence,
                    severity=0.85,
                )
            )

            # Knowledge gap boundary (without hallucinating unobserved intermediate entities!)
            gap_type = _infer_boundary_gap_type(boundary_node, unreached_targets)
            gaps.append(
                KnowledgeGap(
                    gap_id=f"KG-{len(gaps)+1:03d}",
                    gap_type=gap_type,
                    status=KnowledgeState.CANDIDATE,
                    affected_entities=[boundary_node] + sorted(unreached_targets)[:2],
                    suspected_missing_relation=SuspectedMissingRelation(
                        from_entity=boundary_node,
                        relation="ROUTES_THROUGH",
                        to_entity=None,  # Intentionally null/boundary-only: NEVER hallucinate unobserved entity!
                    ),
                    reason=f"Degradation propagates beyond known boundary at {boundary_name}; downstream transport or service dependency missing.",
                    supporting_evidence=residual_evidence,
                    contradicting_evidence=[],
                    unexplained_residual=[residual_record.residual_id],
                    confidence=0.70,
                    required_validation=True,
                    display_name=f"Operational knowledge gap downstream of {boundary_name}",
                )
            )

    return gaps, candidates, residuals, contradictions


def _classify_gap_type(source: str, target: str, evidence_item: Any) -> KnowledgeGapType:
    """Classify the probable gap type from entity domains, prefixes, and evidence."""
    s_upper, t_upper = source.upper(), target.upper()

    if "POWER" in s_upper or "POWER" in t_upper or "ENV" in s_upper or "ENV" in t_upper:
        return KnowledgeGapType.MISSING_POWER_ENVIRONMENT
    if "DC" in s_upper or "DC" in t_upper or "CONTAINER" in s_upper or "HOST" in s_upper or "K8S" in s_upper:
        return KnowledgeGapType.MISSING_HOSTING_CONTAINER
    if "TICKET" in s_upper or "CRM" in s_upper or "BSS" in s_upper:
        return KnowledgeGapType.MISSING_SERVICE_TO_FUNCTION
    if "DRA" in s_upper or "ROAMING" in s_upper or "IPX" in s_upper:
        return KnowledgeGapType.MISSING_ROAMING_INTERCONNECT
    if "DB" in s_upper or "CACHE" in s_upper or "REDIS" in s_upper or "KAFKA" in s_upper:
        return KnowledgeGapType.MISSING_DB_CACHE_MESSAGE_BUS
    if "MONITOR" in s_upper or "NMS" in s_upper:
        return KnowledgeGapType.MISSING_MONITORING_DEPENDENCY
    if "SEC" in s_upper or "FW" in s_upper or "FIREWALL" in s_upper:
        return KnowledgeGapType.MISSING_SECURITY_CONTROL
    if "RTR" in s_upper and "RTR" in t_upper:
        return KnowledgeGapType.MISSING_TRANSPORT_PATH
    if "VRF" in s_upper or "VRF" in t_upper:
        return KnowledgeGapType.MISSING_DEPENDENCY

    return KnowledgeGapType.MISSING_DEPENDENCY


def _infer_boundary_gap_type(boundary_node: str, unreached: set[str]) -> KnowledgeGapType:
    """Infer gap type at structural boundary based on boundary node and unreached entities."""
    b_upper = boundary_node.upper()
    unreached_upper = " ".join(u.upper() for u in unreached)

    if "POWER" in b_upper or "POWER" in unreached_upper:
        return KnowledgeGapType.MISSING_POWER_ENVIRONMENT
    if "DC" in b_upper or "K8S" in b_upper or "HOST" in b_upper:
        return KnowledgeGapType.MISSING_HOSTING_CONTAINER
    if "DRA" in b_upper or "OCS" in unreached_upper:
        return KnowledgeGapType.MISSING_ROAMING_INTERCONNECT
    if "DB" in unreached_upper or "MYSQL" in unreached_upper:
        return KnowledgeGapType.MISSING_DB_CACHE_MESSAGE_BUS
    if "FW" in unreached_upper or "SEC" in unreached_upper:
        return KnowledgeGapType.MISSING_SECURITY_CONTROL
    if "BSS" in b_upper or "BILLING" in b_upper:
        return KnowledgeGapType.MISSING_PROVISIONING_BSS
    if "NMS" in b_upper or "OSS" in b_upper:
        return KnowledgeGapType.MISSING_MONITORING_DEPENDENCY
    if "EXT" in unreached_upper or "ROAMING" in unreached_upper:
        return KnowledgeGapType.MISSING_EXTERNAL_DEPENDENCY
    if "SMF" in unreached_upper and "AMF" in b_upper:
        return KnowledgeGapType.MISSING_SHARED_DEPENDENCY
    if "TICKET" in unreached_upper or "CRM" in unreached_upper:
        return KnowledgeGapType.MISSING_SERVICE_TO_FUNCTION
    if "CORE" in unreached_upper and "PE" in b_upper:
        return KnowledgeGapType.MISSING_TRANSPORT_PATH

    return KnowledgeGapType.MISSING_DEPENDENCY


def rank_next_best_evidence(
    gaps: list[KnowledgeGap],
    residuals: list[UnexplainedResidual],
    hypotheses: list[Hypothesis],
    max_requests: int = 3,
) -> list[NextBestEvidenceRequest]:
    """Calculate utility-ranked next-best-evidence requests to reduce uncertainty.
    
    Priority formula:
        priority = round(expected_information_gain * reliability / (cost + latency + risk), 4)
    """
    requests: list[NextBestEvidenceRequest] = []
    seen_questions: set[str] = set()

    for gap in gaps:
        target_entity = gap.suspected_missing_relation.from_entity
        target_display = default_naming_resolver.to_display_name(target_entity)

        # 1. Neighbor discovery query
        q1 = f"Which downstream transport node carries traffic from {target_display}?"
        if q1 not in seen_questions:
            seen_questions.add(q1)
            gain = 0.85
            cost = 0.20
            latency = 0.50
            risk = 0.02
            rel = 0.95
            prio = round(gain * rel / (cost + latency + risk), 4)
            requests.append(
                NextBestEvidenceRequest(
                    request_id=f"NBE-{len(requests)+1:03d}",
                    question=q1,
                    evidence_type="TOPOLOGY_NEIGHBOR",
                    target=target_entity,
                    expected_information_gain=gain,
                    cost=cost,
                    risk=risk,
                    latency=latency,
                    reliability=rel,
                    availability=1.0,
                    priority=prio,
                    hypotheses_discriminated=[gap.gap_id],
                )
            )

        # 2. Routing table / interface query
        q2 = f"Retrieve routing table and next-hop forwarding state for {target_display}."
        if q2 not in seen_questions:
            seen_questions.add(q2)
            gain = 0.75
            cost = 0.30
            latency = 1.00
            risk = 0.05
            rel = 0.90
            prio = round(gain * rel / (cost + latency + risk), 4)
            requests.append(
                NextBestEvidenceRequest(
                    request_id=f"NBE-{len(requests)+1:03d}",
                    question=q2,
                    evidence_type="ROUTING_TABLE",
                    target=target_entity,
                    expected_information_gain=gain,
                    cost=cost,
                    risk=risk,
                    latency=latency,
                    reliability=rel,
                    availability=1.0,
                    priority=prio,
                    hypotheses_discriminated=[gap.gap_id],
                )
            )

    # Sort strictly by priority descending, then request_id
    requests.sort(key=lambda r: (-r.priority, r.request_id))
    return requests[:max_requests]


def save_candidate_knowledge(
    candidate: CandidateRelationship,
    output_dir: Path | str,
) -> Path:
    """Save immutable candidate knowledge record to validation queue.
    
    NEVER mutates live operational telecombrain.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    file_path = out_path / f"{candidate.candidate_id}.json"
    data = candidate.model_dump(mode="json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    return file_path


__all__ = [
    "localize_knowledge_gap",
    "rank_next_best_evidence",
    "save_candidate_knowledge",
]
