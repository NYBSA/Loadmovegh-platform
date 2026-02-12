"""
LoadMoveGH — AI Load-Matching & Driver Ranking Engine
=====================================================

Scores and ranks couriers for a given freight listing using a
multi-dimensional scoring formula that can be overridden by an
optional ML re-ranker for personalised matching.

════════════════════════════════════════════════════════════════
 SCORING FORMULA (5 Dimensions)
════════════════════════════════════════════════════════════════

Each courier is scored across 5 independent dimensions on a
0–100 scale, then combined with configurable weights into a
single composite score:

  composite = Σ  wᵢ × scoreᵢ(courier, listing)

┌─────────────────────────────────────────────────────────────┐
│  Dimension          │ Weight │ What it captures              │
├─────────────────────┼────────┼───────────────────────────────┤
│ 1. Proximity        │  0.30  │ GPS distance to pickup point  │
│ 2. Reliability      │  0.25  │ Completion %, on-time %,      │
│                     │        │ dispute history               │
│ 3. Acceptance Rate  │  0.15  │ How often courier follows     │
│                     │        │ through on bids               │
│ 4. Vehicle Fit      │  0.15  │ Type match, capacity,         │
│                     │        │ special equipment              │
│ 5. Price Compet.    │  0.15  │ Courier's avg bid vs market   │
│                     │        │ rate for this corridor         │
└─────────────────────┴────────┴───────────────────────────────┘

  • Scores are normalised 0–100 (100 = best)
  • Weights are tunable per urgency level:
    - Urgent loads increase proximity weight to 0.40
    - High-value cargo increases reliability weight to 0.35
  • A minimum threshold (default 30) filters out unsuitable drivers

════════════════════════════════════════════════════════════════
 ML RE-RANKER (Optional, Phase 2)
════════════════════════════════════════════════════════════════

When enough historical match-outcome data exists (which courier
was actually chosen, did the trip succeed, was there a dispute),
a LightGBM Learning-to-Rank (LambdaMART) model can be trained
to re-order the candidates.

Input features = the 5 dimension scores + raw courier stats +
listing features.  Target = binary (1 if courier was selected
AND trip completed successfully).

The ML model captures interaction effects the formula misses,
e.g. "courier X is excellent for refrigerated goods on the
Tema-Kumasi corridor specifically".

Until the ML model is trained, the formula-based ranker is
used exclusively.

════════════════════════════════════════════════════════════════
 REAL-TIME RANKING LOGIC
════════════════════════════════════════════════════════════════

 1. CANDIDATE SELECTION (fast, DB-level filter):
    - is_available = True, is_on_trip = False
    - Vehicle can carry the weight
    - Location within configurable radius (default 150 km)
    - Account is active and KYC verified

 2. SCORING (in-process, per candidate):
    - Compute 5 dimension scores
    - Apply urgency-adjusted weights
    - Compute composite score
    - (Optional) ML re-rank top N

 3. RANKING & FILTERING:
    - Sort by composite descending
    - Apply minimum score threshold
    - Return top K (default 10) with breakdown

 4. AUDIT:
    - Log full ranked list to match_recommendations table
    - Track which courier was eventually chosen (feedback loop)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.ml.features import VEHICLE_MAX_WEIGHT, haversine_km


# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Default dimension weights (sum = 1.0)
DEFAULT_WEIGHTS = {
    "proximity": 0.30,
    "reliability": 0.25,
    "acceptance": 0.15,
    "vehicle_fit": 0.15,
    "pricing": 0.15,
}

# Urgency-adjusted weights
URGENT_WEIGHTS = {
    "proximity": 0.40,
    "reliability": 0.25,
    "acceptance": 0.10,
    "vehicle_fit": 0.15,
    "pricing": 0.10,
}

EXPRESS_WEIGHTS = {
    "proximity": 0.35,
    "reliability": 0.25,
    "acceptance": 0.12,
    "vehicle_fit": 0.15,
    "pricing": 0.13,
}

# High-value cargo weights (electronics, medical, chemicals)
HIGH_VALUE_WEIGHTS = {
    "proximity": 0.20,
    "reliability": 0.35,
    "acceptance": 0.15,
    "vehicle_fit": 0.20,
    "pricing": 0.10,
}

# Maximum radius to consider (km)
MAX_PROXIMITY_RADIUS_KM = 300.0

# Sweet-spot radius: full score within this range
IDEAL_PROXIMITY_KM = 15.0

# Minimum composite score to be included in results
MIN_COMPOSITE_SCORE = 30.0

HIGH_VALUE_CARGO = {"electronics", "medical", "chemicals", "perishables"}

# Vehicle compatibility matrix: required → compatible types
VEHICLE_COMPATIBILITY: dict[str, set[str]] = {
    "motorcycle":   {"motorcycle"},
    "van":          {"van", "box_truck"},
    "box_truck":    {"box_truck", "flatbed", "heavy_truck"},
    "flatbed":      {"flatbed", "heavy_truck"},
    "refrigerated": {"refrigerated"},
    "heavy_truck":  {"heavy_truck"},
    "any":          {"motorcycle", "van", "box_truck", "flatbed", "refrigerated", "heavy_truck"},
}


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class CourierStats:
    """Snapshot of a courier's stats for scoring."""
    user_id: str
    full_name: str

    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    current_city: str = ""
    current_region: str = ""

    # Vehicle
    vehicle_type: str = "any"
    vehicle_capacity_kg: float = 5000
    has_refrigeration: bool = False
    has_gps_tracker: bool = False

    # Performance
    acceptance_rate: float = 0.0
    completion_rate: float = 0.0
    on_time_rate: float = 0.0
    avg_rating: float = 0.0
    total_ratings: int = 0

    # Volume
    total_trips_completed: int = 0
    total_trips_cancelled: int = 0
    total_disputes: int = 0
    disputes_lost: int = 0
    member_since_days: int = 0

    # Pricing
    avg_price_vs_market: float = 1.0  # <1 = cheaper than market


@dataclass
class ListingContext:
    """The listing attributes needed for matching."""
    listing_id: str
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    pickup_city: str = ""
    delivery_city: str = ""
    weight_kg: float = 0.0
    cargo_type: str = "general"
    required_vehicle_type: str = "any"
    urgency: str = "standard"
    shipper_price: Optional[float] = None
    ai_suggested_price: Optional[float] = None


@dataclass
class DimensionScores:
    """Breakdown of the 5 scoring dimensions (0–100 each)."""
    proximity: float = 0.0
    reliability: float = 0.0
    acceptance: float = 0.0
    vehicle_fit: float = 0.0
    pricing: float = 0.0


@dataclass
class MatchResult:
    """A single courier's match result."""
    courier_id: str
    courier_name: str
    rank: int = 0
    composite_score: float = 0.0
    dimensions: DimensionScores = field(default_factory=DimensionScores)
    distance_km: Optional[float] = None
    vehicle_type: str = ""
    is_available: bool = True

    def to_dict(self) -> dict:
        return {
            "courier_id": self.courier_id,
            "courier_name": self.courier_name,
            "rank": self.rank,
            "composite_score": round(self.composite_score, 2),
            "dimensions": {
                "proximity": round(self.dimensions.proximity, 2),
                "reliability": round(self.dimensions.reliability, 2),
                "acceptance": round(self.dimensions.acceptance, 2),
                "vehicle_fit": round(self.dimensions.vehicle_fit, 2),
                "pricing": round(self.dimensions.pricing, 2),
            },
            "distance_km": round(self.distance_km, 1) if self.distance_km else None,
            "vehicle_type": self.vehicle_type,
        }


# ═══════════════════════════════════════════════════════════════
#  DIMENSION SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def score_proximity(
    courier: CourierStats,
    listing: ListingContext,
) -> tuple[float, Optional[float]]:
    """
    Score: 0–100 based on GPS distance from courier to pickup point.

    Formula (exponential decay):
      score = 100 × exp(-distance / decay_constant)

    Where decay_constant is tuned so that:
      • 0–15 km  → 85–100 (excellent)
      • 15–50 km → 55–85  (good)
      • 50–150 km → 20–55 (acceptable)
      • >150 km  → <20    (poor)

    Returns (score, distance_km).
    """
    if (
        courier.latitude is None
        or courier.longitude is None
        or listing.pickup_lat is None
        or listing.pickup_lng is None
    ):
        # No GPS data → neutral score (50) so courier isn't penalised
        return 50.0, None

    distance = haversine_km(
        courier.latitude, courier.longitude,
        listing.pickup_lat, listing.pickup_lng,
    )

    if distance > MAX_PROXIMITY_RADIUS_KM:
        return 0.0, distance

    # Exponential decay with decay constant of 80 km
    decay = 80.0
    score = 100.0 * math.exp(-distance / decay)

    # Bonus for being very close (< ideal radius)
    if distance <= IDEAL_PROXIMITY_KM:
        score = min(100.0, score + 10.0)

    return round(max(0.0, min(100.0, score)), 2), round(distance, 1)


def score_reliability(courier: CourierStats) -> float:
    """
    Score: 0–100 based on completion history and dispute record.

    Formula:
      base = 0.50 × completion_rate_pct
           + 0.25 × on_time_rate_pct
           + 0.15 × (1 - dispute_penalty) × 100
           + 0.10 × experience_bonus

    Where:
      dispute_penalty = min(disputes_lost / max(total_trips, 1), 0.5)
      experience_bonus = min(total_trips / 50, 1.0) × 100
    """
    total_trips = max(courier.total_trips_completed + courier.total_trips_cancelled, 1)

    completion_pct = courier.completion_rate * 100  # Already 0.0–1.0

    on_time_pct = courier.on_time_rate * 100

    # Dispute penalty: each lost dispute hurts, capped at 50%
    dispute_penalty = min(courier.disputes_lost / total_trips, 0.5)
    dispute_score = (1.0 - dispute_penalty) * 100

    # Experience bonus: ramps up to 100 over 50 completed trips
    experience_bonus = min(courier.total_trips_completed / 50.0, 1.0) * 100

    score = (
        0.50 * completion_pct
        + 0.25 * on_time_pct
        + 0.15 * dispute_score
        + 0.10 * experience_bonus
    )

    # New courier adjustment: if < 3 trips, reduce confidence
    if courier.total_trips_completed < 3:
        score = score * 0.7 + 35.0 * 0.3  # Blend toward 35 (neutral-low)

    return round(max(0.0, min(100.0, score)), 2)


def score_acceptance(courier: CourierStats) -> float:
    """
    Score: 0–100 based on bid follow-through rate.

    Formula:
      score = acceptance_rate × 100

    With adjustments:
      • < 5 total bids → blend toward 50 (insufficient data)
      • Cancelled trips count negatively (beyond simple acceptance)

    A courier who accepts bids and completes them is rewarded;
    one who frequently cancels after accepting is penalised.
    """
    base = courier.acceptance_rate * 100

    # Cancellation penalty
    total_assigned = max(
        courier.total_trips_completed + courier.total_trips_cancelled, 1
    )
    cancel_rate = courier.total_trips_cancelled / total_assigned
    penalty = cancel_rate * 30  # Up to 30 point penalty

    score = base - penalty

    # New courier: blend toward neutral
    total_bids = courier.total_trips_completed + courier.total_trips_cancelled
    if total_bids < 5:
        score = score * 0.5 + 50.0 * 0.5

    return round(max(0.0, min(100.0, score)), 2)


def score_vehicle_fit(
    courier: CourierStats,
    listing: ListingContext,
) -> float:
    """
    Score: 0–100 based on vehicle suitability for the load.

    Components:
      1. Type compatibility (0 or 40 points)
      2. Capacity headroom (0–30 points)
      3. Special equipment (0–20 points)
      4. GPS tracker bonus (0–10 points)

    A courier with the wrong vehicle type scores 0 (hard filter).
    """
    score = 0.0

    # 1. Type compatibility (hard requirement)
    required = listing.required_vehicle_type.lower()
    courier_vtype = (courier.vehicle_type or "any").lower()

    compatible_types = VEHICLE_COMPATIBILITY.get(required, set())
    if required == "any":
        # Any vehicle works, but bigger is better for heavy loads
        score += 40.0
    elif courier_vtype in compatible_types:
        score += 40.0
    else:
        return 0.0  # Incompatible → hard zero

    # 2. Capacity headroom: ideal is 60–90% utilisation
    if courier.vehicle_capacity_kg > 0:
        utilisation = listing.weight_kg / courier.vehicle_capacity_kg
        if utilisation > 1.0:
            return 0.0  # Overweight → hard zero
        elif utilisation <= 0.0:
            score += 15.0
        elif 0.3 <= utilisation <= 0.9:
            score += 30.0  # Sweet spot
        elif utilisation < 0.3:
            score += 20.0  # Oversized truck → slight penalty
        else:  # 0.9–1.0
            score += 22.0  # Near capacity → a bit risky
    else:
        score += 15.0

    # 3. Special equipment
    if listing.cargo_type in ("perishables",) and courier.has_refrigeration:
        score += 20.0
    elif listing.cargo_type in ("perishables",) and not courier.has_refrigeration:
        score -= 10.0  # Penalty for missing refrigeration
    else:
        score += 10.0  # Neutral for non-perishable

    # 4. GPS tracker (important for high-value cargo)
    if courier.has_gps_tracker:
        if listing.cargo_type in HIGH_VALUE_CARGO:
            score += 10.0
        else:
            score += 5.0

    return round(max(0.0, min(100.0, score)), 2)


def score_pricing(
    courier: CourierStats,
    listing: ListingContext,
) -> float:
    """
    Score: 0–100 based on pricing competitiveness.

    A courier who consistently bids near or below market rate scores
    higher; one who bids significantly above market scores lower.

    Formula:
      ratio = courier.avg_price_vs_market
      score = 100 × exp(-2 × max(ratio - 0.8, 0))

    Sweet spot: ratio 0.8–1.0 (competitive but not suspiciously cheap).
    Penalty ramps for ratio > 1.2 (expensive).
    Slight penalty for ratio < 0.6 (too cheap → quality concern).
    """
    ratio = courier.avg_price_vs_market

    if ratio <= 0 or courier.total_trips_completed == 0:
        # No data → neutral
        return 50.0

    # Optimal zone: 0.80–1.05
    if 0.80 <= ratio <= 1.05:
        score = 90.0 + (1.05 - ratio) * 40  # 90–100
    elif ratio < 0.80:
        # Suspiciously cheap — slight concern
        score = 70.0 + ratio * 25  # ~87 at 0.70, ~75 at 0.60
        if ratio < 0.50:
            score = max(40.0, score - 20)  # Quality concern
    else:
        # Expensive: exponential penalty above 1.05
        overshoot = ratio - 1.05
        score = 90.0 * math.exp(-3.0 * overshoot)

    return round(max(0.0, min(100.0, score)), 2)


# ═══════════════════════════════════════════════════════════════
#  COMPOSITE SCORER
# ═══════════════════════════════════════════════════════════════

def select_weights(listing: ListingContext) -> dict[str, float]:
    """Choose dimension weights based on listing characteristics."""
    urgency = listing.urgency.lower()
    cargo = listing.cargo_type.lower()

    if cargo in HIGH_VALUE_CARGO:
        return HIGH_VALUE_WEIGHTS.copy()
    elif urgency == "urgent":
        return URGENT_WEIGHTS.copy()
    elif urgency == "express":
        return EXPRESS_WEIGHTS.copy()
    else:
        return DEFAULT_WEIGHTS.copy()


def score_courier(
    courier: CourierStats,
    listing: ListingContext,
    weights: Optional[dict[str, float]] = None,
) -> MatchResult:
    """
    Compute the full 5-dimension score and weighted composite
    for a single courier against a listing.

    Returns a MatchResult with breakdown.
    """
    if weights is None:
        weights = select_weights(listing)

    # Score each dimension
    prox_score, distance_km = score_proximity(courier, listing)
    rel_score = score_reliability(courier)
    acc_score = score_acceptance(courier)
    veh_score = score_vehicle_fit(courier, listing)
    price_score = score_pricing(courier, listing)

    dimensions = DimensionScores(
        proximity=prox_score,
        reliability=rel_score,
        acceptance=acc_score,
        vehicle_fit=veh_score,
        pricing=price_score,
    )

    # Weighted composite
    composite = (
        weights["proximity"] * prox_score
        + weights["reliability"] * rel_score
        + weights["acceptance"] * acc_score
        + weights["vehicle_fit"] * veh_score
        + weights["pricing"] * price_score
    )

    return MatchResult(
        courier_id=courier.user_id,
        courier_name=courier.full_name,
        composite_score=round(composite, 2),
        dimensions=dimensions,
        distance_km=distance_km,
        vehicle_type=courier.vehicle_type or "unknown",
    )


# ═══════════════════════════════════════════════════════════════
#  BATCH RANKING
# ═══════════════════════════════════════════════════════════════

def rank_couriers(
    couriers: list[CourierStats],
    listing: ListingContext,
    top_k: int = 10,
    min_score: float = MIN_COMPOSITE_SCORE,
    weights: Optional[dict[str, float]] = None,
) -> list[MatchResult]:
    """
    Score all candidate couriers against a listing, filter,
    sort, and return the top K matches.

    This is the main entry point for the formula-based ranker.
    """
    if weights is None:
        weights = select_weights(listing)

    results: list[MatchResult] = []

    for courier in couriers:
        result = score_courier(courier, listing, weights)

        # Hard filters
        if result.dimensions.vehicle_fit == 0:
            continue  # Incompatible vehicle
        if result.composite_score < min_score:
            continue

        results.append(result)

    # Sort by composite score descending
    results.sort(key=lambda r: r.composite_score, reverse=True)

    # Assign ranks
    for i, result in enumerate(results):
        result.rank = i + 1

    return results[:top_k]


# ═══════════════════════════════════════════════════════════════
#  ML RE-RANKER (Phase 2 — LambdaMART)
# ═══════════════════════════════════════════════════════════════

def ml_rerank(
    results: list[MatchResult],
    listing: ListingContext,
    model_path: Optional[str] = None,
) -> list[MatchResult]:
    """
    Optional ML re-ranker using LightGBM LambdaMART.

    Takes the formula-ranked results and re-orders them using a
    trained Learning-to-Rank model that captures interaction
    effects between courier stats and listing features.

    Feature vector per (courier, listing) pair:
      - 5 dimension scores (from formula)
      - Raw courier stats (acceptance_rate, completion_rate, etc.)
      - Listing features (distance, weight, cargo_type encoded, urgency)
      - Interaction: distance × urgency, weight × capacity, etc.

    Target: P(bid accepted AND trip completed successfully)

    If no model is loaded, returns the original ranking unchanged.
    """
    if model_path is None:
        return results

    try:
        import lightgbm as lgb
        import numpy as np
    except ImportError:
        return results

    from pathlib import Path
    path = Path(model_path)
    if not path.exists():
        return results

    booster = lgb.Booster(model_file=str(path))

    features_list = []
    for r in results:
        features_list.append([
            # Dimension scores
            r.dimensions.proximity,
            r.dimensions.reliability,
            r.dimensions.acceptance,
            r.dimensions.vehicle_fit,
            r.dimensions.pricing,
            # Composite
            r.composite_score,
            # Distance
            r.distance_km or 0,
        ])

    X = np.array(features_list, dtype=np.float64)
    ml_scores = booster.predict(X)

    # Blend: 60% ML, 40% formula
    for i, result in enumerate(results):
        blended = 0.6 * ml_scores[i] + 0.4 * result.composite_score
        result.composite_score = round(blended, 2)

    results.sort(key=lambda r: r.composite_score, reverse=True)
    for i, result in enumerate(results):
        result.rank = i + 1

    return results
