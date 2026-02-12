"""
LoadMoveGH — Pydantic Schemas for Freight Listings, Bids, and Trips
Full input validation for the freight marketplace.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════
#  ENUMS (mirrored as string literals for schema validation)
# ═══════════════════════════════════════════════════════════════

CARGO_TYPES = [
    "electronics", "perishables", "furniture", "textiles",
    "construction", "medical", "chemicals", "livestock", "general",
]

VEHICLE_TYPES = [
    "van", "box_truck", "flatbed", "refrigerated",
    "heavy_truck", "motorcycle", "any",
]

URGENCY_LEVELS = ["standard", "express", "urgent"]

LISTING_STATUSES = [
    "draft", "active", "bidding", "assigned", "in_transit",
    "delivered", "completed", "cancelled", "expired",
]

BID_STATUSES = ["pending", "accepted", "rejected", "withdrawn", "expired"]

TRIP_STATUSES = [
    "pickup_pending", "picked_up", "in_transit", "at_waypoint",
    "delivered", "confirmed", "disputed", "cancelled",
]

TRIP_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "pickup_pending": ["picked_up", "cancelled"],
    "picked_up": ["in_transit", "cancelled"],
    "in_transit": ["at_waypoint", "delivered"],
    "at_waypoint": ["in_transit", "delivered"],
    "delivered": ["confirmed", "disputed"],
    "confirmed": [],
    "disputed": ["confirmed", "cancelled"],
    "cancelled": [],
}


# ═══════════════════════════════════════════════════════════════
#  ADDRESS
# ═══════════════════════════════════════════════════════════════

class AddressCreate(BaseModel):
    city: str = Field(..., min_length=2, max_length=100, examples=["Accra"])
    region: Optional[str] = Field(None, max_length=100, examples=["Greater Accra"])
    street: Optional[str] = Field(None, max_length=500)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[float] = Field(None, ge=-90, le=90, examples=[5.6037])
    longitude: Optional[float] = Field(None, ge=-180, le=180, examples=[-0.1870])
    country: str = Field("GH", max_length=3)

    @field_validator("latitude")
    @classmethod
    def validate_ghana_latitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 4.5 or v > 11.5):
            raise ValueError("Latitude out of Ghana range (4.5°N – 11.5°N)")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_ghana_longitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < -3.5 or v > 1.5):
            raise ValueError("Longitude out of Ghana range (3.5°W – 1.5°E)")
        return v


class AddressResponse(BaseModel):
    id: uuid.UUID
    city: str
    region: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: str = "GH"

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
#  FREIGHT LISTING — CREATE
# ═══════════════════════════════════════════════════════════════

class CreateListingRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    pickup: AddressCreate
    delivery: AddressCreate
    cargo_type: str = Field(..., examples=["electronics"])
    weight_kg: float = Field(..., gt=0, le=50000)
    dimensions_length_cm: Optional[float] = Field(None, gt=0, le=2000)
    dimensions_width_cm: Optional[float] = Field(None, gt=0, le=500)
    dimensions_height_cm: Optional[float] = Field(None, gt=0, le=500)
    vehicle_type: str = Field("any", examples=["box_truck"])
    shipper_price: Optional[float] = Field(None, gt=0, le=1_000_000)
    currency: str = Field("GHS", max_length=3)
    urgency: str = Field("standard", examples=["express"])
    special_instructions: Optional[str] = Field(None, max_length=1000)

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

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v.upper() not in ("GHS", "USD", "NGN", "XOF"):
            raise ValueError("Currency must be GHS, USD, NGN, or XOF")
        return v.upper()


# ═══════════════════════════════════════════════════════════════
#  FREIGHT LISTING — UPDATE
# ═══════════════════════════════════════════════════════════════

class UpdateListingRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    cargo_type: Optional[str] = None
    weight_kg: Optional[float] = Field(None, gt=0, le=50000)
    vehicle_type: Optional[str] = None
    shipper_price: Optional[float] = Field(None, gt=0, le=1_000_000)
    urgency: Optional[str] = None
    special_instructions: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None

    @field_validator("cargo_type")
    @classmethod
    def validate_cargo_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_lower = v.lower()
        if v_lower not in CARGO_TYPES:
            raise ValueError(f"Invalid cargo type. Must be one of: {', '.join(CARGO_TYPES)}")
        return v_lower

    @field_validator("vehicle_type")
    @classmethod
    def validate_vehicle_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_lower = v.lower()
        if v_lower not in VEHICLE_TYPES:
            raise ValueError(f"Invalid vehicle type. Must be one of: {', '.join(VEHICLE_TYPES)}")
        return v_lower

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_lower = v.lower()
        if v_lower not in URGENCY_LEVELS:
            raise ValueError(f"Invalid urgency. Must be one of: {', '.join(URGENCY_LEVELS)}")
        return v_lower

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_lower = v.lower()
        allowed = ["active", "cancelled"]
        if v_lower not in allowed:
            raise ValueError(f"Shippers can only set status to: {', '.join(allowed)}")
        return v_lower


# ═══════════════════════════════════════════════════════════════
#  FREIGHT LISTING — RESPONSE
# ═══════════════════════════════════════════════════════════════

class ListingResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    shipper_id: uuid.UUID
    shipper_name: Optional[str] = None
    pickup: AddressResponse
    delivery: AddressResponse
    distance_km: Optional[float] = None
    cargo_type: str
    weight_kg: float
    dimensions_length_cm: Optional[float] = None
    dimensions_width_cm: Optional[float] = None
    dimensions_height_cm: Optional[float] = None
    vehicle_type: str
    shipper_price: Optional[float] = None
    ai_suggested_price: Optional[float] = None
    currency: str = "GHS"
    urgency: str
    status: str
    special_instructions: Optional[str] = None
    bid_count: int = 0
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ListingSummary(BaseModel):
    id: uuid.UUID
    title: str
    pickup_city: str
    delivery_city: str
    distance_km: Optional[float] = None
    cargo_type: str
    weight_kg: float
    vehicle_type: str
    shipper_price: Optional[float] = None
    ai_suggested_price: Optional[float] = None
    currency: str = "GHS"
    urgency: str
    status: str
    bid_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedListings(BaseModel):
    listings: List[ListingSummary]
    total: int
    page: int
    per_page: int


# ═══════════════════════════════════════════════════════════════
#  FREIGHT BID
# ═══════════════════════════════════════════════════════════════

class CreateBidRequest(BaseModel):
    price: float = Field(..., gt=0, le=1_000_000, examples=[780.00])
    currency: str = Field("GHS", max_length=3)
    eta_hours: Optional[float] = Field(None, gt=0, le=720)
    eta_description: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = Field(None, max_length=1000)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v.upper() not in ("GHS", "USD", "NGN", "XOF"):
            raise ValueError("Currency must be GHS, USD, NGN, or XOF")
        return v.upper()


class BidResponse(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    courier_id: uuid.UUID
    courier_name: Optional[str] = None
    price: float
    currency: str = "GHS"
    eta_hours: Optional[float] = None
    eta_description: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BidListResponse(BaseModel):
    bids: List[BidResponse]
    total: int


class AcceptBidRequest(BaseModel):
    bid_id: uuid.UUID


class AcceptBidResponse(BaseModel):
    message: str = "Bid accepted. Trip created and courier notified."
    listing_id: uuid.UUID
    bid_id: uuid.UUID
    trip_id: uuid.UUID
    courier_name: Optional[str] = None
    accepted_price: float


# ═══════════════════════════════════════════════════════════════
#  FREIGHT TRIP
# ═══════════════════════════════════════════════════════════════

class TripResponse(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    bid_id: uuid.UUID
    courier_id: uuid.UUID
    courier_name: Optional[str] = None
    pickup_city: Optional[str] = None
    delivery_city: Optional[str] = None
    distance_km: Optional[float] = None
    status: str
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_location_name: Optional[str] = None
    proof_of_delivery_url: Optional[str] = None
    delivery_notes: Optional[str] = None
    started_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateTripStatusRequest(BaseModel):
    status: str
    current_latitude: Optional[float] = Field(None, ge=-90, le=90)
    current_longitude: Optional[float] = Field(None, ge=-180, le=180)
    current_location_name: Optional[str] = Field(None, max_length=255)
    proof_of_delivery_url: Optional[str] = Field(None, max_length=2000)
    delivery_notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in TRIP_STATUSES:
            raise ValueError(f"Invalid trip status. Must be one of: {', '.join(TRIP_STATUSES)}")
        return v_lower


class UpdateTripStatusResponse(BaseModel):
    message: str
    trip_id: uuid.UUID
    previous_status: str
    new_status: str
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str
