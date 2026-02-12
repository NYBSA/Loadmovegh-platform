"""
LoadMoveGH — SQLAlchemy Models: Wallets, Transactions, Escrow, MoMo, Payouts, Disputes
Implements the ARCHITECTURE.md Wallet & Escrow schema with Ghana-specific MoMo integration.

                     ┌──────────────────────────────────────────┐
                     │           PAYMENT FLOW OVERVIEW           │
                     ├──────────────────────────────────────────┤
                     │                                          │
                     │  Shipper deposits GHS via MTN MoMo       │
                     │            ↓                             │
                     │  Funds land in Shipper Wallet            │
                     │            ↓                             │
                     │  Bid accepted → EscrowHold created       │
                     │  (full bid amount locked)                │
                     │            ↓                             │
                     │  Trip delivered + confirmed               │
                     │            ↓                             │
                     │  Escrow released:                        │
                     │   • Platform commission deducted (5%)    │
                     │   • Net amount → Courier Wallet          │
                     │            ↓                             │
                     │  Courier withdraws to MoMo               │
                     │                                          │
                     │  If disputed → funds stay in escrow      │
                     │  until admin resolves                    │
                     └──────────────────────────────────────────┘
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ── Helpers ──────────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ═══════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class WalletStatus(str, enum.Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"               # Funds in (MoMo, card, bank)
    WITHDRAWAL = "withdrawal"         # Funds out (MoMo, bank)
    ESCROW_HOLD = "escrow_hold"       # Funds locked for a trip
    ESCROW_RELEASE = "escrow_release" # Funds released to courier
    ESCROW_REFUND = "escrow_refund"   # Funds returned to shipper (dispute/cancel)
    COMMISSION = "commission"         # Platform fee deduction
    TRANSFER_IN = "transfer_in"      # Internal wallet-to-wallet (receiving)
    TRANSFER_OUT = "transfer_out"    # Internal wallet-to-wallet (sending)
    ADJUSTMENT = "adjustment"         # Manual admin adjustment


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class ReferenceType(str, enum.Enum):
    TRIP = "trip"
    LISTING = "listing"
    BID = "bid"
    ESCROW = "escrow"
    DISPUTE = "dispute"
    MOMO_PAYMENT = "momo_payment"
    PAYOUT = "payout"
    MANUAL = "manual"


class EscrowStatus(str, enum.Enum):
    HELD = "held"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    PARTIALLY_RELEASED = "partially_released"


class MoMoProvider(str, enum.Enum):
    MTN = "mtn"
    VODAFONE = "vodafone"
    AIRTELTIGO = "airteltigo"


class MoMoDirection(str, enum.Enum):
    COLLECTION = "collection"   # User → Platform (deposit)
    DISBURSEMENT = "disbursement"  # Platform → User (withdrawal/payout)


class MoMoStatus(str, enum.Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class PayoutStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED_SHIPPER = "resolved_shipper"   # Refund to shipper
    RESOLVED_COURIER = "resolved_courier"   # Pay courier
    RESOLVED_SPLIT = "resolved_split"       # Split between both
    ESCALATED = "escalated"
    CLOSED = "closed"


class DisputeReason(str, enum.Enum):
    DAMAGED_GOODS = "damaged_goods"
    MISSING_ITEMS = "missing_items"
    LATE_DELIVERY = "late_delivery"
    WRONG_DELIVERY = "wrong_delivery"
    NO_DELIVERY = "no_delivery"
    OVERCHARGE = "overcharge"
    FRAUD = "fraud"
    OTHER = "other"


# ═══════════════════════════════════════════════════════════════
#  WALLET
# ═══════════════════════════════════════════════════════════════

class Wallet(Base):
    """
    Each user (or organization) has one wallet per currency.
    `balance` = available funds; `escrow_balance` = funds locked in escrow.
    """
    __tablename__ = "wallets"
    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="uq_wallet_user_currency"),
        Index("ix_wallets_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Balances (Numeric for financial precision)
    balance: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.00
    )
    escrow_balance: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.00
    )
    total_deposited: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.00
    )
    total_withdrawn: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.00
    )
    total_earned: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.00
    )

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")
    status: Mapped[WalletStatus] = mapped_column(
        SAEnum(WalletStatus, name="wallet_status_enum", create_constraint=True),
        nullable=False,
        default=WalletStatus.ACTIVE,
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="wallet", lazy="dynamic",
    )


# ═══════════════════════════════════════════════════════════════
#  TRANSACTION (Ledger)
# ═══════════════════════════════════════════════════════════════

class Transaction(Base):
    """
    Immutable double-entry-style ledger.  Every money movement creates
    a transaction row.  `amount` is always positive; `type` indicates
    direction (deposit = credit, withdrawal = debit, etc.).
    """
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_txn_wallet_created", "wallet_id", "created_at"),
        Index("ix_txn_reference", "reference_type", "reference_id"),
        Index("ix_txn_type_status", "type", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )

    # Core fields
    type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="txn_type_enum", create_constraint=True),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")
    fee: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.00)
    net_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    # Balance snapshot after this transaction
    balance_after: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    status: Mapped[TransactionStatus] = mapped_column(
        SAEnum(TransactionStatus, name="txn_status_enum", create_constraint=True),
        nullable=False,
        default=TransactionStatus.PENDING,
    )

    # Reference linking
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Human-readable
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")


# ═══════════════════════════════════════════════════════════════
#  ESCROW HOLD
# ═══════════════════════════════════════════════════════════════

class EscrowHold(Base):
    """
    Created when a shipper accepts a bid.  Locks the bid amount from
    the shipper's wallet until delivery is confirmed or a dispute resolved.
    """
    __tablename__ = "escrow_holds"
    __table_args__ = (
        Index("ix_escrow_trip", "trip_id"),
        Index("ix_escrow_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freight_trips.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freight_listings.id"), nullable=False
    )
    shipper_wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False
    )
    courier_wallet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=True
    )

    # Amounts
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")
    platform_commission_rate: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.05  # 5%
    )
    platform_commission_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    courier_payout_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(14, 2), nullable=True
    )

    # Status
    status: Mapped[EscrowStatus] = mapped_column(
        SAEnum(EscrowStatus, name="escrow_status_enum", create_constraint=True),
        nullable=False,
        default=EscrowStatus.HELD,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    released_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    trip = relationship("FreightTrip", lazy="selectin")
    listing = relationship("FreightListing", lazy="selectin")
    shipper_wallet: Mapped["Wallet"] = relationship(
        foreign_keys=[shipper_wallet_id], lazy="selectin"
    )
    courier_wallet: Mapped[Optional["Wallet"]] = relationship(
        foreign_keys=[courier_wallet_id], lazy="selectin"
    )


# ═══════════════════════════════════════════════════════════════
#  MTN MOBILE MONEY PAYMENT
# ═══════════════════════════════════════════════════════════════

class MoMoPayment(Base):
    """
    Tracks every Mobile Money API interaction (collection / disbursement).
    Ghana MoMo providers: MTN, Vodafone Cash, AirtelTigo Money.
    """
    __tablename__ = "momo_payments"
    __table_args__ = (
        Index("ix_momo_external_id", "external_transaction_id"),
        Index("ix_momo_wallet", "wallet_id"),
        Index("ix_momo_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True
    )

    # Provider details
    provider: Mapped[MoMoProvider] = mapped_column(
        SAEnum(MoMoProvider, name="momo_provider_enum", create_constraint=True),
        nullable=False,
        default=MoMoProvider.MTN,
    )
    direction: Mapped[MoMoDirection] = mapped_column(
        SAEnum(MoMoDirection, name="momo_direction_enum", create_constraint=True),
        nullable=False,
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)

    # Amounts
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")
    fee: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.00)

    # Provider tracking
    external_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, unique=True
    )
    provider_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    callback_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[MoMoStatus] = mapped_column(
        SAEnum(MoMoStatus, name="momo_status_enum", create_constraint=True),
        nullable=False,
        default=MoMoStatus.INITIATED,
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    wallet: Mapped["Wallet"] = relationship(lazy="selectin")
    transaction: Mapped[Optional["Transaction"]] = relationship(lazy="selectin")


# ═══════════════════════════════════════════════════════════════
#  PAYOUT SCHEDULE
# ═══════════════════════════════════════════════════════════════

class PayoutSchedule(Base):
    """
    Scheduled payouts to couriers — auto-created after escrow release,
    processed in batch or on-demand via MoMo disbursement.
    """
    __tablename__ = "payout_schedules"
    __table_args__ = (
        Index("ix_payout_courier_status", "courier_id", "status"),
        Index("ix_payout_due_date", "due_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    courier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False
    )
    escrow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("escrow_holds.id"), nullable=False
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freight_trips.id"), nullable=False
    )

    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")

    status: Mapped[PayoutStatus] = mapped_column(
        SAEnum(PayoutStatus, name="payout_status_enum", create_constraint=True),
        nullable=False,
        default=PayoutStatus.SCHEDULED,
    )

    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationships
    courier = relationship("User", foreign_keys=[courier_id], lazy="selectin")
    wallet: Mapped["Wallet"] = relationship(lazy="selectin")
    escrow: Mapped["EscrowHold"] = relationship(lazy="selectin")


# ═══════════════════════════════════════════════════════════════
#  DISPUTE
# ═══════════════════════════════════════════════════════════════

class Dispute(Base):
    """
    Raised when shipper or courier disputes a trip outcome.
    Freezes escrow until admin resolution.
    """
    __tablename__ = "disputes"
    __table_args__ = (
        Index("ix_dispute_trip", "trip_id"),
        Index("ix_dispute_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("freight_trips.id", ondelete="CASCADE"),
        nullable=False,
    )
    escrow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("escrow_holds.id"), nullable=False
    )

    # Parties
    raised_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    against_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Details
    reason: Mapped[DisputeReason] = mapped_column(
        SAEnum(DisputeReason, name="dispute_reason_enum", create_constraint=True),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_urls: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Resolution
    status: Mapped[DisputeStatus] = mapped_column(
        SAEnum(DisputeStatus, name="dispute_status_enum", create_constraint=True),
        nullable=False,
        default=DisputeStatus.OPEN,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # If split resolution, how much goes to each party
    shipper_refund_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    courier_payout_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(14, 2), nullable=True
    )

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
    trip = relationship("FreightTrip", lazy="selectin")
    escrow: Mapped["EscrowHold"] = relationship(lazy="selectin")
    raised_by = relationship("User", foreign_keys=[raised_by_user_id], lazy="selectin")
    against_user = relationship("User", foreign_keys=[against_user_id], lazy="selectin")
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id], lazy="selectin")
