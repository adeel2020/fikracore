"""Conversation session context.

Phase 3A: per-``session_id`` in-memory context. The only thing we remember is
the active incident id (so follow-up questions like "why did it happen?" can
target the incident without the client repeating the id). Deliberately minimal —
no message history, no semantic fallback.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionContext:
    session_id: str
    active_incident_id: str | None = None
    last_intent: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    """Thread-safe in-memory session store (single process, per-service)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, SessionContext] = {}

    def get(self, session_id: str) -> SessionContext:
        with self._lock:
            ctx = self._sessions.get(session_id)
            if ctx is None:
                ctx = SessionContext(session_id=session_id)
                self._sessions[session_id] = ctx
            return ctx

    def set_active_incident(self, session_id: str, incident_id: str | None) -> SessionContext:
        with self._lock:
            ctx = self._sessions.setdefault(session_id, SessionContext(session_id=session_id))
            ctx.active_incident_id = incident_id
            return ctx

    def active_incident(self, session_id: str) -> str | None:
        with self._lock:
            ctx = self._sessions.get(session_id)
            return ctx.active_incident_id if ctx else None

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


default_session_store = SessionStore()
