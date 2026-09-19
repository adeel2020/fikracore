"""Phase 2.2: Topological Correlation.

Knowledge graph traversal and dynamic causal DiGraph inversion from consumer/supplier to causal driver/sink.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from ..contracts import Evidence, KnowledgeState, Relationship
from ..knowledge import CanonicalKnowledge

# Dependency edges point from consumer to supplier. Connectivity alone is not causal direction.
DEPENDENCIES = {"depends-on", "routes-through", "carried-by", "hosted-on", "runs-on",
                "backhauled-by", "powered-by", "charges-via", "authenticates-via", "resolves-via",
                "timed-by", "uses-database", "uses-cache", "uses-message-bus", "provisioned-by"}
FORWARD_TYPES = {"member-of", "monitored-by", "supports-service", "serves"}
ACTIVE = {KnowledgeState.CONFIRMED, KnowledgeState.SUPPORTED, KnowledgeState.INFERRED, KnowledgeState.UNKNOWN}


@dataclass
class TopologicalResult:
    """Output of Phase 2.2 topological correlation."""
    edges: dict[str, Relationship]
    graph: nx.DiGraph
    provider_name: str
    reads_count: int
    failures: set[str]
    traversed_entities: list[str] = field(default_factory=list)


def build_knowledge_graph(
    events: list[Evidence],
    knowledge: CanonicalKnowledge,
) -> TopologicalResult:
    """Traverse knowledge graph and build causal DiGraph.

    This implements Phase 2.2 of the Correlation Engine:
    - Traverse knowledge edges for all canonical entities
    - Build directed graph with causal direction inversion
    - Forward types keep source→target; dependency types invert to target→source
    """
    edges: dict[str, Relationship] = {}
    traversed = sorted({item.canonical_entity for item in events})

    for slug in traversed:
        for edge in knowledge.traverse(slug):
            edges[edge.relationship_id] = edge

    graph = nx.DiGraph()
    graph.add_nodes_from(item.canonical_entity for item in events)

    for edge in sorted(edges.values(), key=lambda e: e.relationship_id):
        if edge.state not in ACTIVE:
            continue
        if edge.link_type in FORWARD_TYPES:
            source, target = edge.source, edge.target
        else:
            source, target = edge.target, edge.source
        graph.add_edge(source, target, relationship=edge)

    return TopologicalResult(
        edges=edges,
        graph=graph,
        provider_name=type(knowledge.provider).__name__,
        reads_count=len(knowledge.reads),
        failures=knowledge.failures,
        traversed_entities=traversed,
    )
