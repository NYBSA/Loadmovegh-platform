"""
LoadMoveGH — OpenAI Client Singleton
=====================================

Provides a reusable async httpx-based client for the OpenAI Chat Completions
API with **function calling** support.  All assistant interactions route
through this module so we have a single place for model selection, rate
limiting, retry logic, and cost tracking.

Flow
----
1.  Build messages array (system + history + user)
2.  Attach tool definitions (load search, pricing, profit, route, FAQ)
3.  Call OpenAI /v1/chat/completions
4.  If response contains tool_calls → execute tools → feed results back
5.  Return final assistant message

Environment
-----------
OPENAI_API_KEY          — required
OPENAI_MODEL            — default gpt-4o
OPENAI_MAX_TOKENS       — default 2048
OPENAI_TEMPERATURE      — default 0.4
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("loadmovegh.ai")

_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_MAX_TOOL_ROUNDS = 5   # Safety: max tool-call round-trips per request


# ═══════════════════════════════════════════════════════════════
#  DATA TYPES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ToolCall:
    """Represents a single function call the model wants to make."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class AssistantReply:
    """The final reply from the OpenAI API after all tool rounds."""
    content: str
    tool_calls_made: list[ToolCall] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0


# ═══════════════════════════════════════════════════════════════
#  TOOL DEFINITIONS (OpenAI Function Calling Schema)
# ═══════════════════════════════════════════════════════════════

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "suggest_best_loads",
            "description": (
                "Search and rank the best available freight loads for a courier "
                "based on their location, vehicle type, preferred routes, and "
                "current market conditions. Returns top matching loads with "
                "AI match scores."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Courier's current latitude",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Courier's current longitude",
                    },
                    "vehicle_type": {
                        "type": "string",
                        "enum": [
                            "pickup", "van", "flatbed", "box_truck",
                            "trailer", "refrigerated", "tanker",
                        ],
                        "description": "Courier's vehicle type",
                    },
                    "max_distance_km": {
                        "type": "number",
                        "description": "Max pickup distance in km (default 100)",
                    },
                    "cargo_preference": {
                        "type": "string",
                        "description": "Preferred cargo type if any",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 5)",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_pricing",
            "description": (
                "Get AI-recommended bid price range for a freight load. "
                "Uses the ML pricing engine considering distance, weight, "
                "cargo type, urgency, fuel costs, and regional demand."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {
                        "type": "string",
                        "description": "UUID of the freight listing",
                    },
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city name",
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city name",
                    },
                    "distance_km": {
                        "type": "number",
                        "description": "Route distance in kilometres",
                    },
                    "weight_kg": {
                        "type": "number",
                        "description": "Load weight in kg",
                    },
                    "cargo_type": {
                        "type": "string",
                        "description": "Type of cargo",
                    },
                    "vehicle_type": {
                        "type": "string",
                        "description": "Required vehicle type",
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["standard", "express", "urgent", "scheduled"],
                        "description": "Urgency level",
                    },
                },
                "required": ["distance_km", "weight_kg", "cargo_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_profit_forecast",
            "description": (
                "Calculate a profit forecast for a courier or shipper. "
                "For couriers: project earnings over N days based on "
                "historical trip data, fuel costs, and commission. "
                "For shippers: project shipping spend and savings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "UUID of the user (auto-filled from context)",
                    },
                    "forecast_days": {
                        "type": "integer",
                        "description": "Number of days to forecast (default 30)",
                    },
                    "include_fuel_costs": {
                        "type": "boolean",
                        "description": "Whether to deduct estimated fuel costs",
                    },
                    "include_commission": {
                        "type": "boolean",
                        "description": "Whether to deduct platform commission",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "optimize_route",
            "description": (
                "Suggest the optimal route between origin and destination "
                "in Ghana, considering road conditions, distance, estimated "
                "travel time, fuel stops, and weigh bridge locations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_lat": {
                        "type": "number",
                        "description": "Origin latitude",
                    },
                    "origin_lng": {
                        "type": "number",
                        "description": "Origin longitude",
                    },
                    "origin_city": {
                        "type": "string",
                        "description": "Origin city name",
                    },
                    "dest_lat": {
                        "type": "number",
                        "description": "Destination latitude",
                    },
                    "dest_lng": {
                        "type": "number",
                        "description": "Destination longitude",
                    },
                    "dest_city": {
                        "type": "string",
                        "description": "Destination city name",
                    },
                    "vehicle_type": {
                        "type": "string",
                        "description": "Vehicle type for road suitability",
                    },
                    "avoid_tolls": {
                        "type": "boolean",
                        "description": "Whether to avoid toll roads",
                    },
                },
                "required": ["origin_city", "dest_city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "answer_platform_question",
            "description": (
                "Answer questions about how the LoadMoveGH platform works. "
                "Covers: registration, KYC, posting loads, bidding, escrow, "
                "wallet deposits/withdrawals, commissions, dispute process, "
                "safety features, and account management."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The user's question about the platform",
                    },
                    "topic": {
                        "type": "string",
                        "enum": [
                            "registration", "kyc", "posting_loads",
                            "bidding", "escrow", "wallet", "commissions",
                            "disputes", "safety", "account", "general",
                        ],
                        "description": "Detected topic category",
                    },
                },
                "required": ["question"],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════
#  SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════

def build_system_prompt(*, user_role: str, user_name: str) -> str:
    """Role-aware system prompt for the assistant."""
    role_context = {
        "courier": (
            "The user is a courier/driver on LoadMoveGH. Help them find "
            "profitable loads, optimise routes, understand pricing, forecast "
            "earnings, and navigate the platform. Be practical and numbers-driven."
        ),
        "shipper": (
            "The user is a shipper on LoadMoveGH. Help them post loads "
            "efficiently, understand market pricing, choose reliable couriers, "
            "manage escrow payments, and track shipments."
        ),
    }

    return f"""You are the LoadMoveGH AI Assistant — a smart freight advisor embedded in Ghana's leading freight marketplace app.

IDENTITY
- Name: LoadMove AI
- Platform: LoadMoveGH — connecting shippers with couriers across Ghana & West Africa
- Currency: Ghana Cedi (GHS)
- Region: Ghana (16 regions), expanding to West Africa

USER CONTEXT
- Name: {user_name}
- Role: {user_role}
- {role_context.get(user_role, role_context["courier"])}

CAPABILITIES
You have access to these tools — use them proactively when relevant:
1. suggest_best_loads — Find and rank loads matching the user's profile
2. recommend_pricing — Get AI price recommendations for a load/bid
3. show_profit_forecast — Project earnings or spending over time
4. optimize_route — Suggest the best route between two points in Ghana
5. answer_platform_question — Answer how-to questions about LoadMoveGH

GUIDELINES
- Be concise but helpful. Use bullet points for lists.
- Always show amounts in GHS with proper formatting (e.g. GHS 1,250.00).
- When recommending prices, explain the key factors.
- For route advice, mention road conditions, rest stops, and estimated time.
- Proactively use tools when the user's question implies needing data.
- If you don't have enough information, ask clarifying questions.
- Be friendly and professional. Use the user's name occasionally.
- Never fabricate data — if a tool returns no results, say so honestly.
- Keep responses focused on freight, logistics, and the platform.
"""


# ═══════════════════════════════════════════════════════════════
#  OPENAI CLIENT
# ═══════════════════════════════════════════════════════════════

class OpenAIAssistant:
    """
    Stateless assistant that takes a message history, calls OpenAI with
    function calling, executes tools, and returns the final reply.

    Usage::

        assistant = OpenAIAssistant(tool_executor=my_executor)
        reply = await assistant.chat(messages, user_role="courier", user_name="Kofi")
    """

    def __init__(self, tool_executor):
        """
        Parameters
        ----------
        tool_executor : callable
            An async function(tool_name: str, arguments: dict) -> dict
            that executes the named tool and returns a JSON-serializable result.
        """
        self._tool_executor = tool_executor

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        user_role: str = "courier",
        user_name: str = "User",
    ) -> AssistantReply:
        """
        Send messages to OpenAI, execute any tool calls, and return
        the final assistant reply.
        """
        system_prompt = build_system_prompt(
            user_role=user_role, user_name=user_name,
        )

        # Prepend system message
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        all_tool_calls: list[ToolCall] = []
        all_tool_results: list[dict[str, Any]] = []
        total_prompt = 0
        total_completion = 0
        model_used = ""
        start = time.monotonic()

        for _round in range(_MAX_TOOL_ROUNDS):
            response_data = await self._call_openai(full_messages)

            usage = response_data.get("usage", {})
            total_prompt += usage.get("prompt_tokens", 0)
            total_completion += usage.get("completion_tokens", 0)
            model_used = response_data.get("model", settings.OPENAI_MODEL)

            choice = response_data["choices"][0]
            assistant_msg = choice["message"]

            # ── No tool calls → final reply ─────────────────────
            if not assistant_msg.get("tool_calls"):
                elapsed = int((time.monotonic() - start) * 1000)
                return AssistantReply(
                    content=assistant_msg.get("content", ""),
                    tool_calls_made=all_tool_calls,
                    tool_results=all_tool_results,
                    model=model_used,
                    prompt_tokens=total_prompt,
                    completion_tokens=total_completion,
                    latency_ms=elapsed,
                )

            # ── Has tool calls → execute them ───────────────────
            full_messages.append(assistant_msg)

            for tc in assistant_msg["tool_calls"]:
                fn = tc["function"]
                try:
                    args = json.loads(fn["arguments"])
                except (json.JSONDecodeError, TypeError):
                    args = {}

                tool_call = ToolCall(
                    id=tc["id"], name=fn["name"], arguments=args,
                )
                all_tool_calls.append(tool_call)

                logger.info(
                    "Tool call: %s(%s)", fn["name"],
                    json.dumps(args, default=str)[:200],
                )

                # Execute the tool
                try:
                    result = await self._tool_executor(fn["name"], args)
                except Exception as exc:
                    logger.exception("Tool execution failed: %s", fn["name"])
                    result = {"error": str(exc)}

                all_tool_results.append(result)

                # Feed tool result back to the model
                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, default=str),
                })

        # Exhausted rounds — return whatever we have
        elapsed = int((time.monotonic() - start) * 1000)
        return AssistantReply(
            content="I'm having trouble completing that request. Please try again.",
            tool_calls_made=all_tool_calls,
            tool_results=all_tool_results,
            model=model_used,
            prompt_tokens=total_prompt,
            completion_tokens=total_completion,
            latency_ms=elapsed,
        )

    async def _call_openai(
        self, messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Make a single call to the OpenAI Chat Completions API."""
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "tools": TOOL_DEFINITIONS,
            "tool_choice": "auto",
            "temperature": settings.OPENAI_TEMPERATURE,
            "max_tokens": settings.OPENAI_MAX_TOKENS,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                _OPENAI_URL, headers=headers, json=payload,
            )
            response.raise_for_status()
            return response.json()
