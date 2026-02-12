"""
LoadMoveGH — AI Assistant Tool Implementations
===============================================

Each function here is called by the OpenAI function-calling loop when the
model decides it needs external data.  All tools are async and receive a
database session for live data access.

Tools
-----
1. suggest_best_loads     — query load board + AI match scoring
2. recommend_pricing      — run the ML pricing engine
3. show_profit_forecast   — compute earnings projection
4. optimize_route         — route planning with Ghana knowledge
5. answer_platform_question — retrieve platform knowledge base
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.freight import (
    FreightBid,
    FreightListing,
    FreightTrip,
    ListingStatus,
    TripStatus,
)
from app.models.wallet import Transaction, Wallet

logger = logging.getLogger("loadmovegh.ai.tools")


# ═══════════════════════════════════════════════════════════════
#  GHANA KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════

# Major city coordinates for route planning
GHANA_CITIES: dict[str, tuple[float, float]] = {
    "accra": (5.6037, -0.1870),
    "kumasi": (6.6885, -1.6244),
    "tamale": (9.4034, -0.8424),
    "takoradi": (4.8976, -1.7554),
    "tema": (5.6698, -0.0166),
    "cape coast": (5.1036, -1.2466),
    "sunyani": (7.3397, -2.3266),
    "ho": (6.6016, 0.4684),
    "bolgatanga": (10.7855, -0.8515),
    "wa": (10.0588, -2.5099),
    "koforidua": (6.0940, -0.2593),
    "techiman": (7.5829, -1.9376),
    "obuasi": (6.2055, -1.6604),
    "nkawkaw": (6.5530, -0.7632),
    "winneba": (5.3545, -0.6290),
}

# Major route corridors with distance/time data
GHANA_ROUTES: dict[str, dict[str, Any]] = {
    "accra-kumasi": {
        "distance_km": 252,
        "estimated_hours": 4.5,
        "road_type": "Highway (N6)",
        "condition": "Good — recently resurfaced",
        "fuel_stops": ["Nsawam", "Nkawkaw", "Konongo"],
        "weigh_bridges": ["Ofankor", "Ejisu"],
        "notes": "Heavy traffic leaving Accra before 6am. Best departure 5:30am.",
    },
    "accra-tamale": {
        "distance_km": 607,
        "estimated_hours": 10,
        "road_type": "Highway (N6 → N10)",
        "condition": "Good to Kumasi, variable Kumasi–Tamale",
        "fuel_stops": ["Nsawam", "Nkawkaw", "Kumasi", "Techiman", "Kintampo"],
        "weigh_bridges": ["Ofankor", "Ejisu", "Buipe"],
        "notes": "Plan overnight stop in Kumasi or Techiman for long hauls.",
    },
    "accra-takoradi": {
        "distance_km": 218,
        "estimated_hours": 3.5,
        "road_type": "Highway (N1)",
        "condition": "Good — dual carriageway most of the way",
        "fuel_stops": ["Winneba", "Cape Coast"],
        "weigh_bridges": ["Kasoa"],
        "notes": "Coastal route with sea breeze. Watch for fog near Cape Coast early morning.",
    },
    "tema-takoradi": {
        "distance_km": 227,
        "estimated_hours": 4,
        "road_type": "Highway (N1)",
        "condition": "Good",
        "fuel_stops": ["Kasoa", "Winneba", "Cape Coast"],
        "weigh_bridges": ["Tema Port Exit", "Kasoa"],
        "notes": "High container traffic from Tema Port. Allow extra time for port exits.",
    },
    "kumasi-tamale": {
        "distance_km": 379,
        "estimated_hours": 6,
        "road_type": "Highway (N10)",
        "condition": "Mixed — good to Techiman, variable Techiman–Tamale",
        "fuel_stops": ["Techiman", "Kintampo", "Buipe"],
        "weigh_bridges": ["Ejisu", "Buipe"],
        "notes": "Rainy season (May–Oct) can cause delays near Kintampo.",
    },
    "kumasi-takoradi": {
        "distance_km": 230,
        "estimated_hours": 4,
        "road_type": "Highway (N8)",
        "condition": "Good — mining corridor, well maintained",
        "fuel_stops": ["Obuasi", "Tarkwa"],
        "weigh_bridges": ["Obuasi"],
        "notes": "Mining trucks frequent. Drive defensively.",
    },
}

# Platform knowledge base
PLATFORM_FAQ: dict[str, str] = {
    "registration": (
        "**How to Register:**\n"
        "1. Download the LoadMoveGH app or visit loadmovegh.com\n"
        "2. Choose your role: Courier (driver) or Shipper\n"
        "3. Enter your email or Ghana phone number (024/054/020 etc.)\n"
        "4. Verify via OTP or email link\n"
        "5. Complete KYC: upload Ghana Card/Passport, business registration (if company), "
        "and vehicle documents (couriers)\n"
        "6. KYC review takes 1–3 business days\n\n"
        "Both individuals and companies can register."
    ),
    "kyc": (
        "**KYC (Know Your Customer):**\n"
        "- Required documents: Ghana Card or Passport, TIN certificate\n"
        "- Companies: Business registration certificate, director ID\n"
        "- Couriers also need: Driver's licence, vehicle registration, insurance\n"
        "- Status: Pending → Verified or Rejected (with reason)\n"
        "- Verified users get a green badge and higher bid trust score"
    ),
    "posting_loads": (
        "**Posting Loads (Shippers):**\n"
        "1. Go to 'Post Load' tab\n"
        "2. Enter pickup and delivery locations\n"
        "3. Specify cargo type, weight, vehicle requirement\n"
        "4. Set urgency level (standard/express/urgent)\n"
        "5. Set your budget or use AI price recommendation\n"
        "6. Publish — couriers can now bid\n\n"
        "Your load appears on the Load Board for all matching couriers."
    ),
    "bidding": (
        "**Bidding Process:**\n"
        "- Couriers browse the Load Board and bid on available loads\n"
        "- Each bid includes: amount (GHS), estimated pickup & delivery time, optional note\n"
        "- AI shows a recommended price range so you bid competitively\n"
        "- Shippers review bids and accept the best one\n"
        "- Accepted bid → escrow hold → trip starts\n"
        "- You can withdraw a bid anytime before acceptance"
    ),
    "escrow": (
        "**Escrow System:**\n"
        "- When a bid is accepted, the agreed amount is held in escrow\n"
        "- Neither party can access the funds until delivery is confirmed\n"
        "- Courier delivers → shipper confirms → funds released minus 5% commission\n"
        "- If delivery fails, escrow is refunded to the shipper\n"
        "- Disputes are handled by the LoadMoveGH support team"
    ),
    "wallet": (
        "**Wallet & Payments:**\n"
        "- Every user has a GHS wallet\n"
        "- Deposit via MTN MoMo, Vodafone Cash, or AirtelTigo Money\n"
        "- Minimum deposit: GHS 1.00 | Max transaction: GHS 50,000\n"
        "- Withdraw to any MoMo number (1% fee, min GHS 0.50, max GHS 10.00)\n"
        "- View full transaction history with filters"
    ),
    "commissions": (
        "**Platform Commissions:**\n"
        "- LoadMoveGH charges 5% commission on completed deliveries\n"
        "- Commission is deducted from the escrow before releasing to courier\n"
        "- Example: GHS 1,000 delivery → GHS 50 commission → GHS 950 to courier\n"
        "- No commission on cancelled or disputed trips\n"
        "- Withdrawal fee: 1% (min GHS 0.50, max GHS 10.00)"
    ),
    "disputes": (
        "**Dispute Resolution:**\n"
        "- Either party can open a dispute during an active trip\n"
        "- Common reasons: damage, delay, non-delivery, payment issues\n"
        "- A support agent reviews evidence from both sides\n"
        "- Resolution options: full refund, partial refund, release to courier\n"
        "- Average resolution time: 2–5 business days\n"
        "- Repeated disputes affect your trust score"
    ),
    "safety": (
        "**Safety Features:**\n"
        "- All users are KYC-verified\n"
        "- AI fraud detection monitors for suspicious activity\n"
        "- Real-time GPS tracking for all active shipments\n"
        "- Escrow protects both parties\n"
        "- 24/7 support hotline for emergencies\n"
        "- Courier ratings visible to shippers before accepting bids"
    ),
    "account": (
        "**Account Management:**\n"
        "- Update profile, phone, email in Settings\n"
        "- Switch between courier and shipper roles (if both registered)\n"
        "- View your ratings, completion rate, and stats\n"
        "- Deactivate account: contact support\n"
        "- Two-factor authentication available for extra security"
    ),
    "general": (
        "**About LoadMoveGH:**\n"
        "LoadMoveGH is Ghana's AI-powered freight marketplace connecting "
        "shippers who need to move cargo with couriers who have the vehicles. "
        "Features include: AI pricing, smart load matching, escrow payments, "
        "real-time tracking, and Mobile Money integration.\n\n"
        "For any help, ask me a question or contact support@loadmovegh.com."
    ),
}


# ═══════════════════════════════════════════════════════════════
#  HELPER: Haversine distance
# ═══════════════════════════════════════════════════════════════

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in km between two lat/lng points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _find_route_key(origin: str, dest: str) -> str | None:
    """Try to match a known route corridor."""
    o = origin.lower().strip()
    d = dest.lower().strip()
    for key in GHANA_ROUTES:
        cities = key.split("-")
        if (o in cities[0] or cities[0] in o) and (d in cities[1] or cities[1] in d):
            return key
        if (d in cities[0] or cities[0] in d) and (o in cities[1] or cities[1] in o):
            return key
    return None


# ═══════════════════════════════════════════════════════════════
#  TOOL EXECUTOR — the single dispatch point
# ═══════════════════════════════════════════════════════════════

class ToolExecutor:
    """
    Executes AI assistant tools using live database queries.

    Instantiate with a DB session and the current user's ID,
    then pass ``self.execute`` as the ``tool_executor`` callback
    to ``OpenAIAssistant``.
    """

    def __init__(self, db: AsyncSession, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch to the correct tool function."""
        dispatcher = {
            "suggest_best_loads": self._suggest_best_loads,
            "recommend_pricing": self._recommend_pricing,
            "show_profit_forecast": self._show_profit_forecast,
            "optimize_route": self._optimize_route,
            "answer_platform_question": self._answer_platform_question,
        }
        handler = dispatcher.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}
        return await handler(arguments)

    # ─── Tool 1: Suggest Best Loads ─────────────────────────

    async def _suggest_best_loads(self, args: dict[str, Any]) -> dict[str, Any]:
        lat = args.get("latitude", 5.6037)  # Default Accra
        lng = args.get("longitude", -0.1870)
        vehicle = args.get("vehicle_type")
        max_dist = args.get("max_distance_km", 100)
        cargo_pref = args.get("cargo_preference")
        limit = min(args.get("limit", 5), 10)

        # Query open listings
        stmt = select(FreightListing).where(
            FreightListing.status == ListingStatus.open,
        )
        if vehicle:
            stmt = stmt.where(FreightListing.vehicle_type == vehicle)
        if cargo_pref:
            stmt = stmt.where(FreightListing.cargo_type == cargo_pref)

        stmt = stmt.order_by(FreightListing.created_at.desc()).limit(50)
        result = await self.db.execute(stmt)
        listings = result.scalars().all()

        # Score by proximity and sort
        scored = []
        for listing in listings:
            pickup_lat = float(listing.origin_lat or 0)
            pickup_lng = float(listing.origin_lng or 0)
            dist = _haversine(lat, lng, pickup_lat, pickup_lng)

            if dist > max_dist:
                continue

            # Simple scoring: closer + higher budget = better
            proximity_score = max(0, 100 - (dist / max_dist * 100))
            budget_score = min(100, float(listing.budget_max or 0) / 20)  # normalize
            match_score = round(proximity_score * 0.6 + budget_score * 0.4, 1)

            scored.append({
                "listing_id": str(listing.id),
                "title": listing.title,
                "route": f"{listing.origin_city} → {listing.dest_city}",
                "distance_km": round(float(listing.distance_km or 0), 1),
                "pickup_distance_km": round(dist, 1),
                "cargo_type": str(listing.cargo_type.value if listing.cargo_type else "general"),
                "vehicle_type": str(listing.vehicle_type.value if listing.vehicle_type else "any"),
                "weight_kg": float(listing.weight_kg or 0),
                "budget": f"GHS {float(listing.budget_min or 0):,.2f} – {float(listing.budget_max or 0):,.2f}",
                "urgency": str(listing.urgency.value if listing.urgency else "standard"),
                "match_score": match_score,
                "pickup_date": str(listing.pickup_date),
                "bid_count": listing.bid_count or 0,
            })

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        top = scored[:limit]

        return {
            "loads_found": len(top),
            "total_available": len(scored),
            "loads": top,
            "search_params": {
                "location": f"{lat:.4f}, {lng:.4f}",
                "max_distance_km": max_dist,
                "vehicle_type": vehicle or "any",
            },
        }

    # ─── Tool 2: Recommend Pricing ──────────────────────────

    async def _recommend_pricing(self, args: dict[str, Any]) -> dict[str, Any]:
        distance = args.get("distance_km", 0)
        weight = args.get("weight_kg", 0)
        cargo = args.get("cargo_type", "general")
        vehicle = args.get("vehicle_type", "pickup")
        urgency = args.get("urgency", "standard")
        origin = args.get("origin_city", "")
        dest = args.get("dest_city", "")

        # Base rate calculation (GHS per km per ton)
        base_rate_per_km_per_ton = 3.50  # Market average in Ghana

        # Adjustments
        cargo_multiplier = {
            "general": 1.0, "perishable": 1.3, "hazardous": 1.5,
            "fragile": 1.2, "bulk": 0.9, "liquid": 1.4, "livestock": 1.3,
        }.get(cargo, 1.0)

        urgency_multiplier = {
            "standard": 1.0, "express": 1.2, "urgent": 1.5, "scheduled": 0.95,
        }.get(urgency, 1.0)

        vehicle_multiplier = {
            "pickup": 0.8, "van": 0.9, "flatbed": 1.0, "box_truck": 1.1,
            "trailer": 1.3, "refrigerated": 1.6, "tanker": 1.5,
        }.get(vehicle, 1.0)

        # Fuel cost estimate
        fuel_price = settings.PRICING_DEFAULT_DIESEL_PRICE  # GHS/litre
        fuel_consumption = 0.35  # litres/km avg for freight
        fuel_cost = distance * fuel_consumption * fuel_price

        # Total estimate
        weight_tons = max(weight / 1000, 0.1)
        base_price = distance * weight_tons * base_rate_per_km_per_ton
        adjusted = base_price * cargo_multiplier * urgency_multiplier * vehicle_multiplier

        # Price range (±15%)
        price_min = round(max(adjusted * 0.85, fuel_cost * 1.2), 2)
        price_max = round(adjusted * 1.15, 2)
        recommended = round(adjusted, 2)

        # Commission
        commission = round(recommended * settings.PLATFORM_COMMISSION_RATE, 2)
        courier_net = round(recommended - commission, 2)

        return {
            "recommended_price": f"GHS {recommended:,.2f}",
            "price_range": {
                "min": f"GHS {price_min:,.2f}",
                "max": f"GHS {price_max:,.2f}",
            },
            "breakdown": {
                "base_rate": f"GHS {base_rate_per_km_per_ton}/km/ton",
                "distance_km": distance,
                "weight_kg": weight,
                "cargo_multiplier": f"{cargo_multiplier}x ({cargo})",
                "urgency_multiplier": f"{urgency_multiplier}x ({urgency})",
                "vehicle_multiplier": f"{vehicle_multiplier}x ({vehicle})",
                "estimated_fuel_cost": f"GHS {fuel_cost:,.2f}",
            },
            "for_courier": {
                "platform_commission": f"{settings.PLATFORM_COMMISSION_RATE * 100}%",
                "commission_amount": f"GHS {commission:,.2f}",
                "net_earnings": f"GHS {courier_net:,.2f}",
            },
            "route": f"{origin} → {dest}" if origin and dest else None,
            "advice": _pricing_advice(
                recommended, fuel_cost, distance, urgency, cargo,
            ),
        }

    # ─── Tool 3: Profit Forecast ────────────────────────────

    async def _show_profit_forecast(self, args: dict[str, Any]) -> dict[str, Any]:
        target_user_id = args.get("user_id")
        if target_user_id:
            try:
                uid = uuid.UUID(target_user_id)
            except ValueError:
                uid = self.user_id
        else:
            uid = self.user_id

        days = args.get("forecast_days", 30)
        include_fuel = args.get("include_fuel_costs", True)
        include_commission = args.get("include_commission", True)

        # Historical data: completed trips in last 90 days
        since = datetime.now(timezone.utc) - timedelta(days=90)

        trip_stmt = select(FreightTrip).where(
            and_(
                FreightTrip.courier_id == uid,
                FreightTrip.status == TripStatus.delivered,
                FreightTrip.delivered_at >= since,
            )
        )
        result = await self.db.execute(trip_stmt)
        trips = result.scalars().all()

        # Wallet balance
        wallet_stmt = select(Wallet).where(Wallet.user_id == uid)
        w_result = await self.db.execute(wallet_stmt)
        wallet = w_result.scalar_one_or_none()

        if not trips:
            return {
                "forecast_days": days,
                "historical_trips": 0,
                "message": (
                    "Not enough trip history to generate a forecast. "
                    "Complete a few deliveries first, and I'll be able to "
                    "project your earnings accurately."
                ),
                "wallet_balance": f"GHS {float(wallet.balance):,.2f}" if wallet else "N/A",
            }

        # Compute averages
        total_revenue = 0.0
        total_distance = 0.0
        for trip in trips:
            # Revenue = accepted bid amount
            if trip.accepted_bid_amount:
                total_revenue += float(trip.accepted_bid_amount)
            total_distance += float(trip.distance_km or 0)

        avg_per_trip = total_revenue / len(trips) if trips else 0
        trips_per_day = len(trips) / 90
        daily_revenue = avg_per_trip * trips_per_day

        # Costs
        daily_fuel = (total_distance / 90) * 0.35 * settings.PRICING_DEFAULT_DIESEL_PRICE if include_fuel else 0
        daily_commission = daily_revenue * settings.PLATFORM_COMMISSION_RATE if include_commission else 0
        daily_profit = daily_revenue - daily_fuel - daily_commission

        forecast_revenue = round(daily_revenue * days, 2)
        forecast_fuel = round(daily_fuel * days, 2)
        forecast_commission = round(daily_commission * days, 2)
        forecast_profit = round(daily_profit * days, 2)

        return {
            "forecast_days": days,
            "historical_basis": {
                "trips_last_90_days": len(trips),
                "total_revenue": f"GHS {total_revenue:,.2f}",
                "avg_per_trip": f"GHS {avg_per_trip:,.2f}",
                "trips_per_day": round(trips_per_day, 2),
            },
            "forecast": {
                "projected_revenue": f"GHS {forecast_revenue:,.2f}",
                "estimated_fuel_costs": f"GHS {forecast_fuel:,.2f}" if include_fuel else "N/A",
                "platform_commission": f"GHS {forecast_commission:,.2f}" if include_commission else "N/A",
                "projected_net_profit": f"GHS {forecast_profit:,.2f}",
                "projected_trips": round(trips_per_day * days),
            },
            "wallet_balance": f"GHS {float(wallet.balance):,.2f}" if wallet else "N/A",
            "tips": _profit_tips(daily_profit, trips_per_day),
        }

    # ─── Tool 4: Route Optimization ─────────────────────────

    async def _optimize_route(self, args: dict[str, Any]) -> dict[str, Any]:
        origin = args.get("origin_city", "")
        dest = args.get("dest_city", "")
        vehicle = args.get("vehicle_type", "")
        avoid_tolls = args.get("avoid_tolls", False)

        # Try to find a known route
        route_key = _find_route_key(origin, dest)

        if route_key:
            route = GHANA_ROUTES[route_key]
            return {
                "route": f"{origin} → {dest}",
                "distance_km": route["distance_km"],
                "estimated_time": f"{route['estimated_hours']} hours",
                "road_type": route["road_type"],
                "road_condition": route["condition"],
                "fuel_stops": route["fuel_stops"],
                "weigh_bridges": route["weigh_bridges"],
                "tips": route["notes"],
                "estimated_fuel_cost": f"GHS {route['distance_km'] * 0.35 * settings.PRICING_DEFAULT_DIESEL_PRICE:,.2f}",
                "vehicle_advice": _vehicle_route_advice(vehicle, route),
            }

        # Fallback: compute straight-line distance
        origin_coords = GHANA_CITIES.get(origin.lower().strip())
        dest_coords = GHANA_CITIES.get(dest.lower().strip())

        if origin_coords and dest_coords:
            straight_dist = _haversine(
                origin_coords[0], origin_coords[1],
                dest_coords[0], dest_coords[1],
            )
            road_dist = round(straight_dist * 1.3, 1)  # Roads are ~30% longer
            est_hours = round(road_dist / 60, 1)  # ~60 km/h avg

            return {
                "route": f"{origin} → {dest}",
                "estimated_distance_km": road_dist,
                "estimated_time": f"{est_hours} hours",
                "road_type": "Mixed — verify locally",
                "road_condition": "Check with local drivers for current conditions",
                "fuel_stops": "Plan stops every 100–150 km",
                "estimated_fuel_cost": f"GHS {road_dist * 0.35 * settings.PRICING_DEFAULT_DIESEL_PRICE:,.2f}",
                "note": "This is an estimate. Detailed route data not available for this corridor.",
            }

        return {
            "route": f"{origin} → {dest}",
            "error": "Could not find detailed route data for this corridor.",
            "suggestion": (
                "Try using the city names exactly (e.g. Accra, Kumasi, Tamale, "
                "Takoradi, Tema, Cape Coast, Sunyani, Ho, Bolgatanga, Wa)."
            ),
        }

    # ─── Tool 5: Platform FAQ ───────────────────────────────

    async def _answer_platform_question(self, args: dict[str, Any]) -> dict[str, Any]:
        question = args.get("question", "")
        topic = args.get("topic", "general")

        # Direct topic match
        answer = PLATFORM_FAQ.get(topic, PLATFORM_FAQ["general"])

        # If the topic is "general", try to find a better match from the question
        if topic == "general":
            keywords_to_topics = {
                "register": "registration",
                "sign up": "registration",
                "kyc": "kyc",
                "verify": "kyc",
                "post": "posting_loads",
                "load": "posting_loads",
                "bid": "bidding",
                "escrow": "escrow",
                "wallet": "wallet",
                "deposit": "wallet",
                "withdraw": "wallet",
                "momo": "wallet",
                "mobile money": "wallet",
                "commission": "commissions",
                "fee": "commissions",
                "dispute": "disputes",
                "refund": "disputes",
                "safety": "safety",
                "fraud": "safety",
                "account": "account",
                "profile": "account",
                "password": "account",
            }
            q_lower = question.lower()
            for keyword, t in keywords_to_topics.items():
                if keyword in q_lower:
                    answer = PLATFORM_FAQ[t]
                    topic = t
                    break

        return {
            "topic": topic,
            "answer": answer,
            "question": question,
            "related_topics": _related_topics(topic),
        }


# ═══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _pricing_advice(price: float, fuel: float, distance: float,
                    urgency: str, cargo: str) -> str:
    """Generate contextual pricing advice."""
    margin = price - fuel
    margin_pct = (margin / price * 100) if price > 0 else 0

    tips = []
    if margin_pct < 20:
        tips.append("This route has a thin margin. Consider negotiating a higher price.")
    if urgency == "urgent":
        tips.append("Urgent loads command 30–50% premium. Price accordingly.")
    if cargo in ("hazardous", "perishable"):
        tips.append(f"{cargo.title()} cargo requires special handling — factor in extra costs.")
    if distance > 400:
        tips.append("Long-haul route: factor in driver rest stops and overnight accommodation.")
    if not tips:
        tips.append("This pricing looks healthy for the current market conditions.")

    return " ".join(tips)


def _profit_tips(daily_profit: float, trips_per_day: float) -> list[str]:
    """Generate actionable profit-boosting tips."""
    tips = []
    if trips_per_day < 0.5:
        tips.append("You're averaging less than 1 trip every 2 days. Try expanding your search radius.")
    if daily_profit < 50:
        tips.append("Consider targeting express/urgent loads for 20–50% higher rates.")
    tips.append("Set up notifications for loads on your preferred routes to bid early.")
    tips.append("Maintain a high completion rate (>95%) to rank higher in AI matching.")
    return tips


def _vehicle_route_advice(vehicle: str, route: dict) -> str:
    """Vehicle-specific route advice."""
    if vehicle in ("trailer", "tanker"):
        return "Large vehicles: plan for weigh bridge delays and limited parking."
    if vehicle == "refrigerated":
        return "Ensure fuel stops can handle extended idle time for cooling unit."
    return "Standard vehicle — no special route restrictions."


def _related_topics(current: str) -> list[str]:
    """Suggest related FAQ topics."""
    relations = {
        "registration": ["kyc", "wallet"],
        "kyc": ["registration", "safety"],
        "posting_loads": ["bidding", "escrow"],
        "bidding": ["posting_loads", "commissions"],
        "escrow": ["bidding", "disputes"],
        "wallet": ["commissions", "escrow"],
        "commissions": ["wallet", "bidding"],
        "disputes": ["escrow", "safety"],
        "safety": ["kyc", "disputes"],
        "account": ["registration", "safety"],
        "general": ["registration", "wallet", "bidding"],
    }
    return relations.get(current, ["general"])
