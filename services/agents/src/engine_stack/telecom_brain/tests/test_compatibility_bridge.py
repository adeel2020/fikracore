from __future__ import annotations

import asyncio

from engine_stack.telecom_brain.models import TelecomResult, TelecomTrace
from jarvis.superpowers.telecom_brain import TelecomBrainEngine, normalize_query


class FakeCanonicalEngine:
    async def initialize(self) -> None:
        pass

    async def process(self, query, session_id=None, context=None):
        return TelecomResult(
            text="structured canonical answer",
            spoken_response="spoken canonical answer",
            service_id="storytelling",
            trace=TelecomTrace(selected_service="storytelling", service_confidence=0.9),
        )


def test_bridge_delegates_to_canonical_engine() -> None:
    bridge = TelecomBrainEngine(config=None)
    bridge._engine = FakeCanonicalEngine()

    answer = asyncio.run(bridge.process("tell the incident story", session_id="s1"))

    assert answer == "structured canonical answer"
    assert bridge.last_reply == "structured canonical answer"
    assert bridge.last_spoken_reply == "spoken canonical answer"


def test_bridge_keeps_speech_normalization_compatibility() -> None:
    assert normalize_query("show a m f and f c a p s status") == "show AMF and FCAPS status"
