"""Voice session context.

Phase 3B: the voice session reuses the Phase 3A conversation session store.
There is NO separate incident memory — the ``VoiceSession`` is a thin wrapper
that carries a ``session_id`` and a reference to the shared
``ConversationService`` (whose ``SessionStore`` holds the active incident for
follow-up questions). It also records the last voice turn for observability.
"""

from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class VoiceSession:
    conversation: Any
    session_id: str
    last_transcript: str | None = None
    last_answer: str | None = None
    last_intent: str | None = None
    last_incident_id: str | None = None
    meta: dict[str, Any] = dataclasses.field(default_factory=dict)

    @property
    def active_incident_id(self) -> str | None:
        return self.conversation.sessions.active_incident(self.session_id)

    def remember(
        self,
        *,
        transcript: str | None,
        answer: str | None,
        intent: str | None,
        incident_id: str | None,
    ) -> None:
        self.last_transcript = transcript
        self.last_answer = answer
        self.last_intent = intent
        self.last_incident_id = incident_id


__all__ = ["VoiceSession"]
