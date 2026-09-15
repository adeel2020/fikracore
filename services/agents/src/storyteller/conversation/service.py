"""Conversational storyteller service.

Orchestrates:  IncidentContext → IncidentStory → per-intent answer.

Incident resolution is strict and never guesses:

    1. path incident_id  (explicit in the URL)
    2. message incident reference (an incident slug mentioned in the text)
    3. session active_incident_id (the incident from a prior turn)
    4. otherwise → ``IncidentContextRequired`` (a clear, explicit response)

We NEVER pick an incident by semantic similarity. If the resolved reference
does not exist in the graph, we return ``IncidentNotFound`` rather than
silently selecting a similar incident.
"""

from __future__ import annotations

import logging
import re

from ..knowledge.context import IncidentContext
from ..knowledge.mobile_core_knowledge import MobileCoreKnowledge
from ..reasoning.pipeline import build_incident_story, build_story_response
from ..reasoning.story import IncidentStory, StoryResponse
from .intents import INTENTS, classify_intent, render_answer
from .session import SessionStore

logger = logging.getLogger(__name__)

# Incident slug formats. The canonical form is incidents/<domain>/<id>.
# <domain>/incidents/<id> remains accepted as a legacy alias.
_SLUG_RE = re.compile(r"((?:incidents/[A-Za-z0-9_-]+|[A-Za-z0-9_-]+/incidents)/[A-Za-z0-9._\-]+)")

# Accepted shorthand: a bare incident id like "INC-123" or "amf-overload-2026-08-09".
_BARE_ID_RE = re.compile(r"\b((?:INC|inc|id)[-_]?\d{1,6}|[a-z0-9]+(?:-[a-z0-9]+)+)\b")


class IncidentContextRequired(Exception):
    """No incident could be resolved from path, message, or session."""


class IncidentNotFound(Exception):
    """A resolved incident id does not exist in the graph."""


class ConversationError(Exception):
    """Generic conversation-layer error."""


def extract_incident_ref(message: str) -> str | None:
    """Pull a full slug (preferred) or bare incident id from the message."""
    match = _SLUG_RE.search(message)
    if match:
        return match.group(1).rstrip(".,;:!?")
    match = _BARE_ID_RE.search(message)
    if match:
        return match.group(1).rstrip(".,;:!?")
    return None


class ConversationService:
    """Stateless orchestrator; the only mutable state is the session store."""

    def __init__(
        self,
        knowledge: MobileCoreKnowledge,
        sessions: SessionStore | None = None,
        *,
        synthesize: bool = True,
    ) -> None:
        self.knowledge = knowledge
        self.sessions = sessions or SessionStore()
        self.synthesize = synthesize

    # ------------------------------------------------------------------
    # Incident resolution (strict order — no semantic guessing).
    # ------------------------------------------------------------------
    def resolve_incident(
        self,
        *,
        path_incident_id: str | None,
        message: str,
        session_id: str | None,
    ) -> str:
        """Resolve the incident id following the documented priority order."""
        if path_incident_id:
            return path_incident_id

        msg_ref = extract_incident_ref(message) if message else None
        if msg_ref:
            return msg_ref

        if session_id:
            active = self.sessions.active_incident(session_id)
            if active:
                return active

        raise IncidentContextRequired(
            "No incident context found. Please provide an incident id in the "
            "URL, mention it in your message, or ask a follow-up within an "
            "active session."
        )

    # ------------------------------------------------------------------
    # Story construction.
    # ------------------------------------------------------------------
    def get_context(self, incident_id: str) -> IncidentContext:
        ctx = self.knowledge.get_incident_context(incident_id)
        if not ctx.incident:
            trace = "; ".join(ctx.lookup_trace[:8])
            detail = f" Lookup attempts: {trace}." if trace else ""
            raise IncidentNotFound(f"Incident '{incident_id}' was not found in the knowledge graph.{detail}")
        return ctx

    def get_story(self, incident_id: str, *, synthesize: bool | None = None) -> IncidentStory:
        ctx = self.get_context(incident_id)
        story = build_incident_story(ctx)
        return story

    def get_story_response(
        self, incident_id: str, *, synthesize: bool | None = None
    ) -> StoryResponse:
        ctx = self.get_context(incident_id)
        return build_story_response(ctx, synthesize=self.synthesize if synthesize is None else synthesize)

    # ------------------------------------------------------------------
    # Ask: resolve -> story -> deterministic per-intent answer.
    # ------------------------------------------------------------------
    def ask(
        self,
        *,
        path_incident_id: str | None,
        message: str,
        session_id: str | None = None,
        intent: str | None = None,
    ) -> tuple[IncidentStory, str, str, str | None]:
        """Return ``(story, intent, answer, incident_id)``.

        ``answer`` is always the deterministic render of the structured story.
        The LLM is not required and never replaces the structured story.
        """
        incident_id = self.resolve_incident(
            path_incident_id=path_incident_id, message=message, session_id=session_id
        )
        story = self.get_story(incident_id)

        effective_intent = intent if intent else classify_intent(message)
        if effective_intent not in INTENTS:
            raise ConversationError(
                f"Unknown intent '{effective_intent}'. Supported intents: {', '.join(INTENTS)}"
            )

        # Record the active incident so follow-ups can omit the id.
        if session_id:
            self.sessions.set_active_incident(session_id, incident_id)
            self.sessions.get(session_id).last_intent = effective_intent

        answer = render_answer(effective_intent, story)
        return story, effective_intent, answer, incident_id
