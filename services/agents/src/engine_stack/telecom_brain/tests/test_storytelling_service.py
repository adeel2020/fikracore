from __future__ import annotations

from dataclasses import dataclass

import pytest

from engine_stack.telecom_brain.engine_context import create_default_context
from engine_stack.telecom_brain.models import TelecomRequest
from engine_stack.telecom_brain.services.storytelling import StorytellingService


@dataclass
class FakeStory:
    incident_id: str = "incidents/mobile-core/amf-overload"

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "summary": "AMF overload reduced registration success.",
            "status": "open",
            "severity": "critical",
        }


class FakeConversation:
    def ask(self, *, path_incident_id, message, session_id=None, intent=None):
        return FakeStory(), "story", "AMF overload reduced registration success.", "incidents/mobile-core/amf-overload"


@pytest.mark.anyio
async def test_storytelling_service_wraps_existing_conversation_service() -> None:
    service = StorytellingService(conversation=FakeConversation())
    request = TelecomRequest(
        query="tell the story for incidents/mobile-core/amf-overload",
        session_id="s1",
    )

    result = await service.handle(request, create_default_context())

    assert result.text == "AMF overload reduced registration success."
    assert result.incidents[0].id == "incidents/mobile-core/amf-overload"
    assert "storyteller.ConversationService" in result.trace.provenance


@pytest.mark.anyio
async def test_storytelling_confidence_prefers_incident_story_queries() -> None:
    confidence = await StorytellingService(conversation=FakeConversation()).can_handle(
        TelecomRequest(query="tell the incident story for incidents/mobile-core/amf-overload")
    )

    assert confidence >= 0.8
