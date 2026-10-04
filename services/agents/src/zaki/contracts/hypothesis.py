"""Ranked Hypothesis Contracts for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class RankedHypothesisItem(BaseContract):
    hypothesis_id: str
    rank: int = 1
    score: float = 0.0
    state: str = "CANDIDATE"  # CANDIDATE, SUPPORTED, REJECTED
    role: str = "COMPETING"   # LEADING, COMPETING, WEAK
    causal_role: str = "ROOT" # ROOT, TRIGGER, CONTRIBUTING_CONDITION, PROPAGATION_MECHANISM, SYMPTOM
    root_entity: str = ""
    canonical_root_entity: str = ""
    domain: str = "unknown"
    statement: str = ""
    explanation_coverage: float = 0.0
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    score_components: Dict[str, float] = Field(default_factory=dict)
    provenance: List[str] = Field(default_factory=list)
    rank_delta: int = 0


class HypothesisRankingMetadata(BaseContract):
    run_id: str
    revision: int = 1
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HypothesisRankingSpec(BaseContract):
    hypotheses: List[RankedHypothesisItem] = Field(default_factory=list)
    leading_hypothesis_id: Optional[str] = None
    convergence_reached: bool = False
    convergence_gap: float = 0.0


class HypothesisRankingContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "HypothesisRanking"
    metadata: HypothesisRankingMetadata
    spec: HypothesisRankingSpec
