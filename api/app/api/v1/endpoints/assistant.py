"""
LoadMoveGH — AI Assistant API Endpoints
========================================

Endpoints
---------
POST   /assistant/sessions                      — Start new chat session
GET    /assistant/sessions                      — List user's sessions
GET    /assistant/sessions/{id}                 — Get session with messages
DELETE /assistant/sessions/{id}                 — Archive/delete a session
POST   /assistant/sessions/{id}/messages        — Send message, get AI reply
POST   /assistant/quick                         — One-shot action (no session)
GET    /assistant/suggestions                   — Get contextual prompt chips

Integration Flow
-----------------
1. User opens chat → POST /sessions (or reuse existing)
2. User sends message → POST /sessions/{id}/messages
3. Backend builds message history from DB
4. OpenAI called with function-calling tools enabled
5. If model calls tools → execute tools with live DB data → feed results back
6. Final assistant reply persisted and returned to client
7. Client displays response with optional rich cards (loads, prices, routes)
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.models.assistant import ChatMessage, ChatSession, MessageRole, SessionStatus
from app.models.user import User
from app.ai.openai_client import OpenAIAssistant
from app.ai.tools import ToolExecutor
from app.schemas.assistant import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatReplyResponse,
    QuickActionRequest,
    QuickActionResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionResponse,
    StartSessionRequest,
    SuggestedPrompt,
    SuggestedPromptsResponse,
    ToolCallResponse,
)

logger = logging.getLogger("loadmovegh.api.assistant")

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


# ═══════════════════════════════════════════════════════════════
#  SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    body: StartSessionRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new AI assistant chat session."""
    session = ChatSession(
        user_id=user.id,
        title=body.title or "New conversation",
        context_listing_id=uuid.UUID(body.context_listing_id) if body.context_listing_id else None,
        context_trip_id=uuid.UUID(body.context_trip_id) if body.context_trip_id else None,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return _session_to_response(session, message_count=0)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's chat sessions (newest first)."""
    base = select(ChatSession).where(
        and_(
            ChatSession.user_id == user.id,
            ChatSession.status == SessionStatus.active,
        )
    )

    # Count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Fetch
    stmt = base.order_by(ChatSession.updated_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit)
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    return SessionListResponse(
        sessions=[
            _session_to_response(s, message_count=len(s.messages))
            for s in sessions
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a chat session with all messages."""
    session = await _get_user_session(db, session_id, user.id)

    return SessionDetailResponse(
        id=str(session.id),
        title=session.title,
        status=session.status.value,
        messages=[_message_to_response(m) for m in session.messages],
        total_prompt_tokens=session.total_prompt_tokens,
        total_completion_tokens=session.total_completion_tokens,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def archive_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive (soft-delete) a chat session."""
    session = await _get_user_session(db, session_id, user.id)
    session.status = SessionStatus.archived
    await db.flush()


# ═══════════════════════════════════════════════════════════════
#  CHAT — SEND MESSAGE & GET AI REPLY
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatReplyResponse,
)
async def send_message(
    session_id: uuid.UUID,
    body: ChatMessageRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the AI assistant and receive a reply.

    **Integration Flow:**
    1. Persist user message to DB
    2. Build conversation history from session messages
    3. Create tool executor with live DB access
    4. Call OpenAI with function-calling tools
    5. If tools are invoked → execute with real data → feed results back
    6. Persist assistant reply (and tool calls) to DB
    7. Return the final reply to the client
    """
    session = await _get_user_session(db, session_id, user.id)

    # Update context if provided
    if body.context_listing_id:
        session.context_listing_id = uuid.UUID(body.context_listing_id)
    if body.context_trip_id:
        session.context_trip_id = uuid.UUID(body.context_trip_id)

    # ── 1. Persist user message ──────────────────────────────
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.user,
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()

    # ── 2. Build conversation history ────────────────────────
    history = []
    for msg in session.messages:
        if msg.role == MessageRole.system:
            continue  # System prompt is injected by OpenAI client
        entry: dict[str, Any] = {"role": msg.role.value}
        if msg.content:
            entry["content"] = msg.content
        if msg.tool_call_id:
            entry["tool_call_id"] = msg.tool_call_id
            entry["content"] = json.dumps(msg.tool_result) if msg.tool_result else ""
        history.append(entry)

    # Add the new user message
    history.append({"role": "user", "content": body.content})

    # ── 3. Create tool executor ──────────────────────────────
    executor = ToolExecutor(db=db, user_id=user.id)

    # ── 4–5. Call OpenAI ─────────────────────────────────────
    assistant = OpenAIAssistant(tool_executor=executor.execute)

    user_role = "courier"
    if hasattr(user, "role_names") and user.role_names:
        if "shipper" in user.role_names:
            user_role = "shipper"

    reply = await assistant.chat(
        messages=history,
        user_role=user_role,
        user_name=user.first_name or "User",
    )

    # ── 6. Persist assistant reply ───────────────────────────
    tool_call_responses = []

    # Persist tool call messages
    for tc, result in zip(reply.tool_calls_made, reply.tool_results):
        tool_msg = ChatMessage(
            session_id=session.id,
            role=MessageRole.tool,
            tool_call_id=tc.id,
            tool_name=tc.name,
            tool_arguments=tc.arguments,
            tool_result=result,
        )
        db.add(tool_msg)
        tool_call_responses.append(
            ToolCallResponse(
                tool_name=tc.name,
                arguments=tc.arguments,
                result=result,
            )
        )

    # Persist assistant reply
    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.assistant,
        content=reply.content,
        model_used=reply.model,
        prompt_tokens=reply.prompt_tokens,
        completion_tokens=reply.completion_tokens,
        latency_ms=reply.latency_ms,
    )
    db.add(assistant_msg)

    # Update session token counters
    session.total_prompt_tokens += reply.prompt_tokens
    session.total_completion_tokens += reply.completion_tokens
    session.updated_at = datetime.now(timezone.utc)

    # Auto-title from first message
    if session.title == "New conversation" and len(session.messages) <= 2:
        session.title = body.content[:80]

    await db.flush()
    await db.refresh(assistant_msg)

    # ── 7. Return response ───────────────────────────────────
    return ChatReplyResponse(
        session_id=str(session.id),
        reply=ChatMessageResponse(
            id=str(assistant_msg.id),
            role="assistant",
            content=reply.content,
            tool_calls=tool_call_responses,
            model_used=reply.model,
            latency_ms=reply.latency_ms,
            created_at=assistant_msg.created_at,
        ),
        tool_calls_made=len(reply.tool_calls_made),
        prompt_tokens=reply.prompt_tokens,
        completion_tokens=reply.completion_tokens,
    )


# ═══════════════════════════════════════════════════════════════
#  QUICK ACTIONS (no persistent session)
# ═══════════════════════════════════════════════════════════════

@router.post("/quick", response_model=QuickActionResponse)
async def quick_action(
    body: QuickActionRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    One-shot AI action without creating a chat session.
    Useful for inline suggestions in the load board or wallet UI.

    Actions: suggest_loads, recommend_price, profit_forecast, optimize_route, platform_help
    """
    executor = ToolExecutor(db=db, user_id=user.id)

    tool_map = {
        "suggest_loads": "suggest_best_loads",
        "recommend_price": "recommend_pricing",
        "profit_forecast": "show_profit_forecast",
        "optimize_route": "optimize_route",
        "platform_help": "answer_platform_question",
    }

    tool_name = tool_map.get(body.action)
    if not tool_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {body.action}. Valid: {list(tool_map.keys())}",
        )

    result = await executor.execute(tool_name, body.params)

    # Optionally get a natural-language summary from OpenAI
    assistant_message = None
    prompt_tokens = 0
    completion_tokens = 0
    latency_ms = 0

    if body.params.get("include_summary", True):
        assistant = OpenAIAssistant(tool_executor=executor.execute)

        user_role = "courier"
        if hasattr(user, "role_names") and user.role_names:
            if "shipper" in user.role_names:
                user_role = "shipper"

        summary_reply = await assistant.chat(
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Summarise this {body.action} result concisely for the user "
                        f"in 2-3 sentences: {json.dumps(result, default=str)[:2000]}"
                    ),
                }
            ],
            user_role=user_role,
            user_name=user.first_name or "User",
        )
        assistant_message = summary_reply.content
        prompt_tokens = summary_reply.prompt_tokens
        completion_tokens = summary_reply.completion_tokens
        latency_ms = summary_reply.latency_ms

    return QuickActionResponse(
        action=body.action,
        result=result,
        assistant_message=assistant_message,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
    )


# ═══════════════════════════════════════════════════════════════
#  CONTEXTUAL SUGGESTIONS
# ═══════════════════════════════════════════════════════════════

@router.get("/suggestions", response_model=SuggestedPromptsResponse)
async def get_suggestions(
    user: User = Depends(get_current_active_user),
):
    """
    Return role-aware suggested prompts for the chat input.
    Displayed as quick-action chips in the Flutter chat UI.
    """
    user_role = "courier"
    if hasattr(user, "role_names") and user.role_names:
        if "shipper" in user.role_names:
            user_role = "shipper"

    courier_prompts = [
        SuggestedPrompt(
            icon="package",
            label="Best loads near me",
            message="What are the best loads available near my current location?",
            category="loads",
        ),
        SuggestedPrompt(
            icon="money",
            label="Price recommendation",
            message="What should I bid on a 500kg general cargo from Accra to Kumasi?",
            category="pricing",
        ),
        SuggestedPrompt(
            icon="chart",
            label="My earnings forecast",
            message="Show me my projected earnings for the next 30 days",
            category="profit",
        ),
        SuggestedPrompt(
            icon="map",
            label="Route to Kumasi",
            message="What's the best route from Accra to Kumasi?",
            category="route",
        ),
        SuggestedPrompt(
            icon="help",
            label="How does escrow work?",
            message="Explain how the escrow payment system works on LoadMoveGH",
            category="help",
        ),
        SuggestedPrompt(
            icon="fuel",
            label="Fuel cost estimate",
            message="How much fuel will I need for a Tema to Tamale delivery?",
            category="route",
        ),
    ]

    shipper_prompts = [
        SuggestedPrompt(
            icon="money",
            label="Pricing advice",
            message="What's a fair budget for shipping 2 tons of electronics from Accra to Takoradi?",
            category="pricing",
        ),
        SuggestedPrompt(
            icon="chart",
            label="Spending forecast",
            message="Show me my projected shipping costs for the next 30 days",
            category="profit",
        ),
        SuggestedPrompt(
            icon="package",
            label="Post a load",
            message="Help me decide the best way to post a load for refrigerated goods from Tema",
            category="loads",
        ),
        SuggestedPrompt(
            icon="map",
            label="Delivery timeline",
            message="How long does a delivery from Accra to Tamale usually take?",
            category="route",
        ),
        SuggestedPrompt(
            icon="help",
            label="Dispute process",
            message="How do I open a dispute if my shipment is damaged?",
            category="help",
        ),
        SuggestedPrompt(
            icon="wallet",
            label="Wallet help",
            message="How do I deposit money using MTN Mobile Money?",
            category="help",
        ),
    ]

    return SuggestedPromptsResponse(
        prompts=courier_prompts if user_role == "courier" else shipper_prompts,
    )


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

async def _get_user_session(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID,
) -> ChatSession:
    """Fetch a session that belongs to the user, or 404."""
    result = await db.execute(
        select(ChatSession).where(
            and_(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return session


def _session_to_response(session: ChatSession, message_count: int = 0) -> SessionResponse:
    return SessionResponse(
        id=str(session.id),
        title=session.title,
        status=session.status.value,
        message_count=message_count,
        total_prompt_tokens=session.total_prompt_tokens,
        total_completion_tokens=session.total_completion_tokens,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _message_to_response(msg: ChatMessage) -> ChatMessageResponse:
    tool_calls = []
    if msg.tool_name:
        tool_calls.append(
            ToolCallResponse(
                tool_name=msg.tool_name,
                arguments=msg.tool_arguments or {},
                result=msg.tool_result or {},
            )
        )

    return ChatMessageResponse(
        id=str(msg.id),
        role=msg.role.value,
        content=msg.content,
        tool_calls=tool_calls,
        model_used=msg.model_used,
        latency_ms=msg.latency_ms,
        created_at=msg.created_at,
    )
