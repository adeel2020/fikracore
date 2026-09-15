"""Phase 3A — conversational storyteller HTTP API.

POST /api/incidents/{incident_id}/story
POST /api/incidents/{incident_id}/ask

The structured IncidentStory is the source of truth; the LLM may optionally
synthesize prose, but answers are always generated deterministically from the
structured story when the LLM is disabled.

Endpoints are injected with a ``ConversationService`` (see ``get_service``) so
tests can substitute a fake knowledge layer.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..reasoning.story import StoryResponse
from engine_stack.engines.telecom_brain.models import StoryAudience
from engine_stack.engines.telecom_brain.services.narrative import narrative_from_story
from engine_stack.engines.telecom_brain.services.visual_explanation import VisualExplanationService
from .intents import INTENTS, render_spoken_answer
from .service import (
    ConversationError,
    ConversationService,
    IncidentContextRequired,
    IncidentNotFound,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


class StoryRequest(BaseModel):
    session_id: str | None = None
    synthesize: bool | None = None


class AskRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None
    intent: str | None = Field(default=None, max_length=40)
    include_live_telemetry: bool = False


class AskResponse(BaseModel):
    incident_id: str
    intent: str
    answer: str
    spoken_answer: str | None = None
    story: dict
    narrative: dict | None = None
    visual_explanation: dict | None = None
    telemetry_evidence: list[dict] | None = None


def _service() -> ConversationService:
    """Dependency: real service wired to gbrain. Overridden in tests."""
    from ..knowledge.gbrain_client import GbrainClient
    from ..knowledge.mobile_core_knowledge import MobileCoreKnowledge
    from .service import ConversationService
    from .session import SessionStore

    _store = getattr(_service, "_store", None)
    if _store is None:
        _store = SessionStore()
        _service._store = _store
    return ConversationService(MobileCoreKnowledge(GbrainClient()), sessions=_store)


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, IncidentContextRequired):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, IncidentNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ConversationError):
        return HTTPException(status_code=422, detail=str(exc))
    logger.error("conversation service error: %s", exc)
    return HTTPException(status_code=500, detail="Internal error building incident story.")


@router.post("/{incident_id:path}/story", response_model=StoryResponse)
async def get_story(
    incident_id: str,
    req: StoryRequest | None = None,
    svc: ConversationService = Depends(_service),
) -> StoryResponse:
    """Return the deterministic story for an incident (optionally synthesized)."""
    try:
        if not incident_id:
            raise IncidentContextRequired(
                "No incident context found. Please provide an incident id in the URL."
            )
        resp = svc.get_story_response(
            incident_id, synthesize=req.synthesize if req else None
        )
        if req and req.session_id:
            svc.sessions.set_active_incident(req.session_id, incident_id)
        return resp
    except Exception as exc:  # noqa: BLE001
        raise _map_error(exc) from exc


@router.post("/{incident_id:path}/ask", response_model=AskResponse)
async def ask(
    incident_id: str,
    req: AskRequest,
    svc: ConversationService = Depends(_service),
) -> AskResponse:
    """Answer a free-text question about an incident (or the active session's)."""
    try:
        story, intent, answer, resolved_id = svc.ask(
            path_incident_id=incident_id or None,
            message=req.message,
            session_id=req.session_id,
            intent=req.intent,
        )
        audience = _audience_from_intent(intent)
        narrative = narrative_from_story(story, intent=intent, written_story=answer, audience=audience)
        visual = VisualExplanationService().build(narrative)
        telemetry_evidence = _live_telemetry_evidence(resolved_id, req.message) if req.include_live_telemetry else None
        return AskResponse(
            incident_id=resolved_id,
            intent=intent,
            answer=answer,
            spoken_answer=render_spoken_answer(intent, story),
            story=story.to_dict(),
            narrative=narrative.model_dump(mode="json"),
            visual_explanation=visual.model_dump(mode="json"),
            telemetry_evidence=telemetry_evidence,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_error(exc) from exc


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


def _live_telemetry_evidence(incident_id: str | None, query: str) -> list[dict]:
    if not incident_id:
        return []
    try:
        from engine_stack.engines.telecom_brain.services.grafana_evidence import GrafanaEvidenceProvider

        provider = GrafanaEvidenceProvider()
        return [item.to_dict() for item in provider.evidence_for_incident(incident_id, query=query, limit=8)]
    except Exception as exc:  # noqa: BLE001 - telemetry enrichment must not break deterministic story
        logger.info("live Grafana telemetry enrichment skipped: %s", exc)
        return []


__all__ = ["INTENTS", "AskRequest", "AskResponse", "StoryRequest", "router"]
