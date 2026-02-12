"""
LoadMoveGH — SQLAlchemy Models: Addresses, Freight Listings, Bids, Trips
Matches the ARCHITECTURE.md schema for Freight & Listings + Location.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ── Helpers ──────────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── Enums ────────────────────────────────────────────────────

class CargoType(str, enum.Enum):
    ELECTRONICS = "electronics"
    PERISHABLES = "perishables"
    FURNITURE = "furniture"
    TEXTILES = "textiles"
    CONSTRUCTION = "construction"
    MEDICAL = "medical"
    CHEMICALS = "chemicals"
    LIVESTOCK = "livestock"
    GENERAL = "general"


class VehicleType(str, enum.Enum):
    VAN = "van"
    BOX_TRUCK = "box_truck"
    FLATBED = "flatbed"
    REFRIGERATED = "refrigerated"
    HEAVY_TRUCK = "heavy_truck"
    MOTORCYCLE = "motorcycle"
    ANY = "any"


class Urgency(str, enum.Enum):
    STANDARD = "standard"
    EXPRESS = "express"
    URGENT = "urgent"


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    BIDDING = "bidding"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BidStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class TripStatus(str, enum.Enum):
    PICKUP_PENDING = "pickup_pending"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    AT_WAYPOINT = "at_waypoint"
    DELIVERED = "delivered"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


# ═══════════════════════════════════════════════════════════════
#  ADDRESS (with geolocation)
# ═══════════════════════════════════════════════════════════════

class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (
        Index("ix_addresses_city", "city"),
        Index("ix_addresses_region", "region"),
        Index("ix_addresses_coords", "latitude", "longitude"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    country: Mapped[str] = mapped_column(String(3), nullable=False, default="GH")
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    street: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


# ═══════════════════════════════════════════════════════════════
#  FREIGHT LISTING
# ═══════════════════════════════════════════════════════════════

class FreightListing(Base):
    __tablename__ = "freight_listings"
    __table_args__ = (
        Index("ix_listings_status_created", "status", "created_at"),
        Index("ix_listings_shipper", "shipper_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    shipper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Route
    pickup_address_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=False
    )
    delivery_address_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=False
    )

    # Cargo details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cargo_type: Mapped[CargoType] = mapped_column(
        SAEnum(CargoType, name="cargo_type_enum", create_constraint=True),
        nullable=False,
    )
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    dimensions_length_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dimensions_width_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dimensions_height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SAEnum(VehicleType, name="vehicle_type_enum", create_constraint=True),
        nullable=False,
        default=VehicleType.ANY,
    )

    # Pricing
    shipper_price: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    ai_suggested_price: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")

    # Urgency & Status
    urgency: Mapped[Urgency] = mapped_column(
        SAEnum(Urgency, name="urgency_enum", create_constraint=True),
        nullable=False,
        default=Urgency.STANDARD,
    )
    status: Mapped[ListingStatus] = mapped_column(
        SAEnum(ListingStatus, name="listing_status_enum", create_constraint=True),
        nullable=False,
        default=ListingStatus.ACTIVE,
    )
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Computed/cached distance
    distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Bid count cache (denormalised for performance)
    bid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Relationships ────────────────────────────────────────
    shipper = relationship("User", foreign_keys=[shipper_id], lazy="selectin")
    pickup_address: Mapped["Address"] = relationship(
        foreign_keys=[pickup_address_id], lazy="selectin"
    )
    delivery_address: Mapped["Address"] = relationship(
        foreign_keys=[delivery_address_id], lazy="selectin"
    )
    bids: Mapped[List["FreightBid"]] = relationship(
        back_populates="listing", lazy="selectin",
        cascade="all, delete-orphan",
    )
    trip: Mapped[Optional["FreightTrip"]] = relationship(
        back_populates="listing", lazy="selectin", uselist=False,
    )


# ═══════════════════════════════════════════════════════════════
#  FREIGHT BID
# ═══════════════════════════════════════════════════════════════

class FreightBid(Base):
    __tablename__ = "freight_bids"
    __table_args__ = (
        Index("ix_bids_listing_status", "listing_id", "status"),
        Index("ix_bids_courier", "courier_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freight_listings.id", ondelete="CASCADE"),
        nullable=False,
    )
    courier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Bid details
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")
    eta_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eta_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[BidStatus] = mapped_column(
        SAEnum(BidStatus, name="bid_status_enum", create_constraint=True),
        nullable=False,
        default=BidStatus.PENDING,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────────────
    listing: Mapped["FreightListing"] = relationship(back_populates="bids")
    courier = relationship("User", foreign_keys=[courier_id], lazy="selectin")


# ═══════════════════════════════════════════════════════════════
#  FREIGHT TRIP (created when a bid is accepted)
# ═══════════════════════════════════════════════════════════════

class FreightTrip(Base):
    __tablename__ = "freight_trips"
    __table_args__ = (
        Index("ix_trips_listing", "listing_id"),
        Index("ix_trips_courier", "courier_id"),
        Index("ix_trips_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freight_listings.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    bid_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freight_bids.id"), nullable=False
    )
    courier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Status
    status: Mapped[TripStatus] = mapped_column(
        SAEnum(TripStatus, name="trip_status_enum", create_constraint=True),
        nullable=False,
        default=TripStatus.PICKUP_PENDING,
    )

    # Location tracking
    current_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Proof of delivery
    proof_of_delivery_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    picked_up_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # ── Relationships ────────────────────────────────────────
    listing: Mapped["FreightListing"] = relationship(back_populates="trip")
    bid: Mapped["FreightBid"] = relationship(lazy="selectin")
    courier = relationship("User", foreign_keys=[courier_id], lazy="selectin")
