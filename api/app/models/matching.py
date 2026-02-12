"""
LoadMoveGH — SQLAlchemy Models: Courier Profiles & Match Scores
Stores live driver stats used by the matching engine and an audit
trail of every match recommendation.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
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


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ═══════════════════════════════════════════════════════════════
#  COURIER PROFILE (materialised driver stats)
# ═══════════════════════════════════════════════════════════════

class CourierProfile(Base):
    """
    Materialised stats for every courier, updated after each trip/bid.
    Provides the raw signals the matching engine consumes.

    Updated by:
      • Background job after trip status changes
      • Periodic batch recalculation (nightly)
      • Real-time location pings from driver app
    """
    __tablename__ = "courier_profiles"
    __table_args__ = (
        Index("ix_cp_user", "user_id", unique=True),
        Index("ix_cp_active_loc", "is_available", "current_latitude", "current_longitude"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )

    # ── Vehicle ──────────────────────────────────────────────
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vehicle_capacity_kg: Mapped[float] = mapped_column(Float, nullable=False, default=5000)
    has_refrigeration: Mapped[bool] = mapped_column(Boolean, default=False)
    has_gps_tracker: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Live location ────────────────────────────────────────
    current_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Availability ─────────────────────────────────────────
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_on_trip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Performance stats ────────────────────────────────────
    # Acceptance rate = bids placed / loads viewed (or offered)
    total_bids_placed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bids_accepted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bids_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Completion reliability
    total_trips_assigned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_trips_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_trips_cancelled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # On-time performance
    total_on_time_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    on_time_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Rating
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_ratings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Pricing
    avg_bid_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    avg_price_vs_market: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False,
        comment="Ratio of courier avg bid to market avg. <1 = competitive, >1 = expensive",
    )

    # Disputes
    total_disputes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    disputes_lost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Experience
    member_since_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", lazy="selectin")


# ═══════════════════════════════════════════════════════════════
#  MATCH RECOMMENDATION LOG (audit trail)
# ═══════════════════════════════════════════════════════════════

class MatchRecommendation(Base):
    """
    Logs every match recommendation the engine produces.
    Used for monitoring, A/B testing, and training the ML ranker.
    """
    __tablename__ = "match_recommendations"
    __table_args__ = (
        Index("ix_mr_listing", "listing_id"),
        Index("ix_mr_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freight_listings.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Algorithm version
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Full ranked list (JSON array of {courier_id, rank, composite_score, dimension_scores})
    ranked_results_json: Mapped[str] = mapped_column(Text, nullable=False)
    total_candidates: Mapped[int] = mapped_column(Integer, nullable=False)
    returned_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Outcome tracking (filled in later)
    chosen_courier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    chosen_courier_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
