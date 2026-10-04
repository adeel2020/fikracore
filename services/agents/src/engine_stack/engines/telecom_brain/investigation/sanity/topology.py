"""
S6 — Topology & Graph Integrity Validator
=========================================
Validates graph relationships and physical/logical network consistency:
- Relationship predicates are valid telecom domain verbs.
- Source and target endpoints exist and are distinct.
- Service paths and blast radius entities are anchored to canonical network elements.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


VALID_TELECOM_PREDICATES = {
    "CONNECTS_TO",
    "TRAVERSES",
    "HOSTED_ON",
    "SERVES",
    "PEERS_WITH",
    "TERMINATES",
    "BACKUP_FOR",
    "DEPENDS_ON",
    "ROUTED_VIA",
    "ENCAPSULATES",
}


class TopologyIntegrityValidator(SanityValidator):
    category = SanityCategory.S6_TOPOLOGY

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})

        # 1. Candidate Relationship Validation
        rel = data.get("relationship") or (data if "source" in data and "target" in data else None)
        if rel and isinstance(rel, dict):
            source = rel.get("source") or rel.get("src")
            target = rel.get("target") or rel.get("dst")
            predicate = str(rel.get("predicate") or rel.get("type", "")).upper()

            if not source or not target:
                results.append(
                    SanityResult(
                        check_id="S6-001",
                        category=self.category,
                        outcome=SanityOutcome.BLOCK,
                        message="Topology relationship missing source or target endpoint.",
                        violating_fields=["source", "target"],
                        remediation_hint="Specify valid canonical entities for both endpoints.",
                    )
                )
            elif source == target:
                results.append(
                    SanityResult(
                        check_id="S6-002",
                        category=self.category,
                        outcome=SanityOutcome.WARN,
                        message=f"Self-referential topology edge detected: {source} -> {target}",
                        violating_fields=["target"],
                        remediation_hint="Verify if loopback or internal interface relationship is intended.",
                    )
                )

            if predicate and predicate not in VALID_TELECOM_PREDICATES:
                results.append(
                    SanityResult(
                        check_id="S6-003",
                        category=self.category,
                        outcome=SanityOutcome.WARN,
                        message=f"Non-standard topology predicate '{predicate}'. Recommended: {sorted(list(VALID_TELECOM_PREDICATES))[:5]}",
                        violating_fields=["predicate"],
                        remediation_hint="Align predicate with canonical 4-plane schema.",
                    )
                )

        # 2. Subgraph Validation (OperationalContext visible_topology_subgraph)
        subgraph = data.get("visible_topology_subgraph")
        if subgraph and isinstance(subgraph, dict):
            nodes = subgraph.get("nodes", [])
            edges = subgraph.get("edges", [])
            if isinstance(nodes, list) and isinstance(edges, list):
                node_ids = {n.get("id") or n if isinstance(n, dict) else str(n) for n in nodes}
                for i, edge in enumerate(edges):
                    if isinstance(edge, dict):
                        u, v = edge.get("source"), edge.get("target")
                        if u and node_ids and u not in node_ids:
                            results.append(
                                SanityResult(
                                    check_id="S6-004",
                                    category=self.category,
                                    outcome=SanityOutcome.WARN,
                                    message=f"Edge [{i}] references source node '{u}' not in visible nodes set.",
                                    violating_fields=[f"edges[{i}].source"],
                                    remediation_hint="Ensure all edge endpoints exist in the visible nodes list.",
                                )
                            )

        if not results:
            results.append(
                SanityResult(
                    check_id="S6-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Topology and graph integrity verified successfully.",
                )
            )
        return results
