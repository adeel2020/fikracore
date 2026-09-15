"""
Multi-turn conversation tests for M.A.R.K. Assistant.

Validates:
1. Multi-turn dialogue flow across consecutive operational questions.
2. Session memory retention (active incident, turn history, intent continuity).
3. Fast-path vs. semantic fallback routing.
4. Session isolation between different session IDs.
5. Cold cache rehydration from the database.
"""

from __future__ import annotations

import asyncio
import time
import pytest

from assistant.mark import JARVIS
from assistant.mark.action_classifier import classify_action
from assistant.mark.session import MarkSession, MarkSessionStore, default_session_store
from assistant.mark.user_actions import UserAction


@pytest.fixture
def mark_assistant():
    """Create a test JARVIS instance with an isolated session store."""
    jarvis = JARVIS()
    asyncio.run(jarvis.initialize())
    jarvis.session_store = MarkSessionStore(redis_url="redis://localhost:9999/0")  # fallback to L1+L3
    return jarvis


class TestMultiTurnDialogue:
    def test_four_turn_operational_drilldown(self, mark_assistant):
        session_id = "test_ops_dialogue_001"
        mark_assistant.session_store.clear(session_id)

        # Turn 1: Open-ended story request
        t1 = asyncio.run(mark_assistant.process("OK tell me about any story you like", session_id=session_id))
        session = mark_assistant.session_store.get(session_id)
        assert session is not None
        assert session.active_incident_id == "mobile-core/incidents/amf-overload-2026-08-09"
        assert len(session.turns) == 1
        assert "AMF" in str(t1) or "amf-overload" in str(t1)

        # Turn 2: Conversational follow-up (elaboration) without repeating incident ID
        t2 = asyncio.run(mark_assistant.process("Can you elaborate on that?", session_id=session_id))
        assert len(session.turns) == 2
        # Must NOT fall back to generic "I am online and ready" or ask which incident
        assert "I am online and ready" not in str(t2)
        assert "Which incident" not in str(t2)
        assert ("CPU" in str(t2) or "98%" in str(t2) or "AMF" in str(t2) or "overload" in str(t2).lower())

        # Turn 3: Evidence drilling
        t3 = asyncio.run(mark_assistant.process("What evidence supports this root cause?", session_id=session_id))
        assert len(session.turns) == 3
        assert "evidence" in str(t3).lower() or "cpu" in str(t3).lower() or "cause" in str(t3).lower()

        # Turn 4: Remediation inquiry
        t4 = asyncio.run(mark_assistant.process("How did we fix it?", session_id=session_id))
        assert len(session.turns) == 4
        assert ("scale" in str(t4).lower() or "pod" in str(t4).lower() or "mitigation" in str(t4).lower() or "remediation" in str(t4).lower())

    def test_session_isolation(self, mark_assistant):
        session_a = "session_alpha"
        session_b = "session_beta"
        mark_assistant.session_store.clear(session_a)
        mark_assistant.session_store.clear(session_b)

        # Session A discusses AMF
        asyncio.run(mark_assistant.process("Explain incident mobile-core/incidents/amf-overload-2026-08-09", session_id=session_a))
        s_a = mark_assistant.session_store.get(session_a)
        assert s_a.active_incident_id == "mobile-core/incidents/amf-overload-2026-08-09"

        # Session B is new and unassociated
        s_b = mark_assistant.session_store.get_or_create(session_b)
        assert s_b.active_incident_id is None
        assert len(s_b.turns) == 0

        # Pleasantry in Session B should not think it's reviewing Session A's incident
        greeting_b = asyncio.run(mark_assistant.process("hello mark", session_id=session_b))
        assert "Greetings" in str(greeting_b) or "Incident Manager" in str(greeting_b)

    def test_cold_cache_db_rehydration(self, mark_assistant):
        session_id = "test_rehydrate_session_999"
        mark_assistant.session_store.clear(session_id)

        # Record a turn
        asyncio.run(mark_assistant.process("Explain incident mobile-core/incidents/amf-overload-2026-08-09", session_id=session_id))

        # Verify recorded in RAM
        session = mark_assistant.session_store.get(session_id)
        assert session is not None
        assert session.active_incident_id == "mobile-core/incidents/amf-overload-2026-08-09"

        # Simulate cold cache / worker reboot by removing from RAM
        with mark_assistant.session_store._lock:
            mark_assistant.session_store._sessions.pop(session_id, None)

        assert mark_assistant.session_store.get(session_id) is None

        # Rehydrate from DB
        rehydrated = mark_assistant.session_store.get_or_create(session_id)
        assert rehydrated is not None
        assert rehydrated.active_incident_id == "mobile-core/incidents/amf-overload-2026-08-09"
        assert len(rehydrated.turns) >= 1

    def test_fast_path_classifier_latency(self):
        session = MarkSession(session_id="latency_test", active_incident_id="mobile-core/incidents/amf-overload-2026-08-09")

        start = time.perf_counter()
        classified = classify_action("can you elaborate on that?", session=session)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert classified.action == UserAction.EXPLAIN_INCIDENT
        assert classified.target_intent == "technical"
        assert classified.confidence >= 0.85
        # Fast path must be strictly sub-millisecond (typically < 0.2ms)
        assert elapsed_ms < 5.0  # Generous threshold for test execution jitter

    def test_story_opt_out_and_list_incidents_intent_disambiguation(self, mark_assistant):
        session_id = "test_story_opt_out_001"
        mark_assistant.session_store.clear(session_id)

        # 1. Turn 1: Establish active incident
        t1 = asyncio.run(mark_assistant.process("what happened in mobile-core/incidents/amf-overload-2026-08-09?", session_id=session_id))
        assert "AMF" in str(t1) or "Incident story" in str(t1)

        # 2. Turn 2: User asks for "list of incident" - must list incidents, NOT tell incident story
        t2 = asyncio.run(mark_assistant.process("list of incident", session_id=session_id))
        assert "Current Incidents Under Management" in str(t2)
        assert "# Incident story" not in str(t2)

        # 3. Turn 3: User says "i do not need the story" - must NOT tell a story
        t3 = asyncio.run(mark_assistant.process("i do not need the story", session_id=session_id))
        assert "no story" in str(t3).lower()
        assert "# Incident story" not in str(t3)

