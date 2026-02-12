"""
LoadMoveGH — Escrow & Payment Lifecycle Endpoints
Handles the full escrow flow: hold → release/refund, commission deduction,
payout scheduling.  Also includes the dispute system.

                  ESCROW LIFECYCLE
    ┌──────────────────────────────────────────┐
    │  Bid Accepted (via accept-bid endpoint)  │
    │     ↓                                    │
    │  POST /escrow/hold-for-trip              │
    │  • Validates shipper balance             │
    │  • Deducts amount from shipper wallet    │
    │  • Creates EscrowHold (status=held)      │
    │  • Logs escrow_hold transaction          │
    │     ↓                                    │
    │  Trip progresses ... delivered            │
    │     ↓                                    │
    │  POST /escrow/{id}/release               │
    │  • Calculates 5% platform commission     │
    │  • Credits courier wallet (net amount)   │
    │  • Logs escrow_release + commission txns │
    │  • Creates PayoutSchedule                │
    │     ↓                                    │
    │  Courier can now withdraw via MoMo       │
    │                                          │
    │  ── DISPUTE PATH ─────────────────────── │
    │  POST /disputes                          │
    │  • Escrow status → disputed              │
    │  • Funds remain locked                   │
    │     ↓                                    │
    │  POST /disputes/{id}/resolve (admin)     │
    │  • resolved_shipper → full refund        │
    │  • resolved_courier → full payout        │
    │  • resolved_split → split amounts        │
    └──────────────────────────────────────────┘
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import (
    get_current_active_user,
    require_any_authenticated,
    require_system_admin,
)
from app.core.config import settings
from app.core.database import get_db
from app.models.freight import FreightListing, FreightTrip, TripStatus
from app.models.user import User
from app.models.wallet import (
    Dispute,
    DisputeReason,
    DisputeStatus,
    EscrowHold,
    EscrowStatus,
    PayoutSchedule,
    PayoutStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
    Wallet,
    WalletStatus,
)
from app.schemas.wallet import (
    DisputeListResponse,
    DisputeResponse,
    EscrowHoldResponse,
    EscrowReleaseResponse,
    MessageResponse,
    OpenDisputeRequest,
    ResolveDisputeRequest,
)

router = APIRouter(tags=["Escrow & Disputes"])

# Platform commission rate (5%)
PLATFORM_COMMISSION_RATE = 0.05


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

async def get_wallet_for_user(
    db: AsyncSession, user_id: uuid.UUID, currency: str = "GHS"
) -> Optional[Wallet]:
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == user_id,
            Wallet.currency == currency,
        )
    )
    return result.scalar_one_or_none()


def build_dispute_response(d: Dispute) -> DisputeResponse:
    return DisputeResponse(
        id=d.id,
        trip_id=d.trip_id,
        escrow_id=d.escrow_id,
        raised_by_user_id=d.raised_by_user_id,
        raised_by_name=d.raised_by.full_name if d.raised_by else None,
        against_user_id=d.against_user_id,
        against_user_name=d.against_user.full_name if d.against_user else None,
        reason=d.reason.value if hasattr(d.reason, "value") else d.reason,
        description=d.description,
        evidence_urls=d.evidence_urls,
        status=d.status.value if hasattr(d.status, "value") else d.status,
        resolution_notes=d.resolution_notes,
        resolved_by_name=d.resolved_by.full_name if d.resolved_by else None,
        shipper_refund_amount=float(d.shipper_refund_amount) if d.shipper_refund_amount else None,
        courier_payout_amount=float(d.courier_payout_amount) if d.courier_payout_amount else None,
        created_at=d.created_at,
        updated_at=d.updated_at,
        resolved_at=d.resolved_at,
    )


# ═══════════════════════════════════════════════════════════════
#  POST /escrow/hold-for-trip — Lock funds when bid is accepted
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/escrow/hold-for-trip",
    response_model=EscrowHoldResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create escrow hold for an accepted trip",
)
async def create_escrow_hold(
    trip_id: uuid.UUID,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> EscrowHoldResponse:
    """
    Lock the accepted bid amount from the shipper's wallet into escrow.

    **Called after a bid is accepted** (can be auto-triggered or manual).
    Validates:
    - Trip exists with status pickup_pending
    - Shipper has sufficient balance
    - No existing escrow for this trip
    """
    # Fetch trip with relationships
    trip_result = await db.execute(
        select(FreightTrip).where(FreightTrip.id == trip_id)
    )
    trip = trip_result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.status != TripStatus.PICKUP_PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Trip must be in pickup_pending status (current: {trip.status.value})",
        )

    # Check no existing escrow
    existing_result = await db.execute(
        select(EscrowHold).where(EscrowHold.trip_id == trip_id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Escrow already exists for this trip")

    # Get bid amount
    bid = trip.bid
    if not bid:
        raise HTTPException(status_code=400, detail="Trip has no associated bid")

    amount = float(bid.price)
    currency = bid.currency

    # Get shipper's wallet
    listing = trip.listing
    if not listing:
        raise HTTPException(status_code=400, detail="Trip has no associated listing")

    shipper_wallet = await get_wallet_for_user(db, listing.shipper_id, currency)
    if not shipper_wallet:
        raise HTTPException(
            status_code=400,
            detail="Shipper does not have a wallet. Please deposit funds first.",
        )

    if shipper_wallet.status != WalletStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Shipper wallet is frozen or closed")

    if float(shipper_wallet.balance) < amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient shipper balance. Available: {currency} {float(shipper_wallet.balance):.2f}, "
                   f"Required: {currency} {amount:.2f}",
        )

    # Get/create courier wallet
    courier_wallet = await get_wallet_for_user(db, trip.courier_id, currency)
    courier_wallet_id = courier_wallet.id if courier_wallet else None

    now = datetime.now(timezone.utc)

    # Deduct from shipper wallet → escrow
    shipper_wallet.balance = float(shipper_wallet.balance) - amount
    shipper_wallet.escrow_balance = float(shipper_wallet.escrow_balance) + amount
    shipper_wallet.updated_at = now

    # Create escrow hold
    escrow = EscrowHold(
        trip_id=trip_id,
        listing_id=listing.id,
        shipper_wallet_id=shipper_wallet.id,
        courier_wallet_id=courier_wallet_id,
        amount=amount,
        currency=currency,
        platform_commission_rate=PLATFORM_COMMISSION_RATE,
        status=EscrowStatus.HELD,
    )
    db.add(escrow)
    await db.flush()

    # Log the escrow_hold transaction on the shipper's wallet
    txn = Transaction(
        wallet_id=shipper_wallet.id,
        type=TransactionType.ESCROW_HOLD,
        amount=amount,
        currency=currency,
        fee=0.00,
        net_amount=amount,
        balance_after=float(shipper_wallet.balance),
        status=TransactionStatus.COMPLETED,
        reference_type="escrow",
        reference_id=str(escrow.id),
        description=f"Escrow hold for trip {trip_id} — {currency} {amount:.2f}",
        completed_at=now,
    )
    db.add(txn)
    await db.flush()

    return EscrowHoldResponse(
        id=escrow.id,
        trip_id=escrow.trip_id,
        listing_id=escrow.listing_id,
        amount=float(escrow.amount),
        currency=escrow.currency,
        platform_commission_rate=escrow.platform_commission_rate,
        status="held",
        created_at=escrow.created_at,
    )


# ═══════════════════════════════════════════════════════════════
#  POST /escrow/{id}/release — Release escrow after delivery
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/escrow/{escrow_id}/release",
    response_model=EscrowReleaseResponse,
    summary="Release escrow after confirmed delivery",
)
async def release_escrow(
    escrow_id: uuid.UUID,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> EscrowReleaseResponse:
    """
    Release escrow funds after delivery is confirmed.

    **Business logic:**
    1. Deduct platform commission (5%) from the held amount
    2. Credit the net amount to the courier's wallet
    3. Remove escrow balance from shipper's wallet tracking
    4. Create a PayoutSchedule for the courier
    5. Log all transactions in the ledger

    Only callable when the trip is in `confirmed` status.
    """
    # Get escrow
    escrow_result = await db.execute(
        select(EscrowHold).where(EscrowHold.id == escrow_id)
    )
    escrow = escrow_result.scalar_one_or_none()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow hold not found")

    if escrow.status != EscrowStatus.HELD:
        raise HTTPException(
            status_code=400,
            detail=f"Escrow is not in held status (current: {escrow.status.value})",
        )

    # Verify trip is confirmed
    trip = escrow.trip
    if not trip:
        raise HTTPException(status_code=400, detail="Associated trip not found")

    if trip.status != TripStatus.CONFIRMED:
        raise HTTPException(
            status_code=400,
            detail=f"Trip must be confirmed before escrow release (current: {trip.status.value})",
        )

    # Authorization: shipper, courier, or admin
    user_roles = user.role_names
    is_admin = "system_admin" in user_roles or "org_admin" in user_roles
    is_shipper = trip.listing and trip.listing.shipper_id == user.id
    if not (is_shipper or is_admin):
        raise HTTPException(status_code=403, detail="Only the shipper or admin can release escrow")

    now = datetime.now(timezone.utc)
    amount = float(escrow.amount)
    currency = escrow.currency

    # Calculate commission
    commission = round(amount * PLATFORM_COMMISSION_RATE, 2)
    courier_payout = round(amount - commission, 2)

    # Update escrow record
    escrow.platform_commission_amount = commission
    escrow.courier_payout_amount = courier_payout
    escrow.status = EscrowStatus.RELEASED
    escrow.released_at = now

    # Get shipper wallet — reduce escrow_balance
    shipper_wallet_result = await db.execute(
        select(Wallet).where(Wallet.id == escrow.shipper_wallet_id)
    )
    shipper_wallet = shipper_wallet_result.scalar_one()
    shipper_wallet.escrow_balance = float(shipper_wallet.escrow_balance) - amount
    shipper_wallet.updated_at = now

    # Get or create courier wallet
    courier_wallet = None
    if escrow.courier_wallet_id:
        cw_result = await db.execute(
            select(Wallet).where(Wallet.id == escrow.courier_wallet_id)
        )
        courier_wallet = cw_result.scalar_one_or_none()

    if courier_wallet is None:
        # Create courier wallet
        courier_wallet = Wallet(
            user_id=trip.courier_id,
            currency=currency,
            balance=0.00,
            escrow_balance=0.00,
            total_deposited=0.00,
            total_withdrawn=0.00,
            total_earned=0.00,
            status=WalletStatus.ACTIVE,
        )
        db.add(courier_wallet)
        await db.flush()
        escrow.courier_wallet_id = courier_wallet.id

    # Credit courier wallet
    courier_wallet.balance = float(courier_wallet.balance) + courier_payout
    courier_wallet.total_earned = float(courier_wallet.total_earned) + courier_payout
    courier_wallet.updated_at = now

    # ── Transaction ledger entries ────────────────────────────

    # 1. Escrow release on shipper wallet (informational)
    shipper_release_txn = Transaction(
        wallet_id=shipper_wallet.id,
        type=TransactionType.ESCROW_RELEASE,
        amount=amount,
        currency=currency,
        fee=0.00,
        net_amount=amount,
        balance_after=float(shipper_wallet.balance),
        status=TransactionStatus.COMPLETED,
        reference_type="escrow",
        reference_id=str(escrow.id),
        description=f"Escrow released for trip {trip.id}",
        completed_at=now,
    )
    db.add(shipper_release_txn)

    # 2. Commission deduction transaction (platform revenue)
    commission_txn = Transaction(
        wallet_id=shipper_wallet.id,
        type=TransactionType.COMMISSION,
        amount=commission,
        currency=currency,
        fee=0.00,
        net_amount=commission,
        balance_after=float(shipper_wallet.balance),
        status=TransactionStatus.COMPLETED,
        reference_type="escrow",
        reference_id=str(escrow.id),
        description=f"Platform commission ({PLATFORM_COMMISSION_RATE*100:.0f}%) on trip {trip.id}",
        completed_at=now,
    )
    db.add(commission_txn)

    # 3. Escrow release credit on courier wallet
    courier_credit_txn = Transaction(
        wallet_id=courier_wallet.id,
        type=TransactionType.ESCROW_RELEASE,
        amount=courier_payout,
        currency=currency,
        fee=commission,
        net_amount=courier_payout,
        balance_after=float(courier_wallet.balance),
        status=TransactionStatus.COMPLETED,
        reference_type="escrow",
        reference_id=str(escrow.id),
        description=f"Payment for trip {trip.id} (net of {PLATFORM_COMMISSION_RATE*100:.0f}% commission)",
        completed_at=now,
    )
    db.add(courier_credit_txn)

    # ── Payout schedule ──────────────────────────────────────

    payout = PayoutSchedule(
        courier_id=trip.courier_id,
        wallet_id=courier_wallet.id,
        escrow_id=escrow.id,
        trip_id=trip.id,
        amount=courier_payout,
        currency=currency,
        status=PayoutStatus.COMPLETED,  # Instant in-wallet payout
        due_date=now,
        paid_at=now,
    )
    db.add(payout)

    await db.flush()

    return EscrowReleaseResponse(
        message=f"Escrow released. Courier receives {currency} {courier_payout:.2f} "
                f"after {PLATFORM_COMMISSION_RATE*100:.0f}% platform commission.",
        escrow_id=escrow.id,
        trip_id=trip.id,
        total_amount=amount,
        platform_commission=commission,
        courier_payout=courier_payout,
        currency=currency,
    )


# ═══════════════════════════════════════════════════════════════
#  POST /escrow/{id}/refund — Refund escrow to shipper
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/escrow/{escrow_id}/refund",
    response_model=MessageResponse,
    summary="Refund escrow to shipper (admin or cancellation)",
)
async def refund_escrow(
    escrow_id: uuid.UUID,
    user: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Full refund of escrowed funds back to the shipper.
    Used for trip cancellation or dispute resolution in shipper's favour.
    Requires system_admin role.
    """
    escrow_result = await db.execute(
        select(EscrowHold).where(EscrowHold.id == escrow_id)
    )
    escrow = escrow_result.scalar_one_or_none()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow hold not found")

    if escrow.status not in (EscrowStatus.HELD, EscrowStatus.DISPUTED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot refund escrow with status: {escrow.status.value}",
        )

    now = datetime.now(timezone.utc)
    amount = float(escrow.amount)
    currency = escrow.currency

    # Credit back to shipper
    shipper_wallet_result = await db.execute(
        select(Wallet).where(Wallet.id == escrow.shipper_wallet_id)
    )
    shipper_wallet = shipper_wallet_result.scalar_one()
    shipper_wallet.balance = float(shipper_wallet.balance) + amount
    shipper_wallet.escrow_balance = float(shipper_wallet.escrow_balance) - amount
    shipper_wallet.updated_at = now

    # Update escrow
    escrow.status = EscrowStatus.REFUNDED
    escrow.refunded_at = now

    # Log transaction
    txn = Transaction(
        wallet_id=shipper_wallet.id,
        type=TransactionType.ESCROW_REFUND,
        amount=amount,
        currency=currency,
        fee=0.00,
        net_amount=amount,
        balance_after=float(shipper_wallet.balance),
        status=TransactionStatus.COMPLETED,
        reference_type="escrow",
        reference_id=str(escrow.id),
        description=f"Escrow refund for trip {escrow.trip_id}",
        completed_at=now,
    )
    db.add(txn)
    await db.flush()

    return MessageResponse(
        message=f"Escrow refunded. {currency} {amount:.2f} returned to shipper wallet."
    )


# ═══════════════════════════════════════════════════════════════
#  POST /disputes — Open a dispute
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/disputes",
    response_model=DisputeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open a dispute on a trip",
)
async def open_dispute(
    body: OpenDisputeRequest,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> DisputeResponse:
    """
    Open a dispute on a delivered trip.

    **When a dispute is opened:**
    1. Trip status is set to `disputed`
    2. Escrow status is set to `disputed` (funds remain locked)
    3. Both parties are notified (placeholder)
    4. Admin review is required to resolve

    Either the shipper or courier on the trip can open a dispute.
    """
    # Validate trip
    trip_result = await db.execute(
        select(FreightTrip).where(FreightTrip.id == body.trip_id)
    )
    trip = trip_result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Must be in disputable state
    disputable = {TripStatus.DELIVERED, TripStatus.CONFIRMED}
    if trip.status not in disputable:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot dispute a trip with status: {trip.status.value}. "
                   "Disputes can only be opened on delivered or confirmed trips.",
        )

    # Check authorization
    listing = trip.listing
    is_shipper = listing and listing.shipper_id == user.id
    is_courier = trip.courier_id == user.id
    if not (is_shipper or is_courier):
        raise HTTPException(status_code=403, detail="Only the shipper or courier can open a dispute")

    # Determine the "against" party
    if is_shipper:
        against_user_id = trip.courier_id
    else:
        against_user_id = listing.shipper_id if listing else trip.courier_id

    # Find the escrow hold
    escrow_result = await db.execute(
        select(EscrowHold).where(EscrowHold.trip_id == body.trip_id)
    )
    escrow = escrow_result.scalar_one_or_none()
    if not escrow:
        raise HTTPException(
            status_code=400,
            detail="No escrow hold found for this trip. Cannot open a dispute.",
        )

    # Check for existing open dispute
    existing_result = await db.execute(
        select(Dispute).where(
            Dispute.trip_id == body.trip_id,
            Dispute.status.in_([DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW, DisputeStatus.ESCALATED]),
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A dispute is already open for this trip")

    now = datetime.now(timezone.utc)

    # Update trip status
    trip.status = TripStatus.DISPUTED
    trip.updated_at = now

    # Update escrow status
    if escrow.status == EscrowStatus.HELD:
        escrow.status = EscrowStatus.DISPUTED

    # Create dispute
    dispute = Dispute(
        trip_id=body.trip_id,
        escrow_id=escrow.id,
        raised_by_user_id=user.id,
        against_user_id=against_user_id,
        reason=DisputeReason(body.reason),
        description=body.description,
        evidence_urls=body.evidence_urls,
        status=DisputeStatus.OPEN,
    )
    db.add(dispute)
    await db.flush()
    await db.refresh(dispute, attribute_names=["raised_by", "against_user"])

    return build_dispute_response(dispute)


# ═══════════════════════════════════════════════════════════════
#  GET /disputes — List disputes
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/disputes",
    response_model=DisputeListResponse,
    summary="List disputes (my disputes or all for admin)",
)
async def list_disputes(
    dispute_status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> DisputeListResponse:
    """Admins see all disputes. Users see only disputes they are party to."""
    user_roles = user.role_names
    is_admin = "system_admin" in user_roles or "org_admin" in user_roles

    stmt = select(Dispute)

    if not is_admin:
        stmt = stmt.where(
            (Dispute.raised_by_user_id == user.id)
            | (Dispute.against_user_id == user.id)
        )

    if dispute_status:
        stmt = stmt.where(Dispute.status == DisputeStatus(dispute_status.lower()))

    stmt = stmt.order_by(Dispute.created_at.desc())
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    disputes = result.scalars().all()

    return DisputeListResponse(
        disputes=[build_dispute_response(d) for d in disputes],
        total=len(disputes),
    )


# ═══════════════════════════════════════════════════════════════
#  GET /disputes/{id} — Dispute detail
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/disputes/{dispute_id}",
    response_model=DisputeResponse,
    summary="Get dispute detail",
)
async def get_dispute(
    dispute_id: uuid.UUID,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> DisputeResponse:
    result = await db.execute(
        select(Dispute).where(Dispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    # Auth check
    user_roles = user.role_names
    is_admin = "system_admin" in user_roles or "org_admin" in user_roles
    is_party = user.id in (dispute.raised_by_user_id, dispute.against_user_id)
    if not (is_admin or is_party):
        raise HTTPException(status_code=403, detail="Not authorised to view this dispute")

    return build_dispute_response(dispute)


# ═══════════════════════════════════════════════════════════════
#  POST /disputes/{id}/resolve — Admin resolves a dispute
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/disputes/{dispute_id}/resolve",
    response_model=DisputeResponse,
    summary="Resolve a dispute (admin only)",
)
async def resolve_dispute(
    dispute_id: uuid.UUID,
    body: ResolveDisputeRequest,
    user: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
) -> DisputeResponse:
    """
    Admin resolves a dispute. Three outcomes:

    1. **resolved_shipper** — Full refund to shipper, courier gets nothing
    2. **resolved_courier** — Full payout to courier (minus commission)
    3. **resolved_split** — Custom split: specify `shipper_refund_amount`
       and `courier_payout_amount`

    The resolution moves funds accordingly and closes the dispute.
    """
    result = await db.execute(
        select(Dispute).where(Dispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if dispute.status not in (DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW, DisputeStatus.ESCALATED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resolve dispute with status: {dispute.status.value}",
        )

    escrow = dispute.escrow
    if not escrow:
        raise HTTPException(status_code=400, detail="No escrow associated with this dispute")

    now = datetime.now(timezone.utc)
    amount = float(escrow.amount)
    currency = escrow.currency

    # Get wallets
    shipper_wallet_result = await db.execute(
        select(Wallet).where(Wallet.id == escrow.shipper_wallet_id)
    )
    shipper_wallet = shipper_wallet_result.scalar_one()

    courier_wallet = None
    if escrow.courier_wallet_id:
        cw_result = await db.execute(
            select(Wallet).where(Wallet.id == escrow.courier_wallet_id)
        )
        courier_wallet = cw_result.scalar_one_or_none()

    trip = dispute.trip

    if body.resolution == "resolved_shipper":
        # Full refund to shipper
        shipper_wallet.balance = float(shipper_wallet.balance) + amount
        shipper_wallet.escrow_balance = float(shipper_wallet.escrow_balance) - amount
        shipper_wallet.updated_at = now

        escrow.status = EscrowStatus.REFUNDED
        escrow.refunded_at = now
        dispute.shipper_refund_amount = amount
        dispute.courier_payout_amount = 0

        txn = Transaction(
            wallet_id=shipper_wallet.id,
            type=TransactionType.ESCROW_REFUND,
            amount=amount,
            currency=currency,
            fee=0.00,
            net_amount=amount,
            balance_after=float(shipper_wallet.balance),
            status=TransactionStatus.COMPLETED,
            reference_type="dispute",
            reference_id=str(dispute.id),
            description=f"Dispute resolved in shipper's favour — full refund for trip {escrow.trip_id}",
            completed_at=now,
        )
        db.add(txn)

    elif body.resolution == "resolved_courier":
        # Full payout to courier (minus commission)
        commission = round(amount * PLATFORM_COMMISSION_RATE, 2)
        courier_payout = round(amount - commission, 2)

        shipper_wallet.escrow_balance = float(shipper_wallet.escrow_balance) - amount
        shipper_wallet.updated_at = now

        if courier_wallet is None:
            courier_wallet = Wallet(
                user_id=trip.courier_id if trip else escrow.courier_wallet_id,
                currency=currency,
                balance=0.00,
                escrow_balance=0.00,
                total_deposited=0.00,
                total_withdrawn=0.00,
                total_earned=0.00,
                status=WalletStatus.ACTIVE,
            )
            db.add(courier_wallet)
            await db.flush()

        courier_wallet.balance = float(courier_wallet.balance) + courier_payout
        courier_wallet.total_earned = float(courier_wallet.total_earned) + courier_payout
        courier_wallet.updated_at = now

        escrow.platform_commission_amount = commission
        escrow.courier_payout_amount = courier_payout
        escrow.status = EscrowStatus.RELEASED
        escrow.released_at = now
        dispute.courier_payout_amount = courier_payout
        dispute.shipper_refund_amount = 0

        # Commission txn
        db.add(Transaction(
            wallet_id=shipper_wallet.id,
            type=TransactionType.COMMISSION,
            amount=commission,
            currency=currency,
            fee=0.00,
            net_amount=commission,
            balance_after=float(shipper_wallet.balance),
            status=TransactionStatus.COMPLETED,
            reference_type="dispute",
            reference_id=str(dispute.id),
            description=f"Platform commission after dispute resolution — trip {escrow.trip_id}",
            completed_at=now,
        ))
        # Courier credit
        db.add(Transaction(
            wallet_id=courier_wallet.id,
            type=TransactionType.ESCROW_RELEASE,
            amount=courier_payout,
            currency=currency,
            fee=commission,
            net_amount=courier_payout,
            balance_after=float(courier_wallet.balance),
            status=TransactionStatus.COMPLETED,
            reference_type="dispute",
            reference_id=str(dispute.id),
            description=f"Dispute resolved in courier's favour — trip {escrow.trip_id}",
            completed_at=now,
        ))

    elif body.resolution == "resolved_split":
        # Custom split
        shipper_refund = body.shipper_refund_amount or 0
        courier_payout = body.courier_payout_amount or 0

        if round(shipper_refund + courier_payout, 2) > amount:
            raise HTTPException(
                status_code=400,
                detail=f"Split amounts ({currency} {shipper_refund + courier_payout:.2f}) "
                       f"exceed escrow amount ({currency} {amount:.2f})",
            )

        shipper_wallet.escrow_balance = float(shipper_wallet.escrow_balance) - amount
        shipper_wallet.updated_at = now

        if shipper_refund > 0:
            shipper_wallet.balance = float(shipper_wallet.balance) + shipper_refund
            db.add(Transaction(
                wallet_id=shipper_wallet.id,
                type=TransactionType.ESCROW_REFUND,
                amount=shipper_refund,
                currency=currency,
                fee=0.00,
                net_amount=shipper_refund,
                balance_after=float(shipper_wallet.balance),
                status=TransactionStatus.COMPLETED,
                reference_type="dispute",
                reference_id=str(dispute.id),
                description=f"Partial refund (dispute split) — trip {escrow.trip_id}",
                completed_at=now,
            ))

        if courier_payout > 0:
            if courier_wallet is None:
                courier_wallet = Wallet(
                    user_id=trip.courier_id if trip else uuid.uuid4(),
                    currency=currency,
                    balance=0.00,
                    escrow_balance=0.00,
                    total_deposited=0.00,
                    total_withdrawn=0.00,
                    total_earned=0.00,
                    status=WalletStatus.ACTIVE,
                )
                db.add(courier_wallet)
                await db.flush()

            courier_wallet.balance = float(courier_wallet.balance) + courier_payout
            courier_wallet.total_earned = float(courier_wallet.total_earned) + courier_payout
            courier_wallet.updated_at = now

            db.add(Transaction(
                wallet_id=courier_wallet.id,
                type=TransactionType.ESCROW_RELEASE,
                amount=courier_payout,
                currency=currency,
                fee=0.00,
                net_amount=courier_payout,
                balance_after=float(courier_wallet.balance),
                status=TransactionStatus.COMPLETED,
                reference_type="dispute",
                reference_id=str(dispute.id),
                description=f"Partial payout (dispute split) — trip {escrow.trip_id}",
                completed_at=now,
            ))

        # Platform keeps remainder as commission
        platform_take = round(amount - shipper_refund - courier_payout, 2)
        if platform_take > 0:
            db.add(Transaction(
                wallet_id=shipper_wallet.id,
                type=TransactionType.COMMISSION,
                amount=platform_take,
                currency=currency,
                fee=0.00,
                net_amount=platform_take,
                balance_after=float(shipper_wallet.balance),
                status=TransactionStatus.COMPLETED,
                reference_type="dispute",
                reference_id=str(dispute.id),
                description=f"Platform commission from dispute split — trip {escrow.trip_id}",
                completed_at=now,
            ))

        escrow.status = EscrowStatus.PARTIALLY_RELEASED
        escrow.released_at = now
        escrow.courier_payout_amount = courier_payout
        escrow.platform_commission_amount = platform_take
        dispute.shipper_refund_amount = shipper_refund
        dispute.courier_payout_amount = courier_payout

    # Finalize dispute
    dispute.status = DisputeStatus(body.resolution)
    dispute.resolution_notes = body.resolution_notes
    dispute.resolved_by_user_id = user.id
    dispute.resolved_at = now
    dispute.updated_at = now

    await db.flush()
    await db.refresh(dispute, attribute_names=["raised_by", "against_user", "resolved_by"])

    return build_dispute_response(dispute)


# ═══════════════════════════════════════════════════════════════
#  POST /disputes/{id}/escalate — Escalate a dispute
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/disputes/{dispute_id}/escalate",
    response_model=DisputeResponse,
    summary="Escalate a dispute for senior review",
)
async def escalate_dispute(
    dispute_id: uuid.UUID,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> DisputeResponse:
    """Mark a dispute for escalated review (either party or admin can escalate)."""
    result = await db.execute(
        select(Dispute).where(Dispute.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    user_roles = user.role_names
    is_admin = "system_admin" in user_roles or "org_admin" in user_roles
    is_party = user.id in (dispute.raised_by_user_id, dispute.against_user_id)
    if not (is_admin or is_party):
        raise HTTPException(status_code=403, detail="Not authorised to escalate this dispute")

    if dispute.status not in (DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot escalate dispute with status: {dispute.status.value}",
        )

    dispute.status = DisputeStatus.ESCALATED
    dispute.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(dispute, attribute_names=["raised_by", "against_user", "resolved_by"])

    return build_dispute_response(dispute)
