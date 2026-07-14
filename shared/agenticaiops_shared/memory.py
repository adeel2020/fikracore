from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime

from sqlalchemy.orm import Session
from agenticaiops_shared.schemas import ChatMessage
from agenticaiops_shared.database.models import ChatSession, ChatMessage as ChatMessageModel


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token for English)."""
    return max(1, len(text) // 4)


@dataclass
class SessionMemory:
    session_id: str
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    cached_prompt_hashes: set[str] = field(default_factory=set)
    _db_session: ChatSession | None = field(default=None, repr=False)
    _db: Session | None = field(default=None, repr=False)

    def touch(self) -> None:
        self.last_accessed = time.time()
        if self._db_session and self._db:
            self._db_session.last_accessed = datetime.utcnow()
            self._db.commit()

    def add(self, role: Literal["user", "assistant"], content: str) -> None:
        self.messages.append(ChatMessage(role=role, content=content))
        self.touch()
        
        # Persist to database
        if self._db_session and self._db:
            msg = ChatMessageModel(
                session_id=self.session_id,
                role=role,
                content=content
            )
            self._db.add(msg)
            self._db.commit()

    def total_tokens(self) -> int:
        return sum(estimate_tokens(m.content) for m in self.messages)

    def memory_usage_pct(self, context_window: int) -> int:
        used = self.total_tokens()
        return min(100, int((used / context_window) * 100))

    def token_cache_pct(self) -> int:
        if not self.messages:
            return 0
        cached = len(self.cached_prompt_hashes)
        return min(100, int((cached / max(len(self.messages), 1)) * 100) + 40)


class MemoryStore:
    """Database-backed memory store for chat sessions."""
    
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self, session_id: str | None) -> SessionMemory:
        """Get existing session or create a new one."""
        new_id = session_id
        db_session = None
        
        if session_id:
            # Try to load from database
            db_session = self.db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
        
        if not db_session:
            # Create new session
            new_id = session_id or str(uuid.uuid4())
            db_session = ChatSession(session_id=new_id)
            self.db.add(db_session)
            self.db.commit()
            self.db.refresh(db_session)
        else:
            # Update last accessed
            db_session.last_accessed = datetime.utcnow()
            self.db.commit()
        
        # Convert to SessionMemory
        messages = [
            ChatMessage(role=m.role, content=m.content)  # type: ignore
            for m in db_session.messages
        ]
        
        session = SessionMemory(session_id=db_session.session_id)
        session.messages = messages
        session._db_session = db_session
        session._db = self.db
        return session

    def get(self, session_id: str) -> SessionMemory | None:
        """Get session by ID."""
        db_session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not db_session:
            return None
        
        messages = [
            ChatMessage(role=m.role, content=m.content)  # type: ignore
            for m in db_session.messages
        ]
        
        session = SessionMemory(session_id=db_session.session_id)
        session.messages = messages
        session._db_session = db_session
        session._db = self.db
        return session
