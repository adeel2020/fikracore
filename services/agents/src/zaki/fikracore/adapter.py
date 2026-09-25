"""FikraCore Investigation Adapter for Zaki v1.

Wraps the authoritative FikraCore reasoning engine without duplicating or altering
correlation, hypothesis ranking, or convergence logic.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from pathlib import Path

from engine_stack.engines.telecom_brain.investigation.contracts import (
    GeneratedRunInput,
    InvestigationResult,
    Terminal,
    KnowledgeState,
)
from engine_stack.engines.telecom_brain.investigation.evidence import input_from_run, load_evidence
from engine_stack.engines.telecom_brain.investigation.investigator import Investigator
from engine_stack.engines.telecom_brain.investigation.knowledge import (
    CanonicalKnowledge,
    InMemoryKnowledgeProvider,
)
from ..domain.contracts.hypothesis import RankedHypothesisItem, HypothesisRankingContract, HypothesisRankingMetadata, HypothesisRankingSpec
from ..domain.contracts.finding import CorrelationFindingContract, CorrelationFindingItem


class FikraCoreAdapter:
    """Authoritative adapter interfacing with FikraCore investigation engine."""

    def __init__(self, provider=None, resolver=None) -> None:
        self.provider = provider
        self.resolver = resolver
        self._active_results: Dict[str, InvestigationResult] = {}
        self._active_runs: Dict[str, GeneratedRunInput] = {}
        self._active_events: Dict[str, List[Any]] = {}

    def start_investigation(
        self,
        run_input: GeneratedRunInput,
        evidence: List[Any],
        input_hashes: Optional[Dict[str, str]] = None,
        step_callback: Optional[Callable[[str, Any], None]] = None,
        provider: Optional[Any] = None,
    ) -> InvestigationResult:
        active_provider = provider or self.provider
        if active_provider is None:
            # Default empty in-memory knowledge provider if none provided
            active_provider = InMemoryKnowledgeProvider([], [])
        
        investigator = Investigator(
            provider=active_provider,
            resolver=self.resolver,
            step_callback=step_callback,
        )

        result = investigator.investigate(
            run=run_input,
            evidence=evidence,
            input_hashes=input_hashes,
            step_callback=step_callback,
        )

        self._active_results[run_input.run_id] = result
        self._active_runs[run_input.run_id] = run_input
        self._active_events[run_input.run_id] = evidence
        return result

    def investigate_directory(
        self,
        run_directory: Path,
        provider: Optional[Any] = None,
        step_callback: Optional[Callable[[str, Any], None]] = None,
    ) -> InvestigationResult:
        run = input_from_run(run_directory)
        op_dir = run_directory / "operational"
        evidence, hashes = load_evidence(run, op_dir)
        return self.start_investigation(
            run_input=run,
            evidence=evidence,
            input_hashes=hashes,
            step_callback=step_callback,
            provider=provider,
        )

    def get_result(self, run_id: str) -> Optional[InvestigationResult]:
        return self._active_results.get(run_id)

    def get_state(self, run_id: str) -> Dict[str, Any]:
        result = self._active_results.get(run_id)
        if not result:
            return {"status": "UNKNOWN", "run_id": run_id}
        return {
            "run_id": result.run_id,
            "scenario_id": result.scenario_id,
            "terminal_state": result.terminal_state.value if hasattr(result.terminal_state, "value") else str(result.terminal_state),
            "selected_hypothesis_id": result.selected_hypothesis_id,
            "discovery_mode": result.discovery_mode,
            "candidate_count": len(result.candidate_relationships),
            "next_best_evidence_count": len(result.next_best_evidence),
            "ranked_hypotheses_count": len(result.ranked_hypotheses),
        }

    def get_ranked_hypotheses(self, run_id: str) -> HypothesisRankingContract:
        result = self._active_results.get(run_id)
        if not result:
            return HypothesisRankingContract(
                metadata=HypothesisRankingMetadata(run_id=run_id, revision=1),
                spec=HypothesisRankingSpec(hypotheses=[]),
            )

        items: List[RankedHypothesisItem] = []
        for idx, h in enumerate(result.ranked_hypotheses, 1):
            role = "LEADING" if idx == 1 and h.status != KnowledgeState.REJECTED else "COMPETING"
            if h.status == KnowledgeState.REJECTED:
                role = "WEAK"

            items.append(
                RankedHypothesisItem(
                    hypothesis_id=h.hypothesis_id,
                    rank=idx,
                    score=h.hypothesis_confidence,
                    state=h.status.value if hasattr(h.status, "value") else str(h.status),
                    role=role,
                    causal_role=h.causal_role.value if hasattr(h.causal_role, "value") else str(h.causal_role),
                    root_entity=h.candidate_root_entity,
                    canonical_root_entity=h.canonical_root_entity,
                    domain=h.candidate_root_domain,
                    statement=h.statement,
                    explanation_coverage=h.explanation_coverage,
                    supporting_evidence=h.supporting_evidence,
                    contradicting_evidence=h.contradicting_evidence,
                    missing_evidence=h.missing_evidence,
                    score_components=h.score_dimensions,
                    provenance=[str(p) for p in h.knowledge_relationships_used],
                )
            )

        leading_id = result.selected_hypothesis_id or (items[0].hypothesis_id if items else None)
        return HypothesisRankingContract(
            metadata=HypothesisRankingMetadata(run_id=run_id, revision=1),
            spec=HypothesisRankingSpec(
                hypotheses=items,
                leading_hypothesis_id=leading_id,
                convergence_reached=result.terminal_state == Terminal.EXPLAINED,
            ),
        )

    def get_knowledge_gaps(self, run_id: str) -> Dict[str, Any]:
        result = self._active_results.get(run_id)
        if not result:
            return {"gaps": [], "residuals": [], "discovery_mode": False}
        return {
            "discovery_mode": result.discovery_mode,
            "terminal_state": result.terminal_state.value if hasattr(result.terminal_state, "value") else str(result.terminal_state),
            "candidate_relationships": [r.model_dump(mode="python") for r in result.candidate_relationships],
            "next_best_evidence": [e.model_dump(mode="python") for e in result.next_best_evidence],
            "diagnostics": result.diagnostics,
        }

    def get_domain_attribution(self, run_id: str) -> Dict[str, Any]:
        result = self._active_results.get(run_id)
        if not result or not result.ranked_hypotheses:
            return {"primary_domain": "unknown", "domains": []}
        leading = result.ranked_hypotheses[0]
        return {
            "primary_domain": leading.candidate_root_domain,
            "root_entity": leading.canonical_root_entity,
            "confidence": leading.hypothesis_confidence,
            "causal_role": leading.causal_role.value if hasattr(leading.causal_role, "value") else str(leading.causal_role),
        }

    def get_affected_services(self, run_id: str) -> List[Dict[str, Any]]:
        result = self._active_results.get(run_id)
        if not result:
            return []
        return [dict(i) if isinstance(i, dict) else i.model_dump(mode="python") for i in result.impact]


default_fikracore_adapter = FikraCoreAdapter()
