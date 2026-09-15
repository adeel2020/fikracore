"""FCAPS learning service for reviewed enrichment candidates."""

from __future__ import annotations

from ..engine_context import TelecomContext
from ..models import FCAPSClassification, RecommendedAction, TelecomRequest, TelecomResult, TelecomTrace


class FCAPSLearningService:
    id = "fcaps_learning"

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        if any(term in query for term in ("fcaps", "learn", "learning", "what did we learn", "asset gap")):
            score += 0.55
        if any(term in query for term in ("missing playbook", "missing runbook", "dashboard", "grafana query")):
            score += 0.3
        if request.context.get("story") or request.context.get("correlation_results"):
            score += 0.2
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        classifications = self._classify(request)
        gaps = self._learning_gaps(request)
        actions = [
            RecommendedAction(action_type="learning candidate", description=gap, requires_approval=False)
            for gap in gaps
        ]
        projection = {
            "kind": "fcaps_learning_candidate",
            "fcaps": [item.value for item in classifications],
            "gaps": gaps,
            "summary": "Reviewed learning candidate; raw incident and telemetry records remain in source systems.",
        }
        try:
            await context.mcp_hub.call_tool("gbrain", "put_learning_candidate", projection)
        except Exception:
            projection["projection_status"] = "skipped_or_unavailable"
        text = self._format(classifications, gaps)
        return TelecomResult(
            text=text,
            spoken_response=f"Classified the learning through {len(classifications)} FCAPS lens areas and proposed {len(gaps)} reviewed candidates.",
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, provenance=["capability_registry.fcaps_learning", "mcp_hub.gbrain"]),
            recommended_actions=actions,
            fcaps=classifications,
            data={"learning_candidate": projection},
        )

    @staticmethod
    def _classify(request: TelecomRequest) -> list[FCAPSClassification]:
        text = f"{request.query} {request.context}".lower()
        classes = []
        if any(term in text for term in ("alarm", "fault", "down", "failure", "timeout", "crash")):
            classes.append(FCAPSClassification.FAULT)
        if any(term in text for term in ("change", "config", "mop", "rollback", "deployment")):
            classes.append(FCAPSClassification.CHANGE_REQUEST_CONFIGURATION)
        if any(term in text for term in ("charging", "billing", "quota", "accounting")):
            classes.append(FCAPSClassification.ACCOUNTING)
        if any(term in text for term in ("kpi", "latency", "throughput", "cssr", "success rate", "cpu")):
            classes.append(FCAPSClassification.PERFORMANCE)
        if any(term in text for term in ("security", "auth", "certificate", "attack", "policy")):
            classes.append(FCAPSClassification.SECURITY)
        return classes or [FCAPSClassification.FAULT]

    @staticmethod
    def _learning_gaps(request: TelecomRequest) -> list[str]:
        text = f"{request.query} {request.context}".lower()
        gaps = []
        for label in ("playbook", "runbook", "grafana query", "dashboard panel", "topology relation", "intent mapping"):
            if f"missing {label}" in text or label in text:
                gaps.append(f"review missing {label}")
        if not gaps:
            gaps.append("review whether a playbook, runbook, Grafana query, dashboard panel, topology relation, or intent mapping is missing")
        return gaps

    @staticmethod
    def _format(classes: list[FCAPSClassification], gaps: list[str]) -> str:
        return "\n".join([
            "**FCAPS Learning**",
            "- Lens: " + ", ".join(item.value for item in classes),
            *[f"- Candidate: {gap}" for gap in gaps],
        ])
