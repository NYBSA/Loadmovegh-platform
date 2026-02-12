"""
LoadMoveGH — SQLAlchemy Models: AI Pricing Engine
Tracks every pricing prediction and model version lifecycle.
Matches the ARCHITECTURE.md AI & Fraud schema.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Float,
    Index,
    ForeignKey,
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


# ── Enums ────────────────────────────────────────────────────

class ModelStatus(str, enum.Enum):
    TRAINING = "training"
    VALIDATING = "validating"
    ACTIVE = "active"       # Currently serving predictions
    SHADOW = "shadow"       # Running in shadow mode (A/B)
    RETIRED = "retired"
    FAILED = "failed"


# ═══════════════════════════════════════════════════════════════
#  PRICING MODEL VERSION
# ═══════════════════════════════════════════════════════════════

class PricingModelVersion(Base):
    """
    Tracks every trained model version with its features, metrics,
    and lifecycle status.  Only one model can be ACTIVE at a time.
    """
    __tablename__ = "pricing_model_versions"
    __table_args__ = (
        Index("ix_pmv_status", "status"),
        Index("ix_pmv_version", "version", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ModelStatus] = mapped_column(
        SAEnum(ModelStatus, name="model_status_enum", create_constraint=True),
        nullable=False,
        default=ModelStatus.TRAINING,
    )

    # Feature list used
    feature_names_json: Mapped[str] = mapped_column(Text, nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Training details
    training_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Metrics (JSON for flexibility)
    metrics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Key metrics as columns for querying
    mae: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rmse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    r2_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mape: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Model artifact path
    model_artifact_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    trained_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retired_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


# ═══════════════════════════════════════════════════════════════
#  AI PRICING RUN (per-prediction audit trail)
# ═══════════════════════════════════════════════════════════════

class AIPricingRun(Base):
    """
    Records every price prediction made by the engine.
    Stores the full feature vector, output, and confidence —
    essential for model monitoring and retraining.
    """
    __tablename__ = "ai_pricing_runs"
    __table_args__ = (
        Index("ix_apr_listing", "listing_id"),
        Index("ix_apr_created", "created_at"),
        Index("ix_apr_model_version", "model_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freight_listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Input features (stored as JSON for audit)
    features_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Prediction output
    suggested_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    price_low: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    price_high: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")

    # Feature importance for this prediction (top features)
    explanation_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Feedback: what actually happened
    actual_accepted_price: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    prediction_error: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationships
    listing = relationship("FreightListing", lazy="selectin")
