"""Visual explanation payloads for professional incident narratives."""

from __future__ import annotations

from ..models import (
    EvidenceGrade,
    IncidentNarrative,
    VisualExplanation,
    VisualWidget,
    VisualWidgetType,
)


class VisualExplanationService:
    """Build frontend-ready visual widgets from an IncidentNarrative."""

    id = "visual_explanation"

    def build(self, narrative: IncidentNarrative) -> VisualExplanation:
        widgets = [
            self._domain_impact_widget(narrative),
            self._evidence_matrix_widget(narrative),
            self._timeline_widget(narrative),
            self._causal_chain_widget(narrative),
            self._next_action_widget(narrative),
        ]
        widgets = [widget for widget in widgets if widget is not None]
        primary = widgets[0].type if widgets else None
        return VisualExplanation(
            incident_id=narrative.incident_id,
            audience=narrative.audience,
            primary_widget=primary,
            widgets=widgets,
            metadata={
                "source": "IncidentNarrative",
                "presentation_modes": ["inline", "hud_highlight", "drawer", "investigation"],
            },
        )

    def _domain_impact_widget(self, narrative: IncidentNarrative) -> VisualWidget | None:
        if not (narrative.domains or narrative.services or narrative.components):
            return None
        nodes = [
            *[{"id": f"domain:{domain}", "label": domain, "kind": "domain"} for domain in narrative.domains],
            *[{"id": f"service:{service}", "label": service, "kind": "service"} for service in narrative.services],
            *[{"id": f"component:{component}", "label": component, "kind": "component"} for component in narrative.components],
        ]
        links = []
        for domain in narrative.domains:
            for service in narrative.services:
                links.append({"source": f"domain:{domain}", "target": f"service:{service}", "relationship": "contributes_to"})
        for service in narrative.services:
            for component in narrative.components:
                links.append({"source": f"service:{service}", "target": f"component:{component}", "relationship": "impacts"})
        return VisualWidget(
            id="visual-domain-impact",
            title="Domain Impact",
            type=VisualWidgetType.DOMAIN_IMPACT_MAP,
            data={"nodes": nodes, "links": links},
            confidence=self._average_claim_confidence(narrative),
            provenance=narrative.provenance[:8],
            supports_claim_ids=[claim.id for claim in narrative.claims[:8]],
        )

    def _evidence_matrix_widget(self, narrative: IncidentNarrative) -> VisualWidget | None:
        if not narrative.claims:
            return None
        rows = [
            {
                "claim_id": claim.id,
                "statement": claim.statement,
                "grade": claim.grade.value,
                "confidence": claim.confidence,
                "fcaps": [item.value for item in claim.fcaps],
            }
            for claim in narrative.claims
        ]
        counts = {grade.value: 0 for grade in EvidenceGrade}
        for claim in narrative.claims:
            counts[claim.grade.value] += 1
        return VisualWidget(
            id="visual-evidence-matrix",
            title="Evidence Matrix",
            type=VisualWidgetType.EVIDENCE_CONFIDENCE_MATRIX,
            data={"rows": rows, "grade_counts": counts},
            confidence=self._average_claim_confidence(narrative),
            provenance=narrative.provenance[:10],
            supports_claim_ids=[claim.id for claim in narrative.claims],
        )

    def _timeline_widget(self, narrative: IncidentNarrative) -> VisualWidget | None:
        if not narrative.timeline:
            return None
        return VisualWidget(
            id="visual-timeline",
            title="Timeline",
            type=VisualWidgetType.TIMELINE,
            data={"events": narrative.timeline},
            confidence=self._average_claim_confidence(narrative),
            provenance=narrative.provenance[:8],
            supports_claim_ids=[claim.id for claim in narrative.claims if "kpi" in claim.id or "summary" in claim.id],
        )

    def _causal_chain_widget(self, narrative: IncidentNarrative) -> VisualWidget | None:
        steps = narrative.causal_chain
        if not steps and narrative.rca_status:
            steps = [narrative.impact_summary, narrative.rca_status]
        steps = [step for step in steps if step]
        if not steps:
            return None
        return VisualWidget(
            id="visual-causal-chain",
            title="Causal Chain",
            type=VisualWidgetType.CAUSAL_CHAIN,
            data={"steps": [{"id": f"step-{idx}", "label": step} for idx, step in enumerate(steps, start=1)]},
            confidence=self._average_claim_confidence(narrative),
            provenance=narrative.provenance[:8],
            supports_claim_ids=[claim.id for claim in narrative.claims if claim.grade != EvidenceGrade.MISSING_EVIDENCE],
        )

    def _next_action_widget(self, narrative: IncidentNarrative) -> VisualWidget | None:
        if not narrative.next_actions and not narrative.open_questions:
            return None
        return VisualWidget(
            id="visual-next-actions",
            title="Next Actions",
            type=VisualWidgetType.NEXT_ACTION_TREE,
            data={
                "actions": [action.model_dump() for action in narrative.next_actions],
                "questions": narrative.open_questions,
            },
            confidence=self._average_claim_confidence(narrative),
            provenance=narrative.provenance[:5],
            supports_claim_ids=[claim.id for action in narrative.next_actions for claim in narrative.claims if claim.id in action.supports_claim_ids],
        )

    @staticmethod
    def _average_claim_confidence(narrative: IncidentNarrative) -> float:
        if not narrative.claims:
            return 0.0
        return sum(claim.confidence for claim in narrative.claims) / len(narrative.claims)

