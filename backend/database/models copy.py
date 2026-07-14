"""Database models for chat sessions and messages."""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship
from backend.database.db import Base
import enum


class MessageRole(str, enum.Enum):
    """Enum for message roles."""
    user = "user"
    assistant = "assistant"


class ChatSession(Base):
    """Represents a chat session."""
    __tablename__ = "chat_sessions"

    session_id = Column(String(36), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.timestamp() if self.created_at else None,
            "last_accessed": self.last_accessed.timestamp() if self.last_accessed else None,
            "message_count": len(self.messages),
        }


class ChatMessage(Base):
    """Represents a single chat message."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id"), index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.timestamp() if self.created_at else None,
        }
