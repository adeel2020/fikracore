"""Storytelling service wrapper over the existing storyteller stack."""

from __future__ import annotations

import re
from typing import Any

from storyteller.conversation.service import (
    ConversationError,
    ConversationService,
    IncidentContextRequired,
    IncidentNotFound,
    extract_incident_ref,
)
from storyteller.conversation.intents import curate_spoken_text, render_spoken_answer
from storyteller.conversation.session import SessionStore
from storyteller.knowledge.gbrain_client import GbrainClient
from storyteller.knowledge.mobile_core_knowledge import MobileCoreKnowledge
from storyteller.reasoning.story import IncidentStory

from ..engine_context import TelecomContext
from ..models import FCAPSClassification, IncidentRef, TelecomRequest, TelecomResult, TelecomTrace
from ..models import StoryAudience
from .narrative import narrative_from_story
from .grafana_evidence import GrafanaEvidenceProvider
from .visual_explanation import VisualExplanationService


class StorytellingService:
    id = "storytelling"

    def __init__(self, conversation: ConversationService | None = None) -> None:
        self._conversation = conversation

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()

        # 1. Negative story intent: user explicitly rejects or opts out of story
        if re.search(r"\b(do\s*n['o]?t|no|stop|never|without|not\s+need|don'?t\s+need|don'?t\s+want|dislike|skip)\b.*\b(story|stories|narrative)\b", query):
            return 0.0

        # 2. Incident registry query: user is asking to list, show, or browse incidents
        if ("incident" in query or "incidents" in query) and any(w in query for w in ("list", "all", "queue", "overview", "registry", "browse", "status")):
            return 0.0

        score = 0.0
        explicit_id = extract_incident_ref(request.query)
        context_id = request.context.get("incident_id")
        intent = request.context.get("intent")

        has_story_keywords = bool(re.search(
            r"\b(tell\s+(me\s+)?(the\s+|a\s+|about\s+)?(incident\s+)?story|narrat|what\s+happened|elaborate|go\s+deeper|explain\s+incident|walk\s+me\s+through|story)\b",
            query,
        ))

        # Explicit incident ID present in current query
        if explicit_id:
            score += 0.40
        # If context has an incident ID from session, only boost if this turn is asking for storytelling/deep dive
        elif context_id and (has_story_keywords or intent in ("story", "technical", "evidence", "timeline", "remediation", "why")):
            score += 0.35

        if has_story_keywords:
            score += 0.45
        elif any(term in query for term in ("timeline", "chronolog", "evidence", "more details")):
            score += 0.25

        if intent in ("story", "technical", "evidence", "timeline", "remediation", "why"):
            score += 0.40

        if any(term in query for term in ("rca", "root cause", "remediation", "recovery")):
            score += 0.15

        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        conversation = self._get_conversation()
        path_incident_id = (
            request.context.get("path_incident_id")
            or request.context.get("incident_id")
            or extract_incident_ref(request.query)
        )
        if not path_incident_id and request.session_id:
            path_incident_id = conversation.sessions.active_incident(request.session_id)
        if not path_incident_id:
            path_incident_id = "mobile-core/incidents/amf-overload-2026-08-09"

        requested_intent = request.context.get("intent")

        try:
            story, intent, answer, incident_id = conversation.ask(
                path_incident_id=path_incident_id,
                message=request.query,
                session_id=request.session_id,
                intent=requested_intent,
            )
            story_payload = story.to_dict()
            spoken_response = self._spoken_response(intent, story, answer)
            data = {"intent": intent, "story": story_payload}
            if isinstance(story, IncidentStory):
                narrative = narrative_from_story(story, intent=intent, written_story=answer)
                visual_explanation = VisualExplanationService().build(narrative)
                telemetry_evidence = self._live_telemetry_evidence(request, context, incident_id)
                data.update(
                    {
                        "narrative": narrative.model_dump(mode="json"),
                        "visual_explanation": visual_explanation.model_dump(mode="json"),
                        "telemetry_evidence": telemetry_evidence,
                    }
                )
            return TelecomResult(
                text=answer,
                spoken_response=spoken_response,
                service_id=self.id,
                trace=TelecomTrace(
                    selected_service=self.id,
                    provenance=["storyteller.ConversationService", "storyteller.MobileCoreKnowledge", "mcp_hub.gbrain"],
                ),
                incidents=[self._incident_ref(incident_id, story_payload)],
                fcaps=[FCAPSClassification.FAULT, FCAPSClassification.PERFORMANCE],
                data=data,
            )
        except IncidentContextRequired as exc:
            return self._needs_context(str(exc))
        except IncidentNotFound as exc:
            return self._not_found(str(exc))
        except ConversationError as exc:
            return self._needs_context(str(exc))

    def _get_conversation(self) -> ConversationService:
        if self._conversation is None:
            self._conversation = self._build_conversation()
        return self._conversation

    def build_payload(
        self,
        incident_id: str,
        *,
        message: str | None = None,
        session_id: str | None = None,
        intent: str = "executive",
    ) -> dict[str, Any]:
        """Build the same Storyteller payload used by chat clients.

        This keeps downstream copilots additive: they can embed Storyteller's
        narrative and visual explanation contract without reimplementing it.
        """
        story, resolved_intent, answer, resolved_id = self._get_conversation().ask(
            path_incident_id=incident_id,
            message=message or f"Create an executive summary for {incident_id}.",
            session_id=session_id,
            intent=intent,
        )
        story_payload = story.to_dict()
        narrative = narrative_from_story(
            story,
            intent=resolved_intent,
            written_story=answer,
            audience=self._audience_from_intent(resolved_intent),
        )
        visual_explanation = VisualExplanationService().build(narrative)
        return {
            "incident_id": resolved_id,
            "intent": resolved_intent,
            "answer": answer,
            "spoken_answer": self._spoken_response(resolved_intent, story, answer),
            "story": story_payload,
            "narrative": narrative.model_dump(mode="json"),
            "visual_explanation": visual_explanation.model_dump(mode="json"),
            "telemetry_evidence": [],
        }

    @staticmethod
    def _build_conversation() -> ConversationService:
        from storyteller.conversation.session import default_session_store
        gbrain = GbrainClient()
        knowledge = MobileCoreKnowledge(gbrain)
        return ConversationService(knowledge, sessions=default_session_store)

    @staticmethod
    def _incident_ref(incident_id: str | None, story: dict[str, Any]) -> IncidentRef:
        return IncidentRef(
            id=incident_id or story.get("incident_id") or "unknown",
            title=story.get("summary") or None,
            status=story.get("status") or None,
            severity=story.get("severity") or None,
            source="storyteller",
        )

    @staticmethod
    def _spoken_response(intent: str, story: Any, answer: str) -> str:
        try:
            return render_spoken_answer(intent, story)
        except Exception:
            return curate_spoken_text(answer)

    @staticmethod
    def _audience_from_intent(intent: str) -> StoryAudience:
        if intent == "noc_brief":
            return StoryAudience.NOC_ENGINEER
        if intent == "rca_lead_brief":
            return StoryAudience.RCA_LEAD
        if intent == "customer_update":
            return StoryAudience.CUSTOMER
        if intent == "post_incident_review":
            return StoryAudience.POST_INCIDENT_REVIEW
        return StoryAudience.EXECUTIVE

    @staticmethod
    def _live_telemetry_evidence(
        request: TelecomRequest,
        context: TelecomContext,
        incident_id: str | None,
    ) -> list[dict[str, Any]]:
        if not incident_id or not request.context.get("include_live_telemetry"):
            return []
        try:
            provider = GrafanaEvidenceProvider(context.mcp_hub)
            return [item.to_dict() for item in provider.evidence_for_incident(incident_id, query=request.query, limit=8)]
        except Exception:
            return []

    def _needs_context(self, message: str) -> TelecomResult:
        return TelecomResult(
            text=message,
            spoken_response="Please provide an incident ID so I can tell the incident story.",
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, warnings=[message]),
        )

    def _not_found(self, message: str) -> TelecomResult:
        return TelecomResult(
            text=message,
            spoken_response="I could not find that incident in the local telecom knowledge graph.",
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, warnings=[message]),
        )
