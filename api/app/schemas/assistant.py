"""
LoadMoveGH — Pydantic Schemas for AI Assistant API
====================================================

Request / response models for the chat endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
#  REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class ChatMessageRequest(BaseModel):
    """A single message from the user."""
    content: str = Field(..., min_length=1, max_length=4000)
    context_listing_id: Optional[str] = Field(
        None, description="Attach a listing context to scope load/pricing queries",
    )
    context_trip_id: Optional[str] = Field(
        None, description="Attach a trip context for tracking/route queries",
    )


class StartSessionRequest(BaseModel):
    """Create a new chat session."""
    title: Optional[str] = Field("New conversation", max_length=200)
    context_listing_id: Optional[str] = None
    context_trip_id: Optional[str] = None


class QuickActionRequest(BaseModel):
    """One-shot queries that don't need a persistent session."""
    action: str = Field(
        ...,
        description="One of: suggest_loads, recommend_price, profit_forecast, optimize_route, platform_help",
    )
    params: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
#  RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class ToolCallResponse(BaseModel):
    """Details of a tool call made by the assistant."""
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class ChatMessageResponse(BaseModel):
    """A single message in the conversation."""
    id: str
    role: str  # user | assistant | system | tool
    content: Optional[str] = None
    tool_calls: list[ToolCallResponse] = Field(default_factory=list)
    model_used: Optional[str] = None
    latency_ms: int = 0
    created_at: datetime


class ChatReplyResponse(BaseModel):
    """Response from sending a message — the assistant's reply."""
    session_id: str
    reply: ChatMessageResponse
    tool_calls_made: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


class SessionResponse(BaseModel):
    """A chat session summary."""
    id: str
    title: str
    status: str
    message_count: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    created_at: datetime
    updated_at: datetime


class SessionDetailResponse(BaseModel):
    """A chat session with all messages."""
    id: str
    title: str
    status: str
    messages: list[ChatMessageResponse]
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    """Paginated list of chat sessions."""
    sessions: list[SessionResponse]
    total: int
    page: int
    limit: int


class QuickActionResponse(BaseModel):
    """Response for one-shot quick actions."""
    action: str
    result: dict[str, Any]
    assistant_message: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0


class SuggestedPrompt(BaseModel):
    """A single suggested prompt chip."""
    icon: str  # emoji or icon name
    label: str
    message: str
    category: str  # loads | pricing | profit | route | help


class SuggestedPromptsResponse(BaseModel):
    """Contextual prompt suggestions for the chat UI."""
    prompts: list[SuggestedPrompt]
