"""4-Dimension Correlation Engine for telecom incident root cause analysis.

Phases:
  2.1 Temporal & Identity Correlation (normalization, freshness, collapse)
  2.2 Topological Correlation (graph traversal, DiGraph inversion)
  2.3 Cross-Domain Pathway Correlation (9 analytical funnels)
  2.4 Service & Blast Radius Correlation (damage envelope, noise isolation)
"""

from .engine import CorrelationEngine
from .temporal_identity import TemporalIdentityResult, normalize_evidence
from .topological import TopologicalResult, build_knowledge_graph
from .pathways import PathwaysResult, evaluate_pathways
from .blast_radius import BlastRadiusResult, analyze_blast_radius

__all__ = [
    "CorrelationEngine",
    "TemporalIdentityResult",
    "normalize_evidence",
    "TopologicalResult",
    "build_knowledge_graph",
    "PathwaysResult",
    "evaluate_pathways",
    "BlastRadiusResult",
    "analyze_blast_radius",
]
