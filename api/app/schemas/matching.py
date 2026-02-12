"""
LoadMoveGH — Pydantic Schemas for Load-Matching Engine
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
#  REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class WeightOverrides(BaseModel):
    """Optional overrides for dimension weights."""
    proximity: Optional[float] = Field(None, ge=0, le=1.0)
    reliability: Optional[float] = Field(None, ge=0, le=1.0)
    acceptance: Optional[float] = Field(None, ge=0, le=1.0)
    vehicle_fit: Optional[float] = Field(None, ge=0, le=1.0)
    pricing: Optional[float] = Field(None, ge=0, le=1.0)


class MatchRequest(BaseModel):
    """Request to find best-matched couriers for a listing."""
    listing_id: str = Field(..., description="UUID of the freight listing to match")
    top_k: int = Field(10, ge=1, le=50, description="Maximum couriers to return")
    min_score: float = Field(30.0, ge=0, le=100, description="Minimum composite score threshold")
    max_radius_km: float = Field(300.0, ge=1, le=1000, description="Maximum courier distance from pickup (km)")
    use_ml_reranker: bool = Field(False, description="Enable ML re-ranking if model available")
    weight_overrides: Optional[WeightOverrides] = Field(
        None, description="Custom dimension weights (must sum to ~1.0)"
    )


class ScoreCourierRequest(BaseModel):
    """Score a single courier against a listing."""
    listing_id: str = Field(..., description="UUID of the freight listing")
    courier_id: str = Field(..., description="UUID of the courier to score")


class UpdateLocationRequest(BaseModel):
    """Update courier's live GPS position."""
    latitude: float = Field(..., ge=4.5, le=11.5, description="Latitude (Ghana bounds)")
    longitude: float = Field(..., ge=-3.5, le=1.5, description="Longitude (Ghana bounds)")
    city: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)


# ═══════════════════════════════════════════════════════════════
#  RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class DimensionScoreResponse(BaseModel):
    """Breakdown of a courier's 5 scoring dimensions."""
    proximity: float = Field(..., description="Location proximity score (0–100)")
    reliability: float = Field(..., description="Completion & dispute score (0–100)")
    acceptance: float = Field(..., description="Bid acceptance rate score (0–100)")
    vehicle_fit: float = Field(..., description="Vehicle suitability score (0–100)")
    pricing: float = Field(..., description="Price competitiveness score (0–100)")


class MatchedCourier(BaseModel):
    """A single courier match result with full breakdown."""
    courier_id: str
    courier_name: str
    rank: int
    composite_score: float = Field(..., description="Weighted composite score (0–100)")
    dimensions: DimensionScoreResponse
    distance_km: Optional[float] = Field(None, description="Distance to pickup in km")
    vehicle_type: str


class MatchResponse(BaseModel):
    """Response from the matching engine."""
    listing_id: str
    algorithm_version: str = "v1.0-formula"
    total_candidates: int = Field(..., description="Total couriers evaluated")
    returned_count: int = Field(..., description="Number of matches returned after filtering")
    weights_used: dict[str, float] = Field(..., description="Dimension weights applied")
    matches: list[MatchedCourier]


class CourierScoreResponse(BaseModel):
    """Detailed score breakdown for a single courier–listing pair."""
    listing_id: str
    courier_id: str
    courier_name: str
    composite_score: float
    dimensions: DimensionScoreResponse
    distance_km: Optional[float] = None
    vehicle_type: str
    weights_used: dict[str, float]
    is_eligible: bool = Field(..., description="Whether courier passes hard filters")
    disqualification_reasons: list[str] = Field(
        default_factory=list, description="Reasons if not eligible"
    )


class CourierProfileResponse(BaseModel):
    """Public courier profile with stats."""
    user_id: str
    full_name: str
    vehicle_type: Optional[str] = None
    vehicle_capacity_kg: float = 0
    current_city: Optional[str] = None
    current_region: Optional[str] = None
    is_available: bool = False
    is_on_trip: bool = False
    acceptance_rate: float = 0.0
    completion_rate: float = 0.0
    on_time_rate: float = 0.0
    avg_rating: float = 0.0
    total_ratings: int = 0
    total_trips_completed: int = 0
    member_since_days: int = 0
    has_gps_tracker: bool = False


class LocationUpdateResponse(BaseModel):
    """Confirmation of location update."""
    user_id: str
    latitude: float
    longitude: float
    city: Optional[str] = None
    region: Optional[str] = None
    updated_at: str
