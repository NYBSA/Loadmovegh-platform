"""
LoadMoveGH — Pydantic Schemas for AI Pricing Engine
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.ml.features import CARGO_RISK, FUEL_CONSUMPTION, URGENCY_MULTIPLIER


CARGO_TYPES = list(CARGO_RISK.keys())
VEHICLE_TYPES = list(FUEL_CONSUMPTION.keys())
URGENCY_LEVELS = list(URGENCY_MULTIPLIER.keys())


# ═══════════════════════════════════════════════════════════════
#  PRICE ESTIMATE — REQUEST
# ═══════════════════════════════════════════════════════════════

class PriceEstimateRequest(BaseModel):
    """
    Request a price estimate for a freight load.
    Provide as much data as possible for accuracy.
    """
    # Route (required)
    pickup_city: str = Field(..., min_length=2, max_length=100, examples=["Accra"])
    delivery_city: str = Field(..., min_length=2, max_length=100, examples=["Kumasi"])
    distance_km: Optional[float] = Field(
        None, gt=0, le=2000,
        description="If not provided, estimated from coordinates",
    )

    # Coordinates (optional but improve accuracy)
    pickup_lat: Optional[float] = Field(None, ge=-90, le=90, examples=[5.6037])
    pickup_lng: Optional[float] = Field(None, ge=-180, le=180, examples=[-0.1870])
    delivery_lat: Optional[float] = Field(None, ge=-90, le=90, examples=[6.6885])
    delivery_lng: Optional[float] = Field(None, ge=-180, le=180, examples=[-1.6244])

    # Regions
    pickup_region: str = Field("", max_length=100, examples=["Greater Accra"])
    delivery_region: str = Field("", max_length=100, examples=["Ashanti"])

    # Load (required)
    weight_kg: float = Field(..., gt=0, le=50000, examples=[2400])
    cargo_type: str = Field(..., examples=["electronics"])
    vehicle_type: str = Field("any", examples=["box_truck"])

    # Dimensions (optional)
    dimensions_length_cm: Optional[float] = Field(None, gt=0)
    dimensions_width_cm: Optional[float] = Field(None, gt=0)
    dimensions_height_cm: Optional[float] = Field(None, gt=0)

    # Urgency
    urgency: str = Field("standard", examples=["express"])

    # Optional context
    listing_id: Optional[uuid.UUID] = Field(
        None, description="Link estimate to an existing listing",
    )

    @field_validator("cargo_type")
    @classmethod
    def validate_cargo_type(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in CARGO_TYPES:
            raise ValueError(f"Invalid cargo type. Must be one of: {', '.join(CARGO_TYPES)}")
        return v_lower

    @field_validator("vehicle_type")
    @classmethod
    def validate_vehicle_type(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in VEHICLE_TYPES:
            raise ValueError(f"Invalid vehicle type. Must be one of: {', '.join(VEHICLE_TYPES)}")
        return v_lower

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in URGENCY_LEVELS:
            raise ValueError(f"Invalid urgency. Must be one of: {', '.join(URGENCY_LEVELS)}")
        return v_lower


# ═══════════════════════════════════════════════════════════════
#  PRICE ESTIMATE — RESPONSE
# ═══════════════════════════════════════════════════════════════

class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    value: float


class PriceEstimateResponse(BaseModel):
    """Recommended bid price range with explainability."""
    # Price range
    price_low: float = Field(..., description="Lower bound (15th percentile)")
    price_mid: float = Field(..., description="Recommended price (median)")
    price_high: float = Field(..., description="Upper bound (85th percentile)")
    currency: str = "GHS"

    # Confidence
    confidence: float = Field(
        ..., ge=0, le=1,
        description="Model confidence (0–1). Higher = tighter interval.",
    )

    # Model info
    model_version: str
    method: str = Field(..., description="'ml' or 'rule_based'")

    # Explainability
    feature_importance: List[FeatureImportanceItem] = Field(
        default_factory=list,
        description="Top features driving this price estimate",
    )

    # Cost breakdown
    fuel_cost_estimate: float = Field(..., description="Estimated fuel cost in GHS")
    distance_km: float
    weight_kg: float

    # Pricing run ID (for audit trail)
    pricing_run_id: Optional[uuid.UUID] = None


# ═══════════════════════════════════════════════════════════════
#  PRICE BREAKDOWN — RESPONSE (for existing listings)
# ═══════════════════════════════════════════════════════════════

class PriceBreakdownResponse(BaseModel):
    """Detailed price breakdown for an existing listing."""
    listing_id: uuid.UUID
    estimate: PriceEstimateResponse

    # Comparison with actual market data
    listing_shipper_price: Optional[float] = None
    avg_bid_price: Optional[float] = None
    bid_count: int = 0
    price_vs_market: Optional[str] = Field(
        None,
        description="'below_market', 'at_market', 'above_market'",
    )


# ═══════════════════════════════════════════════════════════════
#  MODEL STATUS / TRAINING
# ═══════════════════════════════════════════════════════════════

class ModelStatusResponse(BaseModel):
    version: str
    is_ml_loaded: bool
    feature_count: int
    algorithm: str = "LightGBM"


class TrainModelRequest(BaseModel):
    n_samples: int = Field(15000, ge=1000, le=100000)
    version_tag: Optional[str] = Field(None, max_length=50)


class TrainModelResponse(BaseModel):
    message: str
    version: str
    metrics: dict
    artifact_path: str
    training_samples: int
    validation_samples: int


class ModelVersionResponse(BaseModel):
    id: uuid.UUID
    version: str
    algorithm: str
    status: str
    feature_count: int
    training_samples: int
    validation_samples: int
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2_score: Optional[float] = None
    mape: Optional[float] = None
    model_artifact_path: Optional[str] = None
    trained_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str
