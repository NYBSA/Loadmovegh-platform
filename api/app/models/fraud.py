"""
LoadMoveGH — SQLAlchemy Models: Fraud Detection
================================================

Stores fraud signals, per-user risk profiles, alerts for admin
review, and resolution decisions.

                    ┌──────────────────────────────────────┐
                    │       FRAUD DETECTION DATA FLOW       │
                    ├──────────────────────────────────────┤
                    │                                      │
                    │  User action (bid, payment, trip)     │
                    │            ↓                         │
                    │  Fraud Engine evaluates ~30 signals   │
                    │            ↓                         │
                    │  FraudSignal rows logged              │
                    │            ↓                         │
                    │  RiskProfile updated (composite 0–100)│
                    │            ↓                         │
                    │  If score > threshold → FraudAlert    │
                    │            ↓                         │
                    │  Admin reviews → FraudDecision        │
                    │  (freeze, warn, clear, ban)           │
                    │                                      │
                    └──────────────────────────────────────┘
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
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class FraudCategory(str, enum.Enum):
    """Top-level fraud categories the engine detects."""
    FAKE_COMPANY = "fake_company"
    SUSPICIOUS_BIDDING = "suspicious_bidding"
    UNUSUAL_PRICING = "unusual_pricing"
    REPEATED_CANCELLATION = "repeated_cancellation"
    PAYMENT_ABUSE = "payment_abuse"


class SignalSeverity(str, enum.Enum):
    """How serious an individual fraud signal is."""
    LOW = "low"           # Informational, contributes small risk
    MEDIUM = "medium"     # Notable, combined with others → alert
    HIGH = "high"         # Serious standalone indicator
    CRITICAL = "critical" # Immediate action required


class RiskLevel(str, enum.Enum):
    """Composite risk tier for a user."""
    LOW = "low"               # 0–25   → normal
    MEDIUM = "medium"         # 26–50  → monitor
    HIGH = "high"             # 51–75  → restrict
    CRITICAL = "critical"     # 76–100 → freeze/ban


class AlertStatus(str, enum.Enum):
    """Lifecycle of a fraud alert."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    RESOLVED_CLEAR = "resolved_clear"       # False positive
    RESOLVED_WARNING = "resolved_warning"   # Warn user
    RESOLVED_RESTRICT = "resolved_restrict" # Restrict account
    RESOLVED_BAN = "resolved_ban"           # Permanent ban


class DecisionAction(str, enum.Enum):
    """Admin enforcement action."""
    CLEAR = "clear"
    WARNING = "warning"
    FREEZE_WALLET = "freeze_wallet"
    SUSPEND_ACCOUNT = "suspend_account"
    BAN_ACCOUNT = "ban_account"
    RESTRICT_BIDDING = "restrict_bidding"
    RESTRICT_WITHDRAWALS = "restrict_withdrawals"
    MANUAL_REVIEW = "manual_review"


# ═══════════════════════════════════════════════════════════════
#  FRAUD SIGNAL (individual detection event)
# ═══════════════════════════════════════════════════════════════

class FraudSignal(Base):
    """
    A single fraud indicator detected by one of the engine's
    analysers.  Many signals feed into one RiskProfile.

    Examples:
      • "bid_price_3x_above_market" (unusual_pricing, medium)
      • "5_cancellations_in_24h" (repeated_cancellation, high)
      • "deposit_withdraw_cycle_detected" (payment_abuse, critical)
    """
    __tablename__ = "fraud_signals"
    __table_args__ = (
        Index("ix_fs_user_cat", "user_id", "category"),
        Index("ix_fs_created", "created_at"),
        Index("ix_fs_severity", "severity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Classification
    category: Mapped[FraudCategory] = mapped_column(
        SAEnum(FraudCategory, name="fraud_category_enum", create_constraint=True),
        nullable=False,
    )
    signal_code: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Machine-readable signal identifier, e.g. BID_PRICE_OUTLIER",
    )
    severity: Mapped[SignalSeverity] = mapped_column(
        SAEnum(SignalSeverity, name="signal_severity_enum", create_constraint=True),
        nullable=False,
    )

    # Score contribution (0.0–1.0 → how much this signal adds to risk)
    score_delta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Human-readable description
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Context data (JSON): entity IDs, thresholds exceeded, raw values
    context_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reference to the entity that triggered the signal
    entity_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="bid, listing, transaction, trip, user, organization",
    )
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Whether this signal has been consumed into a risk recalculation
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


# ═══════════════════════════════════════════════════════════════
#  RISK PROFILE (per-user composite score)
# ═══════════════════════════════════════════════════════════════

class RiskProfile(Base):
    """
    Materialised risk assessment for each user.  Updated every
    time the fraud engine evaluates new signals.

    The composite_score (0–100) determines the risk_level tier
    and whether enforcement actions are triggered.
    """
    __tablename__ = "risk_profiles"
    __table_args__ = (
        Index("ix_rp_user", "user_id", unique=True),
        Index("ix_rp_level", "risk_level"),
        Index("ix_rp_score", "composite_score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )

    # ── Composite risk score (0–100) ─────────────────────────
    composite_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="risk_level_enum", create_constraint=True),
        nullable=False,
        default=RiskLevel.LOW,
    )

    # ── Per-category scores (0–100 each) ─────────────────────
    fake_company_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    suspicious_bidding_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unusual_pricing_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    repeated_cancellation_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payment_abuse_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ── Counters ─────────────────────────────────────────────
    total_signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_alerts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_enforcements: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Status flags ─────────────────────────────────────────
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    last_scan_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", lazy="selectin")


# ═══════════════════════════════════════════════════════════════
#  FRAUD ALERT (notification to admin)
# ═══════════════════════════════════════════════════════════════

class FraudAlert(Base):
    """
    Generated when a user's risk profile crosses a threshold or
    a critical signal is detected.  Queued for admin review.
    """
    __tablename__ = "fraud_alerts"
    __table_args__ = (
        Index("ix_fa_status", "status"),
        Index("ix_fa_user", "user_id"),
        Index("ix_fa_priority", "priority_score"),
        Index("ix_fa_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Classification
    category: Mapped[FraudCategory] = mapped_column(
        SAEnum(FraudCategory, name="fraud_category_enum", create_constraint=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Priority for admin queue (higher = review first)
    priority_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    # Linked signals (JSON array of signal IDs)
    signal_ids_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus, name="alert_status_enum", create_constraint=True),
        nullable=False,
        default=AlertStatus.OPEN,
    )

    # Assignment
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Risk snapshot at time of alert
    risk_score_at_alert: Mapped[float] = mapped_column(Float, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id], lazy="selectin")


# ═══════════════════════════════════════════════════════════════
#  FRAUD DECISION (admin enforcement)
# ═══════════════════════════════════════════════════════════════

class FraudDecision(Base):
    """
    Records the admin's decision and enforcement action taken
    after reviewing a FraudAlert.
    """
    __tablename__ = "fraud_decisions"
    __table_args__ = (
        Index("ix_fd_alert", "alert_id"),
        Index("ix_fd_user", "target_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fraud_alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    decided_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Action taken
    action: Mapped[DecisionAction] = mapped_column(
        SAEnum(DecisionAction, name="decision_action_enum", create_constraint=True),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Duration (for temporary restrictions, NULL = permanent)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Was the enforcement auto-applied or manual?
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationships
    alert = relationship("FraudAlert", lazy="selectin")
    target_user = relationship("User", foreign_keys=[target_user_id], lazy="selectin")
    decided_by = relationship("User", foreign_keys=[decided_by_user_id], lazy="selectin")
