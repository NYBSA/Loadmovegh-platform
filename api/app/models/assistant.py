"""
LoadMoveGH — SQLAlchemy Models: AI Assistant Conversations
==========================================================

Persists chat sessions and messages so the assistant retains context
across app restarts and can be audited / improved.

Tables
------
- chat_sessions : one per user conversation thread
- chat_messages : individual messages (user, assistant, tool calls/results)
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ── Helpers ──────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── Enums ────────────────────────────────────────────────────────

class MessageRole(str, enum.Enum):
    """Maps to the OpenAI chat-completion roles."""
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class SessionStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


# ── Chat Session ─────────────────────────────────────────────────

class ChatSession(Base):
    """
    A conversation thread between a user and the AI assistant.
    Each session carries a system prompt tailored to the user's role
    (courier vs shipper) and optional context like active trip / listing IDs.
    """
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, default="New conversation",
    )
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, name="session_status"),
        nullable=False,
        default=SessionStatus.active,
    )
    # Contextual anchors — the assistant uses these to scope queries
    context_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    context_trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    # Token accounting (for cost tracking)
    total_prompt_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    total_completion_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow,
    )

    # Relationships
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_chat_sessions_user_updated", "user_id", "updated_at"),
    )


# ── Chat Message ─────────────────────────────────────────────────

class ChatMessage(Base):
    """
    A single message in a conversation. Supports all OpenAI roles
    including tool calls and tool results.
    """
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role"),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    # For tool calls / tool results
    tool_call_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    tool_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    tool_arguments: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )
    tool_result: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )
    # Metadata
    model_used: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )
    prompt_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    completion_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    latency_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
    )
