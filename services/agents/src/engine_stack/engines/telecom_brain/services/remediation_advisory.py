"""Safe remediation advisory service."""

from __future__ import annotations

from ..engine_context import TelecomContext
from ..models import FCAPSClassification, RecommendedAction, TelecomRequest, TelecomResult, TelecomTrace


class RemediationAdvisoryService:
    id = "remediation_advisory"

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        if any(term in query for term in ("what should i do", "next step", "remediate", "remediation", "fix", "rollback", "escalate")):
            score += 0.6
        if request.rca_hypotheses if hasattr(request, "rca_hypotheses") else False:
            score += 0.2
        if request.context.get("rca_hypotheses") or request.context.get("correlation_results"):
            score += 0.2
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        actions = self._actions(request)
        text = "\n".join(["**Remediation Advisory**", *[f"- {a.action_type}: {a.description}" for a in actions]])
        return TelecomResult(
            text=text,
            spoken_response=f"I prepared {len(actions)} advisory steps. Execution still requires explicit approval where marked.",
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, warnings=["Advisory only; execution requires approval."]),
            recommended_actions=actions,
            fcaps=[FCAPSClassification.FAULT, FCAPSClassification.PERFORMANCE],
            data={"approval_required": any(action.requires_approval for action in actions)},
        )

    @staticmethod
    def _actions(request: TelecomRequest) -> list[RecommendedAction]:
        text = f"{request.query} {request.context}".lower()
        actions = [
            RecommendedAction(action_type="diagnostic next step", description="Collect KPI, log, trace, and topology evidence for the affected window.", requires_approval=False),
            RecommendedAction(action_type="pre-check", description="Validate current service health and recent change activity before remediation.", requires_approval=False),
        ]
        if "rollback" in text or "change" in text:
            actions.append(RecommendedAction(action_type="rollback suggestion", description="Prepare rollback candidate for the recent correlated change; do not execute without approval.", requires_approval=True))
        if "capacity" in text or "cpu" in text or "throughput" in text:
            actions.append(RecommendedAction(action_type="capacity action", description="Prepare scale-out or traffic-shift option for approval.", requires_approval=True))
        actions.append(RecommendedAction(action_type="escalation owner", description="Escalate to the owning domain team with correlation and RCA trace attached.", requires_approval=False))
        return actions
