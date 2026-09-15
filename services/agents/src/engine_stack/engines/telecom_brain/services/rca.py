"""RCA triage service built on top of correlation output."""

from __future__ import annotations

from typing import Any

from storyteller.conversation.service import (
    ConversationError,
    ConversationService,
    IncidentContextRequired,
    IncidentNotFound,
    extract_incident_ref,
)
from storyteller.conversation.session import SessionStore
from storyteller.knowledge.gbrain_client import GbrainClient
from storyteller.knowledge.mobile_core_knowledge import MobileCoreKnowledge

from ..engine_context import TelecomContext
from ..models import FCAPSClassification, RCAHypothesis, RecommendedAction, TelecomRequest, TelecomResult, TelecomTrace
from .correlation import CorrelationService


class RCAService:
    id = "rca"

    def __init__(
        self,
        *,
        correlation_service: CorrelationService | None = None,
        conversation: ConversationService | None = None,
    ) -> None:
        self.correlation_service = correlation_service or CorrelationService()
        self._conversation = conversation

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        if any(term in query for term in ("root cause", "rca", "likely cause", "what caused", "why did", "why is")):
            score += 0.55
        if any(term in query for term in ("diagnostic", "triage", "missing proof", "next step")):
            score += 0.25
        if request.alarms or request.context.get("correlation_results"):
            score += 0.25
        if extract_incident_ref(request.query):
            score += 0.2
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        incident_story = self._story_from_incident(request)
        if incident_story is not None:
            return self._from_story(incident_story)

        correlation_payload = request.context.get("correlation_results")
        if correlation_payload is None and request.alarms:
            correlation_result = await self.correlation_service.handle(request, context)
            correlation_payload = correlation_result.data.get("correlation_results", [])
        if correlation_payload:
            return self._from_correlation_payload(correlation_payload)

        return TelecomResult(
            text="RCA needs an incident ID, correlation result, or alarms with evidence to triage.",
            spoken_response="RCA needs an incident ID, correlation result, or alarms with evidence to triage.",
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, warnings=["rca request lacked incident, correlation, or alarm evidence"]),
        )

    def _story_from_incident(self, request: TelecomRequest) -> dict[str, Any] | None:
        incident_id = (
            extract_incident_ref(request.query)
            or request.context.get("path_incident_id")
            or request.context.get("incident_id")
        )
        conversation = self._get_conversation()
        if not incident_id and request.session_id:
            incident_id = conversation.sessions.active_incident(request.session_id)
        if not incident_id and not request.alarms and not request.context.get("correlation_results"):
            incident_id = "mobile-core/incidents/amf-overload-2026-08-09"
        if not incident_id:
            return None
        try:
            story, _intent, _answer, _resolved = conversation.ask(
                path_incident_id=incident_id,
                message=request.query,
                session_id=request.session_id,
                intent="root_cause",
            )
            return story.to_dict()
        except (IncidentContextRequired, IncidentNotFound, ConversationError):
            return None

    def _from_story(self, story: dict[str, Any]) -> TelecomResult:
        root = story.get("root_cause")
        hypotheses = []
        for item in story.get("hypotheses", []):
            hypothesis = item.get("hypothesis", {}) if isinstance(item, dict) else {}
            missing = list(story.get("unresolved_questions", []))
            if item.get("status") != "confirmed" and "root cause is not confirmed" not in missing:
                missing.append("root cause is not confirmed")
            hypotheses.append(
                RCAHypothesis(
                    cause=str(hypothesis.get("value") or "Unspecified hypothesis"),
                    confidence=float(item.get("score") or 0.0),
                    supporting_evidence=[str(e.get("value")) for e in item.get("evidence", []) if isinstance(e, dict)],
                    evidence_against=[],
                    missing_proof=missing,
                    next_diagnostic_step=self._next_step(missing),
                )
            )

        if root:
            text = f"Confirmed root cause: {root.get('value')}"
            spoken = text
        else:
            text = self._format_hypotheses(hypotheses)
            spoken = "Root cause is not confirmed. I found leading hypotheses and missing proof."

        return TelecomResult(
            text=text,
            spoken_response=spoken,
            service_id=self.id,
            trace=TelecomTrace(
                selected_service=self.id,
                provenance=["storyteller.ConversationService", "storyteller.reasoning.pipeline", "mcp_hub.gbrain"],
            ),
            rca_hypotheses=hypotheses,
            recommended_actions=[self._recommended_action(hypotheses)],
            fcaps=[FCAPSClassification.FAULT, FCAPSClassification.PERFORMANCE],
            data={"story": story, "root_cause_confirmed": bool(root)},
        )

    def _from_correlation_payload(self, payload: list[dict[str, Any]]) -> TelecomResult:
        hypotheses = [self._hypothesis_from_correlation(item) for item in payload]
        text = self._format_hypotheses(hypotheses)
        return TelecomResult(
            text=text,
            spoken_response="Root cause is not confirmed from correlation alone. I prepared RCA hypotheses and the next proof to gather.",
            service_id=self.id,
            trace=TelecomTrace(
                selected_service=self.id,
                provenance=["correlation.CorrelationEngine"],
                warnings=["Correlation output is RCA evidence, not confirmed root cause."],
            ),
            rca_hypotheses=hypotheses,
            recommended_actions=[self._recommended_action(hypotheses)],
            fcaps=[FCAPSClassification.FAULT, FCAPSClassification.PERFORMANCE],
            data={"root_cause_confirmed": False, "correlation_results": payload},
        )

    @staticmethod
    def _hypothesis_from_correlation(item: dict[str, Any]) -> RCAHypothesis:
        services = item.get("services") or []
        domains = item.get("domains") or []
        service_text = ", ".join(services) if services else "unmapped service"
        domain_text = ", ".join(domains) if domains else "unknown domain"
        reasons = [str(reason) for reason in item.get("reasons", [])]
        evidence = [*reasons]
        for source_id in item.get("alarms", []):
            evidence.append(f"alarm {source_id}")
        for source_id in item.get("evidence", []):
            evidence.append(f"evidence {source_id}")

        missing = RCAService._missing_proof(item)
        against = []
        if item.get("intent_status") == "not_matched":
            against.append("no matching service intent was found")
        if item.get("outcome") == "standalone":
            against.append("only standalone correlation support is present")

        return RCAHypothesis(
            cause=f"{item.get('scope', 'unclassified')} correlation impacting {service_text} across {domain_text}",
            confidence=min(float(item.get("score") or 0.0) / 100.0, 1.0),
            supporting_evidence=evidence,
            evidence_against=against,
            missing_proof=missing,
            next_diagnostic_step=RCAService._next_step(missing),
        )

    @staticmethod
    def _missing_proof(item: dict[str, Any]) -> list[str]:
        reasons = " ".join(str(reason).lower() for reason in item.get("reasons", []))
        missing = ["confirmed root-cause evidence"]
        if "kpi breach" not in reasons:
            missing.append("corroborating KPI breach")
        if "independent operational evidence" not in reasons:
            missing.append("independent log, trace, ticket, or dashboard evidence")
        if item.get("intent_status") != "violated":
            missing.append("validated service intent violation")
        return missing

    @staticmethod
    def _format_hypotheses(hypotheses: list[RCAHypothesis]) -> str:
        if not hypotheses:
            return "Root cause is not confirmed; no hypotheses are available yet."
        lines = ["**RCA Triage**", "Root cause is not confirmed unless explicitly stated by evidence."]
        for hypothesis in hypotheses:
            lines.append(f"- Hypothesis: {hypothesis.cause} | confidence={hypothesis.confidence:.2f}")
            if hypothesis.supporting_evidence:
                lines.append(f"  - Supports: {'; '.join(hypothesis.supporting_evidence[:4])}")
            if hypothesis.evidence_against:
                lines.append(f"  - Against: {'; '.join(hypothesis.evidence_against[:3])}")
            if hypothesis.missing_proof:
                lines.append(f"  - Missing proof: {'; '.join(hypothesis.missing_proof[:4])}")
            if hypothesis.next_diagnostic_step:
                lines.append(f"  - Next step: {hypothesis.next_diagnostic_step}")
        return "\n".join(lines)

    @staticmethod
    def _next_step(missing: list[str]) -> str:
        if any("KPI" in item for item in missing):
            return "Query the affected service KPI window around the alarm burst."
        if any("intent" in item for item in missing):
            return "Validate service intent state for the affected procedure."
        if any("log" in item or "trace" in item or "dashboard" in item for item in missing):
            return "Collect independent logs, traces, tickets, or dashboard panel evidence."
        return "Ask the owning domain team to confirm the leading hypothesis with source evidence."

    @staticmethod
    def _recommended_action(hypotheses: list[RCAHypothesis]) -> RecommendedAction:
        if hypotheses:
            description = hypotheses[0].next_diagnostic_step or "Gather missing proof for the leading RCA hypothesis."
        else:
            description = "Gather correlation, telemetry, and topology evidence before RCA confirmation."
        return RecommendedAction(
            action_type="diagnostic next step",
            description=description,
            requires_approval=False,
        )

    def _get_conversation(self) -> ConversationService:
        if self._conversation is None:
            self._conversation = self._build_conversation()
        return self._conversation

    @staticmethod
    def _build_conversation() -> ConversationService:
        from storyteller.conversation.session import default_session_store
        gbrain = GbrainClient()
        knowledge = MobileCoreKnowledge(gbrain)
        return ConversationService(knowledge, sessions=default_session_store)
