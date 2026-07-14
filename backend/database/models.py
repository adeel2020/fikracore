"""Database models for chat sessions and messages."""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Enum
from sqlalchemy.orm import relationship
from backend.database.db import Base
import enum


def get_dubai_now() -> datetime:
    """Returns a naive datetime representing the current time in Dubai (UTC + 4)."""
    return datetime.now(timezone(timedelta(hours=4))).replace(tzinfo=None)


def get_dubai_timestamp(dt: datetime | None) -> float | None:
    """Safely converts a naive Dubai datetime to a UNIX epoch timestamp."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=4)))
    return dt.timestamp()


class MessageRole(str, enum.Enum):
    """Enum for message roles."""
    user = "user"
    assistant = "assistant"


class ChatSession(Base):
    """Represents a chat session."""
    __tablename__ = "chat_sessions"

    session_id = Column(String(36), primary_key=True, index=True)
    created_at = Column(DateTime, default=get_dubai_now, index=True)
    last_accessed = Column(DateTime, default=get_dubai_now, onupdate=get_dubai_now)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    telemetry = relationship("SessionTelemetry", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": get_dubai_timestamp(self.created_at),
            "last_accessed": get_dubai_timestamp(self.last_accessed),
            "message_count": len(self.messages),
        }


class ChatMessage(Base):
    """Represents a single chat message."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id"), index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=get_dubai_now, index=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": get_dubai_timestamp(self.created_at),
        }


class SessionTelemetry(Base):
    """Represents API usage and performance telemetry for a session."""
    __tablename__ = "session_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id"), index=True)
    agent_name = Column(String(100))
    
    # Metrics
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Performance
    latency_ms = Column(Integer, default=0)
    throughput_tps = Column(Float, default=0.0) # Tokens per second
    estimated_cost_usd = Column(Float, default=0.0000)
    
    created_at = Column(DateTime, default=get_dubai_now, index=True)

    # Relationships
    session = relationship("ChatSession", back_populates="telemetry")

    def to_dict(self) -> dict:
        """Convert telemetry to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "throughput_tps": self.throughput_tps,
            "estimated_cost_usd": self.estimated_cost_usd,
            "created_at": get_dubai_timestamp(self.created_at),
        }


class ComplaintTelemetry(Base):
    """Telemetry to monitor customer complaints."""
    __tablename__ = "complaint_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id"), index=True)
    complaint_number = Column(String(50), unique=True, index=True)
    time_reported = Column(DateTime, default=get_dubai_now, index=True)
    issue_summary = Column(Text, nullable=False)
    assignment_target = Column(String(100), nullable=False)
    assignment_queue = Column(String(100), nullable=True)
    reassignment_category = Column(String(100), nullable=False)
    resolution_category = Column(String(100), nullable=False)
    raw_complaint = Column(Text, nullable=False)

    # Relationships
    session = relationship("ChatSession")

    def to_dict(self) -> dict:
        """Convert complaint telemetry to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "complaint_number": self.complaint_number,
            "time_reported": get_dubai_timestamp(self.time_reported),
            "issue_summary": self.issue_summary,
            "assignment_target": self.assignment_target,
            "assignment_queue": self.assignment_queue,
            "reassignment_category": self.reassignment_category,
            "resolution_category": self.resolution_category,
            "raw_complaint": self.raw_complaint,
        }