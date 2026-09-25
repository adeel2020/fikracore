"""Dialogue state manager for Mark / Zaki operations copilot.

Maintains multi-turn conversational history, working entity memory, and active
simulation context across turns so Mark can hold state, resolve follow-ups
("why did that happen?", "what is its drop rate?"), and make multi-step decisions.
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class DialogueTurn:
    role: str  # "user" | "assistant"
    text: str
    timestamp: float = field(default_factory=time.time)
    intent: Optional[str] = None
    focused_entity: Optional[str] = None


@dataclass
class ConversationSession:
    session_id: str
    scenario_id: Optional[str] = None
    run_id: Optional[str] = None
    stage: Optional[str] = None
    focused_entity: Optional[str] = None
    focused_kpi: Optional[str] = None
    last_intent: Optional[str] = None
    turns: list[DialogueTurn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_turn(self, role: str, text: str, intent: Optional[str] = None, entity: Optional[str] = None) -> None:
        turn = DialogueTurn(
            role=role,
            text=text,
            intent=intent,
            focused_entity=entity or self.focused_entity,
        )
        self.turns.append(turn)
        # Cap turns history at 20 to keep memory compact
        if len(self.turns) > 20:
            self.turns = self.turns[-20:]
        if entity:
            self.focused_entity = entity
        if intent:
            self.last_intent = intent
        self.updated_at = time.time()

    def get_recent_user_turns(self, limit: int = 3) -> list[str]:
        return [t.text for t in self.turns if t.role == "user"][-limit:]

    def get_last_assistant_turn(self) -> Optional[DialogueTurn]:
        for t in reversed(self.turns):
            if t.role == "assistant":
                return t
        return None


class DialogueStateManager:
    """Thread-safe manager for Mark's conversation memory."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, ConversationSession] = {}

    def get_or_create(
        self,
        session_id: str,
        scenario_id: Optional[str] = None,
        run_id: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> ConversationSession:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                session = ConversationSession(
                    session_id=session_id,
                    scenario_id=scenario_id,
                    run_id=run_id,
                    stage=stage,
                )
                self._sessions[session_id] = session
            else:
                if scenario_id:
                    session.scenario_id = scenario_id
                if run_id:
                    session.run_id = run_id
                if stage:
                    session.stage = stage
            return session

    def record_user_turn(
        self,
        session_id: str,
        text: str,
        detected_entity: Optional[str] = None,
        detected_intent: Optional[str] = None,
        scenario_id: Optional[str] = None,
        run_id: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> ConversationSession:
        session = self.get_or_create(session_id, scenario_id=scenario_id, run_id=run_id, stage=stage)
        session.add_turn(
            role="user",
            text=text,
            intent=detected_intent,
            entity=detected_entity,
        )
        return session

    def record_assistant_turn(
        self,
        session_id: str,
        text: str,
        intent: Optional[str] = None,
        focused_entity: Optional[str] = None,
    ) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.add_turn(
                    role="assistant",
                    text=text,
                    intent=intent,
                    entity=focused_entity,
                )

    def resolve_anaphora_entity(self, text: str, session: ConversationSession) -> Optional[str]:
        """Resolves pronouns ('it', 'that node', 'the entity', 'the culprit') to the focused entity."""
        lower = text.lower()
        pronoun_match = bool(
            re.search(r"\b(it|that node|the node|this node|that entity|the component|the culprit|its)\b", lower)
        )
        if pronoun_match and session.focused_entity:
            return session.focused_entity
        return None

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


# Global singleton instance
dialogue_state_manager = DialogueStateManager()
