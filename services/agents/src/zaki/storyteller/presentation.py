"""Multi-Depth Presentation Projector for Zaki Storyteller."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..domain.contracts.hypothesis import HypothesisRankingContract
from ..domain.contracts.incident import IncidentContextContract
from ..domain.contracts.intent import OperatorIntentContract
from ..domain.contracts.story import IncidentStoryContract, StoryStatement
from ..domain.enums import PresentationDepth, StatementProvenance


class PresentationProjector:
    """Projects authoritative backend run state into 3 presentation depths."""

    @staticmethod
    def build_story(
        incident: IncidentContextContract,
        hypotheses: HypothesisRankingContract,
        inv_result: Any,
        intent: Optional[OperatorIntentContract] = None,
        gaps: Optional[Dict[str, Any]] = None,
        depth: PresentationDepth = PresentationDepth.OPERATOR,
    ) -> IncidentStoryContract:
        leading = None
        competing = []
        for idx, h in enumerate(hypotheses.spec.hypotheses):
            h_dict = h.model_dump(mode="python")
            if idx == 0 and h.role == "LEADING":
                leading = h_dict
            else:
                competing.append(h_dict)

        title = f"Outage Analysis: {incident.title}"
        summary = (
            f"FikraCore investigation completed with terminal state '{inv_result.terminal_state}'. "
            f"Leading root entity candidate is '{leading.get('root_entity') if leading else 'undetermined'}' "
            f"with confidence score {leading.get('score', 0.0) if leading else 0.0}."
        )

        timeline_statements: List[StoryStatement] = []
        statement_idx = 1

        # Observed evidence statements
        if hasattr(inv_result, "provenance") and inv_result.provenance:
            for prov in inv_result.provenance[:5]:
                timeline_statements.append(
                    StoryStatement(
                        statement_id=f"STMT-{statement_idx:03d}",
                        text=f"Observed operational evidence from {prov.get('domain', 'network')}: {prov.get('evidence_ids', [])}",
                        provenance=StatementProvenance.OBSERVED,
                        evidence_ids=prov.get("evidence_ids", []),
                        stage="INGESTION",
                    )
                )
                statement_idx += 1

        # Inferred hypothesis statements
        if leading:
            timeline_statements.append(
                StoryStatement(
                    statement_id=f"STMT-{statement_idx:03d}",
                    text=f"Inferred leading causal root at '{leading.get('root_entity')}' ({leading.get('domain')}) supported by {len(leading.get('supporting_evidence', []))} signals.",
                    provenance=StatementProvenance.INFERRED,
                    source_entity=leading.get("root_entity"),
                    domain=leading.get("domain"),
                    evidence_ids=leading.get("supporting_evidence", []),
                    confidence=leading.get("score", 0.0),
                    stage="HYPOTHESIS_TESTING",
                )
            )
            statement_idx += 1

        # Gaps / Residuals
        if gaps and gaps.get("discovery_mode"):
            timeline_statements.append(
                StoryStatement(
                    statement_id=f"STMT-{statement_idx:03d}",
                    text=f"Detected unmodelled propagation. Knowledge gap identified with {len(gaps.get('candidate_relationships', []))} candidate relations.",
                    provenance=StatementProvenance.INFERRED,
                    stage="KNOWLEDGE_GAP_DETECTION",
                )
            )

        # Technical details breakdown
        technical_details = {
            "score_dimensions": leading.get("score_components", {}) if leading else {},
            "diagnostics": getattr(inv_result, "diagnostics", {}),
            "causal_event_graph_nodes": len(getattr(inv_result, "causal_event_graph", {}).get("nodes", [])) if isinstance(getattr(inv_result, "causal_event_graph", None), dict) else 0,
        }

        # Service impact
        impact_data = {
            "affected_services": getattr(inv_result, "impact", []),
            "blast_radius_summary": f"Service degradation identified across {leading.get('domain', 'telecom')} domain." if leading else "Blast radius evaluation complete.",
        }

        next_action = "Review leading hypothesis evidence basis and authorize suggested next-best verification."
        if gaps and gaps.get("discovery_mode"):
            next_action = "Inspect proposed candidate relationships and submit operator validation decision."

        return IncidentStoryContract(
            incident_id=incident.incident_id,
            run_id=inv_result.run_id,
            presentation_depth=depth,
            title=title,
            summary=summary,
            service_impact=impact_data,
            leading_hypothesis=leading or {},
            competing_hypotheses=competing,
            correlation_narrative={"stage": "CONVERGENCE", "message": summary},
            timeline_statements=timeline_statements,
            next_best_action=next_action,
            outcome=str(inv_result.terminal_state),
            technical_details=technical_details,
        )
