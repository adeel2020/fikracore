"""
M.A.R.K. 3-Tier Adaptive Session Store

Maintains conversation history and incident context across dialogue turns:
- Tier 1: In-Process RAM cache (sub-millisecond for real-time voice & active turns)
- Tier 2: Distributed Redis cache (optional, shared across K8s pods / uvicorn workers)
- Tier 3: PostgreSQL / SQLite database (durable storage and cold session rehydration)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .user_actions import UserAction

logger = logging.getLogger("assistant.mark.session")


@dataclass
class ConversationTurn:
    """A single dialogue exchange between the operator and MARK."""
    turn_id: int
    timestamp: float
    user_query: str
    assistant_reply: str
    spoken_reply: str | None
    action: UserAction
    incident_id: str | None = None
    engine_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "timestamp": self.timestamp,
            "user_query": self.user_query,
            "assistant_reply": self.assistant_reply,
            "spoken_reply": self.spoken_reply,
            "action": self.action.value if hasattr(self.action, "value") else str(self.action),
            "incident_id": self.incident_id,
            "engine_id": self.engine_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversationTurn:
        raw_action = data.get("action", "converse")
        try:
            action = UserAction(raw_action)
        except ValueError:
            action = UserAction.CONVERSE
        return cls(
            turn_id=data.get("turn_id", 0),
            timestamp=data.get("timestamp", time.time()),
            user_query=data.get("user_query", ""),
            assistant_reply=data.get("assistant_reply", ""),
            spoken_reply=data.get("spoken_reply"),
            action=action,
            incident_id=data.get("incident_id"),
            engine_id=data.get("engine_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MarkSession:
    """Active conversational state for a specific session_id."""
    session_id: str
    user_name: str | None = None
    active_incident_id: str | None = None
    last_action: UserAction | None = None
    last_topic: str | None = None
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    turns: list[ConversationTurn] = field(default_factory=list)
    max_turns: int = 20

    def add_turn(
        self,
        user_query: str,
        assistant_reply: str,
        action: UserAction,
        spoken_reply: str | None = None,
        incident_id: str | None = None,
        engine_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationTurn:
        self.last_accessed = time.time()
        self.last_action = action
        if incident_id:
            self.active_incident_id = incident_id

        turn = ConversationTurn(
            turn_id=len(self.turns) + 1,
            timestamp=self.last_accessed,
            user_query=user_query,
            assistant_reply=assistant_reply,
            spoken_reply=spoken_reply,
            action=action,
            incident_id=self.active_incident_id,
            engine_id=engine_id,
            metadata=metadata or {},
        )
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)
        return turn

    def get_recent_turns(self, limit: int = 5) -> list[ConversationTurn]:
        """Return the most recent turns in chronological order."""
        return self.turns[-limit:] if self.turns else []

    def clear(self) -> None:
        self.active_incident_id = None
        self.last_action = None
        self.last_topic = None
        self.user_name = None
        self.turns.clear()
        self.last_accessed = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_name": self.user_name,
            "active_incident_id": self.active_incident_id,
            "last_action": self.last_action.value if self.last_action else None,
            "last_topic": self.last_topic,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "turns": [t.to_dict() for t in self.turns],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarkSession:
        raw_action = data.get("last_action")
        last_action = None
        if raw_action:
            try:
                last_action = UserAction(raw_action)
            except ValueError:
                last_action = None

        session = cls(
            session_id=data["session_id"],
            user_name=data.get("user_name"),
            active_incident_id=data.get("active_incident_id"),
            last_action=last_action,
            last_topic=data.get("last_topic"),
            created_at=data.get("created_at", time.time()),
            last_accessed=data.get("last_accessed", time.time()),
        )
        session.turns = [ConversationTurn.from_dict(t) for t in data.get("turns", [])]
        return session


def resolve_user_name(
    query: str | None = None,
    session: MarkSession | None = None,
    context: dict[str, Any] | None = None,
) -> str | None:
    """
    Resolve the operator's name across context, active session, conversation clues, and environment.
    """
    # 1. Explicit in context
    if context:
        for k in ("user_name", "username", "user", "operator_name"):
            val = context.get(k)
            if isinstance(val, str) and val.strip():
                clean = val.strip()
                if session:
                    session.user_name = clean
                return clean

    # 2. Stored in active session
    if session and session.user_name:
        return session.user_name

    # 3. Mentioned in query (e.g. "my name is Adeel", "I am Adeel", "call me Adeel")
    if query:
        import re
        match = re.search(
            r"\b(?:my\s+name\s+is|i\s*['’]?m|i\s+am|call\s+me)\s+([A-Z][a-zA-Z]{1,25})\b",
            query,
            re.IGNORECASE,
        )
        if match:
            candidate = match.group(1).strip()
            excluded = {
                "fine", "good", "great", "well", "okay", "online", "ready",
                "here", "asking", "mark", "jarvis", "back", "working", "sure",
                "listening", "wondering", "looking", "trying", "hoping",
            }
            if candidate.lower() not in excluded:
                name = candidate.capitalize()
                if session:
                    session.user_name = name
                return name

    # 4. Environment default (MARK_USER_NAME or USER)
    env_name = os.getenv("MARK_USER_NAME")
    if not env_name:
        raw_user = os.getenv("USER") or ""
        if raw_user.lower() == "adeelarshad":
            env_name = "Adeel"
        elif raw_user and raw_user.lower() not in ("root", "nobody", "daemon", "runner", "ubuntu", "ec2-user", "node"):
            import re
            parts = re.split(r"[._-]", raw_user)
            if parts and parts[0].isalpha():
                env_name = parts[0].capitalize()

    if env_name:
        if session and not session.user_name:
            session.user_name = env_name
        return env_name

    return None


class MarkSessionStore:
    """
    Thread-safe 3-tier adaptive session store:
    - Tier 1: In-process RAM cache (threading.RLock for voice-speed <0.1ms).
    - Tier 2: Redis cluster sync (optional, active when Redis is available).
    - Tier 3: PostgreSQL / SQLite database for persistence & cold rehydration.
    """

    def __init__(
        self,
        ttl_seconds: int = 86400,
        max_sessions: int = 1000,
        redis_url: str | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, MarkSession] = {}
        self._ttl_seconds = ttl_seconds
        self._max_sessions = max_sessions

        # Tier 2: Optional Redis client
        self._redis_client = None
        self._init_redis(redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    def _init_redis(self, url: str) -> None:
        """Attempt to connect to Redis; gracefully skip if not installed or unreachable."""
        try:
            import redis  # type: ignore
            client = redis.Redis.from_url(url, socket_connect_timeout=0.5, socket_timeout=0.5)
            client.ping()
            self._redis_client = client
            logger.info("[MarkSessionStore] Connected to Tier 2 Redis cache at %s", url)
        except Exception:
            self._redis_client = None
            logger.debug("[MarkSessionStore] Redis unavailable; running with L1 (RAM) + L3 (Postgres/SQLite).")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_or_create(self, session_id: str) -> MarkSession:
        """Retrieve active session or create/rehydrate one."""
        with self._lock:
            self._evict_expired_unlocked()

            # 1. Tier 1: Check In-Process RAM
            session = self._sessions.get(session_id)
            if session is not None:
                session.last_accessed = time.time()
                return session

            # 2. Tier 2: Check Redis if connected
            session = self._load_from_redis(session_id)
            if session is not None:
                self._sessions[session_id] = session
                return session

            # 3. Tier 3: Rehydrate from PostgreSQL / SQLite
            session = self._rehydrate_from_db(session_id)
            if session is None:
                session = MarkSession(session_id=session_id)

            self._sessions[session_id] = session
            return session

    def get(self, session_id: str) -> MarkSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def set_active_incident(self, session_id: str, incident_id: str | None) -> None:
        with self._lock:
            session = self.get_or_create(session_id)
            session.active_incident_id = incident_id
            session.last_accessed = time.time()
            self._sync_to_redis(session)

    def record_turn(
        self,
        session_id: str,
        user_query: str,
        assistant_reply: str,
        action: UserAction,
        spoken_reply: str | None = None,
        incident_id: str | None = None,
        engine_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationTurn:
        """Record turn in Tier 1 RAM, sync to Tier 2 Redis, and persist to Tier 3 DB."""
        with self._lock:
            session = self.get_or_create(session_id)
            turn = session.add_turn(
                user_query=user_query,
                assistant_reply=assistant_reply,
                action=action,
                spoken_reply=spoken_reply,
                incident_id=incident_id,
                engine_id=engine_id,
                metadata=metadata,
            )
            self._sync_to_redis(session)

        # Persist to DB (Postgres / SQLite)
        self._persist_turn_to_db(session_id, user_query, assistant_reply, incident_id)
        return turn

    def clear(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.pop(session_id, None)
            if session:
                session.clear()
            if self._redis_client:
                try:
                    self._redis_client.delete(f"mark:session:{session_id}")
                except Exception:
                    pass
            try:
                from agenticaiops_shared.database.db import SessionLocal
                from agenticaiops_shared.database.models import ChatMessage, ChatSession
                with SessionLocal() as db:
                    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
                    db.query(ChatSession).filter(ChatSession.session_id == session_id).delete()
                    db.commit()
            except Exception as exc:
                logger.debug("[MarkSessionStore] DB clear skipped for session %s: %s", session_id, exc)

    # ------------------------------------------------------------------
    # Tier 2: Redis Helpers
    # ------------------------------------------------------------------

    def _load_from_redis(self, session_id: str) -> MarkSession | None:
        if not self._redis_client:
            return None
        try:
            data = self._redis_client.get(f"mark:session:{session_id}")
            if data:
                payload = json.loads(data)
                return MarkSession.from_dict(payload)
        except Exception as exc:
            logger.debug("[MarkSessionStore] Redis read failed for session %s: %s", session_id, exc)
        return None

    def _sync_to_redis(self, session: MarkSession) -> None:
        if not self._redis_client:
            return
        try:
            key = f"mark:session:{session.session_id}"
            payload = json.dumps(session.to_dict())
            self._redis_client.setex(key, self._ttl_seconds, payload)
        except Exception as exc:
            logger.debug("[MarkSessionStore] Redis write failed for session %s: %s", session.session_id, exc)

    # ------------------------------------------------------------------
    # Tier 3: Database Rehydration & Persistence
    # ------------------------------------------------------------------

    def _rehydrate_from_db(self, session_id: str) -> MarkSession | None:
        """Rehydrate active incident context and recent turns from ChatSession/ChatMessage."""
        try:
            from agenticaiops_shared.database.db import SessionLocal
            from agenticaiops_shared.database.models import ChatMessage, ChatSession

            with SessionLocal() as db:
                db_session = (
                    db.query(ChatSession)
                    .filter(ChatSession.session_id == session_id)
                    .first()
                )
                if not db_session:
                    return None

                session = MarkSession(session_id=session_id)
                messages = (
                    db.query(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc())
                    .limit(20)
                    .all()
                )

                # Reconstruct turns from alternating user and assistant messages
                user_msg: str | None = None
                for msg in messages:
                    if msg.role == "user":
                        user_msg = msg.content
                    elif msg.role == "assistant" and user_msg is not None:
                        from storyteller.conversation.service import extract_incident_ref
                        inc_ref = extract_incident_ref(msg.content) or extract_incident_ref(user_msg)
                        if inc_ref:
                            session.active_incident_id = inc_ref

                        session.add_turn(
                            user_query=user_msg,
                            assistant_reply=msg.content,
                            action=UserAction.EXPLAIN_INCIDENT if inc_ref else UserAction.CONVERSE,
                            incident_id=inc_ref,
                        )
                        user_msg = None

                logger.info(
                    "[MarkSessionStore] Rehydrated session %s from DB with %d turns (active incident: %s)",
                    session_id,
                    len(session.turns),
                    session.active_incident_id,
                )
                return session
        except Exception as exc:
            logger.debug("[MarkSessionStore] DB rehydration skipped: %s", exc)
            return None

    def _persist_turn_to_db(
        self,
        session_id: str,
        user_query: str,
        assistant_reply: str,
        incident_id: str | None,
    ) -> None:
        """Persist user and assistant messages to ChatSession/ChatMessage."""
        try:
            from agenticaiops_shared.database.db import SessionLocal
            from agenticaiops_shared.database.models import ChatMessage, ChatSession

            with SessionLocal() as db:
                db_session = (
                    db.query(ChatSession)
                    .filter(ChatSession.session_id == session_id)
                    .first()
                )
                if not db_session:
                    db_session = ChatSession(session_id=session_id)
                    db.add(db_session)
                    db.commit()
                else:
                    db_session.last_accessed = datetime.now(timezone.utc).replace(tzinfo=None)
                    db.commit()

                user_record = ChatMessage(
                    session_id=session_id,
                    role="user",
                    content=user_query,
                )
                asst_record = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_reply,
                )
                db.add(user_record)
                db.add(asst_record)
                db.commit()
        except Exception as exc:
            logger.debug("[MarkSessionStore] DB turn persistence skipped: %s", exc)

    def _evict_expired_unlocked(self) -> None:
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if (now - s.last_accessed) > self._ttl_seconds]
        for sid in expired:
            self._sessions.pop(sid, None)


# Module-level singleton default session store
default_session_store = MarkSessionStore()
