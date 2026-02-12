"""
LoadMoveGH — Pydantic Schemas for Wallet, Transactions, Escrow, MoMo, Disputes
Full input validation for Ghana payment flows.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

# ── Ghana phone regex ────────────────────────────────────────
GHANA_PHONE_RE = re.compile(r"^(\+233|0)(2[034-9]|5[045-9]|24|54|55|27|57|26|56)\d{7}$")

MOMO_PROVIDERS = ["mtn", "vodafone", "airteltigo"]
DISPUTE_REASONS = [
    "damaged_goods", "missing_items", "late_delivery", "wrong_delivery",
    "no_delivery", "overcharge", "fraud", "other",
]
DISPUTE_STATUSES = [
    "open", "under_review", "resolved_shipper", "resolved_courier",
    "resolved_split", "escalated", "closed",
]


# ═══════════════════════════════════════════════════════════════
#  WALLET
# ═══════════════════════════════════════════════════════════════

class WalletResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    balance: float
    escrow_balance: float
    total_deposited: float
    total_withdrawn: float
    total_earned: float
    currency: str
    status: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletSummary(BaseModel):
    """Compact wallet info for headers / sidebars."""
    balance: float
    escrow_balance: float
    currency: str
    status: str


# ═══════════════════════════════════════════════════════════════
#  DEPOSIT (MoMo)
# ═══════════════════════════════════════════════════════════════

class MoMoDepositRequest(BaseModel):
    """Initiate a deposit via MTN Mobile Money (or other Ghana providers)."""
    amount: float = Field(..., gt=0, le=50_000, examples=[200.00])
    currency: str = Field("GHS", max_length=3)
    provider: str = Field("mtn", examples=["mtn"])
    phone_number: str = Field(
        ..., min_length=10, max_length=15,
        examples=["+233241234567"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_ghana_phone(cls, v: str) -> str:
        if not GHANA_PHONE_RE.match(v):
            raise ValueError(
                "Invalid Ghana phone number. "
                "Format: +233XXXXXXXXX or 0XXXXXXXXX (MTN/Vodafone/AirtelTigo)"
            )
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in MOMO_PROVIDERS:
            raise ValueError(f"Provider must be one of: {', '.join(MOMO_PROVIDERS)}")
        return v_lower

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v.upper() != "GHS":
            raise ValueError("MoMo deposits only support GHS (Ghana Cedi)")
        return v.upper()

    @field_validator("amount")
    @classmethod
    def validate_min_deposit(cls, v: float) -> float:
        if v < 1.00:
            raise ValueError("Minimum deposit is GHS 1.00")
        return v


class MoMoDepositResponse(BaseModel):
    message: str = "MoMo payment initiated. Check your phone to approve."
    momo_payment_id: uuid.UUID
    transaction_id: uuid.UUID
    provider: str
    phone_number: str
    amount: float
    currency: str
    status: str
    external_transaction_id: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
#  WITHDRAWAL (MoMo)
# ═══════════════════════════════════════════════════════════════

class MoMoWithdrawRequest(BaseModel):
    """Withdraw funds from wallet to MoMo."""
    amount: float = Field(..., gt=0, le=50_000, examples=[500.00])
    currency: str = Field("GHS", max_length=3)
    provider: str = Field("mtn", examples=["mtn"])
    phone_number: str = Field(
        ..., min_length=10, max_length=15,
        examples=["+233241234567"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_ghana_phone(cls, v: str) -> str:
        if not GHANA_PHONE_RE.match(v):
            raise ValueError(
                "Invalid Ghana phone number. "
                "Format: +233XXXXXXXXX or 0XXXXXXXXX"
            )
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in MOMO_PROVIDERS:
            raise ValueError(f"Provider must be one of: {', '.join(MOMO_PROVIDERS)}")
        return v_lower

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v.upper() != "GHS":
            raise ValueError("MoMo withdrawals only support GHS")
        return v.upper()

    @field_validator("amount")
    @classmethod
    def validate_min_withdrawal(cls, v: float) -> float:
        if v < 5.00:
            raise ValueError("Minimum withdrawal is GHS 5.00")
        return v


class MoMoWithdrawResponse(BaseModel):
    message: str = "Withdrawal initiated. Funds will arrive in your MoMo shortly."
    momo_payment_id: uuid.UUID
    transaction_id: uuid.UUID
    provider: str
    phone_number: str
    amount: float
    fee: float
    net_amount: float
    currency: str
    status: str


# ═══════════════════════════════════════════════════════════════
#  MOMO CALLBACK (webhook from provider)
# ═══════════════════════════════════════════════════════════════

class MoMoCallbackPayload(BaseModel):
    """Webhook payload from MoMo provider on payment status update."""
    external_transaction_id: str
    status: str  # success / failed / timeout
    provider_reference: Optional[str] = None
    amount: Optional[float] = None
    message: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
#  TRANSACTION LEDGER
# ═══════════════════════════════════════════════════════════════

class TransactionResponse(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    type: str
    amount: float
    currency: str
    fee: float
    net_amount: float
    balance_after: float
    status: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    per_page: int


# ═══════════════════════════════════════════════════════════════
#  ESCROW
# ═══════════════════════════════════════════════════════════════

class EscrowHoldResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    listing_id: uuid.UUID
    amount: float
    currency: str
    platform_commission_rate: float
    platform_commission_amount: Optional[float] = None
    courier_payout_amount: Optional[float] = None
    status: str
    created_at: datetime
    released_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EscrowListResponse(BaseModel):
    escrow_holds: List[EscrowHoldResponse]
    total: int


class EscrowReleaseResponse(BaseModel):
    message: str
    escrow_id: uuid.UUID
    trip_id: uuid.UUID
    total_amount: float
    platform_commission: float
    courier_payout: float
    currency: str


# ═══════════════════════════════════════════════════════════════
#  DISPUTE
# ═══════════════════════════════════════════════════════════════

class OpenDisputeRequest(BaseModel):
    """Open a dispute on a trip."""
    trip_id: uuid.UUID
    reason: str
    description: str = Field(..., min_length=20, max_length=2000)
    evidence_urls: Optional[str] = Field(
        None, max_length=2000,
        description="Comma-separated URLs to evidence (photos, documents)",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in DISPUTE_REASONS:
            raise ValueError(f"Reason must be one of: {', '.join(DISPUTE_REASONS)}")
        return v_lower


class DisputeResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    escrow_id: uuid.UUID
    raised_by_user_id: uuid.UUID
    raised_by_name: Optional[str] = None
    against_user_id: uuid.UUID
    against_user_name: Optional[str] = None
    reason: str
    description: str
    evidence_urls: Optional[str] = None
    status: str
    resolution_notes: Optional[str] = None
    resolved_by_name: Optional[str] = None
    shipper_refund_amount: Optional[float] = None
    courier_payout_amount: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResolveDisputeRequest(BaseModel):
    """Admin resolves a dispute."""
    resolution: str = Field(
        ..., description="One of: resolved_shipper, resolved_courier, resolved_split"
    )
    resolution_notes: str = Field(..., min_length=10, max_length=2000)
    shipper_refund_amount: Optional[float] = Field(
        None, ge=0, description="Amount to refund to shipper (for split resolution)"
    )
    courier_payout_amount: Optional[float] = Field(
        None, ge=0, description="Amount to pay to courier (for split resolution)"
    )

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: str) -> str:
        v_lower = v.lower()
        allowed = ["resolved_shipper", "resolved_courier", "resolved_split"]
        if v_lower not in allowed:
            raise ValueError(f"Resolution must be one of: {', '.join(allowed)}")
        return v_lower


class DisputeListResponse(BaseModel):
    disputes: List[DisputeResponse]
    total: int


# ═══════════════════════════════════════════════════════════════
#  GENERIC
# ═══════════════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    message: str
