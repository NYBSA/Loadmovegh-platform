"""
LoadMoveGH — Wallet & Payment Endpoints
Deposit via MoMo, withdraw, view balance, transaction ledger, escrow holds.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user, require_any_authenticated
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.wallet import (
    EscrowHold,
    EscrowStatus,
    MoMoDirection,
    MoMoPayment,
    MoMoProvider,
    MoMoStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
    Wallet,
    WalletStatus,
)
from app.schemas.wallet import (
    EscrowHoldResponse,
    EscrowListResponse,
    MessageResponse,
    MoMoCallbackPayload,
    MoMoDepositRequest,
    MoMoDepositResponse,
    MoMoWithdrawRequest,
    MoMoWithdrawResponse,
    TransactionListResponse,
    TransactionResponse,
    WalletResponse,
    WalletSummary,
)

router = APIRouter(prefix="/wallets", tags=["Wallet & Payments"])


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

async def get_or_create_wallet(
    db: AsyncSession, user: User, currency: str = "GHS"
) -> Wallet:
    """Get existing wallet for user+currency, or create one."""
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == user.id,
            Wallet.currency == currency,
        )
    )
    wallet = result.scalar_one_or_none()

    if wallet is None:
        wallet = Wallet(
            user_id=user.id,
            org_id=user.org_id,
            currency=currency,
            balance=0.00,
            escrow_balance=0.00,
            total_deposited=0.00,
            total_withdrawn=0.00,
            total_earned=0.00,
            status=WalletStatus.ACTIVE,
        )
        db.add(wallet)
        await db.flush()

    return wallet


def build_transaction_response(txn: Transaction) -> TransactionResponse:
    return TransactionResponse(
        id=txn.id,
        wallet_id=txn.wallet_id,
        type=txn.type.value if hasattr(txn.type, "value") else txn.type,
        amount=float(txn.amount),
        currency=txn.currency,
        fee=float(txn.fee),
        net_amount=float(txn.net_amount),
        balance_after=float(txn.balance_after),
        status=txn.status.value if hasattr(txn.status, "value") else txn.status,
        reference_type=txn.reference_type,
        reference_id=txn.reference_id,
        description=txn.description,
        created_at=txn.created_at,
        completed_at=txn.completed_at,
    )


def build_wallet_response(wallet: Wallet) -> WalletResponse:
    return WalletResponse(
        id=wallet.id,
        user_id=wallet.user_id,
        balance=float(wallet.balance),
        escrow_balance=float(wallet.escrow_balance),
        total_deposited=float(wallet.total_deposited),
        total_withdrawn=float(wallet.total_withdrawn),
        total_earned=float(wallet.total_earned),
        currency=wallet.currency,
        status=wallet.status.value if hasattr(wallet.status, "value") else wallet.status,
        is_verified=wallet.is_verified,
        created_at=wallet.created_at,
        updated_at=wallet.updated_at,
    )


# ═══════════════════════════════════════════════════════════════
#  GET /wallets/me — My wallet balance
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/me",
    response_model=WalletResponse,
    summary="Get my wallet balance",
)
async def get_my_wallet(
    currency: str = Query("GHS", max_length=3),
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """
    Returns the current user's wallet for the specified currency.
    Creates the wallet if it doesn't exist.
    """
    wallet = await get_or_create_wallet(db, user, currency.upper())
    return build_wallet_response(wallet)


# ═══════════════════════════════════════════════════════════════
#  GET /wallets/me/summary — Quick balance summary
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/me/summary",
    response_model=WalletSummary,
    summary="Quick wallet summary for UI",
)
async def wallet_summary(
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> WalletSummary:
    wallet = await get_or_create_wallet(db, user)
    return WalletSummary(
        balance=float(wallet.balance),
        escrow_balance=float(wallet.escrow_balance),
        currency=wallet.currency,
        status=wallet.status.value if hasattr(wallet.status, "value") else wallet.status,
    )


# ═══════════════════════════════════════════════════════════════
#  GET /wallets/me/transactions — Transaction ledger
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/me/transactions",
    response_model=TransactionListResponse,
    summary="View transaction history",
)
async def list_transactions(
    txn_type: Optional[str] = Query(None, description="Filter: deposit, withdrawal, escrow_hold, etc."),
    txn_status: Optional[str] = Query(None, description="Filter: pending, completed, failed"),
    sort_order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    """
    Paginated transaction ledger for the current user's wallet.
    Supports filtering by transaction type and status.
    """
    wallet = await get_or_create_wallet(db, user)

    stmt = select(Transaction).where(Transaction.wallet_id == wallet.id)

    if txn_type:
        stmt = stmt.where(Transaction.type == TransactionType(txn_type.lower()))
    if txn_status:
        stmt = stmt.where(Transaction.status == TransactionStatus(txn_status.lower()))

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Order and paginate
    if sort_order.lower() == "asc":
        stmt = stmt.order_by(Transaction.created_at.asc())
    else:
        stmt = stmt.order_by(Transaction.created_at.desc())

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    transactions = result.scalars().all()

    return TransactionListResponse(
        transactions=[build_transaction_response(t) for t in transactions],
        total=total,
        page=page,
        per_page=per_page,
    )


# ═══════════════════════════════════════════════════════════════
#  POST /wallets/me/deposit — Deposit via MoMo
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/me/deposit",
    response_model=MoMoDepositResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deposit funds via Mobile Money",
)
async def deposit_momo(
    body: MoMoDepositRequest,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> MoMoDepositResponse:
    """
    Initiate a deposit via MTN Mobile Money (or Vodafone/AirtelTigo).

    **Flow:**
    1. Creates a pending Transaction and MoMoPayment record
    2. Calls the MoMo Collections API to request payment
    3. User receives USSD prompt on their phone to approve
    4. MoMo provider calls our webhook on completion
    5. Webhook handler credits the wallet

    Note: In production, step 2 calls the actual MTN MoMo API.
    This endpoint creates the records and simulates the initiation.
    """
    wallet = await get_or_create_wallet(db, user, body.currency)

    if wallet.status != WalletStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Wallet is frozen or closed")

    # Create the pending transaction
    txn = Transaction(
        wallet_id=wallet.id,
        type=TransactionType.DEPOSIT,
        amount=body.amount,
        currency=body.currency,
        fee=0.00,  # MoMo collection fees typically borne by merchant
        net_amount=body.amount,
        balance_after=float(wallet.balance),  # Unchanged until confirmed
        status=TransactionStatus.PENDING,
        reference_type="momo_payment",
        description=f"MoMo deposit via {body.provider.upper()} ({body.phone_number})",
    )
    db.add(txn)
    await db.flush()

    # Generate a mock external transaction ID (in production: call MoMo API)
    external_id = f"MOMO-{uuid.uuid4().hex[:12].upper()}"

    # Create MoMo payment record
    momo = MoMoPayment(
        wallet_id=wallet.id,
        transaction_id=txn.id,
        provider=MoMoProvider(body.provider),
        direction=MoMoDirection.COLLECTION,
        phone_number=body.phone_number,
        amount=body.amount,
        currency=body.currency,
        fee=0.00,
        external_transaction_id=external_id,
        callback_url=f"{settings.API_V1_PREFIX}/wallets/momo-callback",
        status=MoMoStatus.PENDING,
    )
    db.add(momo)
    await db.flush()

    # Link MoMo payment to transaction
    txn.reference_id = str(momo.id)

    await db.flush()

    return MoMoDepositResponse(
        momo_payment_id=momo.id,
        transaction_id=txn.id,
        provider=body.provider,
        phone_number=body.phone_number,
        amount=body.amount,
        currency=body.currency,
        status="pending",
        external_transaction_id=external_id,
    )


# ═══════════════════════════════════════════════════════════════
#  POST /wallets/me/withdraw — Withdraw to MoMo
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/me/withdraw",
    response_model=MoMoWithdrawResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Withdraw funds to Mobile Money",
)
async def withdraw_momo(
    body: MoMoWithdrawRequest,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> MoMoWithdrawResponse:
    """
    Withdraw available balance to a Ghana MoMo number.

    **Flow:**
    1. Validates sufficient available balance
    2. Deducts withdrawal amount + fee from wallet immediately
    3. Calls MoMo Disbursement API
    4. If disbursement fails, amount is reversed

    Withdrawal fee: 1% of amount (min GHS 0.50, max GHS 10.00).
    """
    wallet = await get_or_create_wallet(db, user, body.currency)

    if wallet.status != WalletStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Wallet is frozen or closed")

    # Calculate fee: 1% with bounds
    fee = round(max(0.50, min(body.amount * 0.01, 10.00)), 2)
    total_debit = body.amount + fee

    if float(wallet.balance) < total_debit:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Available: GHS {float(wallet.balance):.2f}, "
                   f"Required: GHS {total_debit:.2f} (amount + {fee:.2f} fee)",
        )

    # Debit wallet immediately (optimistic)
    wallet.balance = float(wallet.balance) - total_debit
    wallet.total_withdrawn = float(wallet.total_withdrawn) + body.amount
    wallet.updated_at = datetime.now(timezone.utc)

    # Create transaction
    txn = Transaction(
        wallet_id=wallet.id,
        type=TransactionType.WITHDRAWAL,
        amount=body.amount,
        currency=body.currency,
        fee=fee,
        net_amount=body.amount,
        balance_after=float(wallet.balance),
        status=TransactionStatus.PROCESSING,
        reference_type="momo_payment",
        description=f"Withdrawal to {body.provider.upper()} ({body.phone_number})",
    )
    db.add(txn)
    await db.flush()

    external_id = f"MOMO-D-{uuid.uuid4().hex[:12].upper()}"

    momo = MoMoPayment(
        wallet_id=wallet.id,
        transaction_id=txn.id,
        provider=MoMoProvider(body.provider),
        direction=MoMoDirection.DISBURSEMENT,
        phone_number=body.phone_number,
        amount=body.amount,
        currency=body.currency,
        fee=fee,
        external_transaction_id=external_id,
        callback_url=f"{settings.API_V1_PREFIX}/wallets/momo-callback",
        status=MoMoStatus.PENDING,
    )
    db.add(momo)
    await db.flush()

    txn.reference_id = str(momo.id)
    await db.flush()

    return MoMoWithdrawResponse(
        momo_payment_id=momo.id,
        transaction_id=txn.id,
        provider=body.provider,
        phone_number=body.phone_number,
        amount=body.amount,
        fee=fee,
        net_amount=body.amount,
        currency=body.currency,
        status="processing",
    )


# ═══════════════════════════════════════════════════════════════
#  POST /wallets/momo-callback — MoMo webhook
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/momo-callback",
    response_model=MessageResponse,
    summary="MoMo provider callback (webhook)",
    include_in_schema=False,  # Internal endpoint
)
async def momo_callback(
    body: MoMoCallbackPayload,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Handles callbacks from MoMo provider when a payment is completed or failed.
    In production, this should verify the callback signature.

    **On success (collection/deposit):**
    - Credits wallet balance
    - Marks transaction as completed

    **On failure:**
    - Marks transaction as failed
    - For withdrawals: reverses the debit
    """
    # Find the MoMo payment
    result = await db.execute(
        select(MoMoPayment).where(
            MoMoPayment.external_transaction_id == body.external_transaction_id
        )
    )
    momo = result.scalar_one_or_none()
    if not momo:
        raise HTTPException(status_code=404, detail="MoMo payment not found")

    if momo.status in (MoMoStatus.SUCCESS, MoMoStatus.FAILED):
        return MessageResponse(message="Payment already processed")

    now = datetime.now(timezone.utc)

    if body.status.lower() == "success":
        momo.status = MoMoStatus.SUCCESS
        momo.provider_reference = body.provider_reference
        momo.completed_at = now

        # Credit wallet for deposits
        if momo.direction == MoMoDirection.COLLECTION:
            wallet_result = await db.execute(
                select(Wallet).where(Wallet.id == momo.wallet_id)
            )
            wallet = wallet_result.scalar_one()
            wallet.balance = float(wallet.balance) + float(momo.amount)
            wallet.total_deposited = float(wallet.total_deposited) + float(momo.amount)
            wallet.updated_at = now

            # Update transaction
            if momo.transaction_id:
                txn_result = await db.execute(
                    select(Transaction).where(Transaction.id == momo.transaction_id)
                )
                txn = txn_result.scalar_one_or_none()
                if txn:
                    txn.status = TransactionStatus.COMPLETED
                    txn.balance_after = float(wallet.balance)
                    txn.completed_at = now

        # For disbursements, just mark as completed (wallet already debited)
        elif momo.direction == MoMoDirection.DISBURSEMENT:
            if momo.transaction_id:
                txn_result = await db.execute(
                    select(Transaction).where(Transaction.id == momo.transaction_id)
                )
                txn = txn_result.scalar_one_or_none()
                if txn:
                    txn.status = TransactionStatus.COMPLETED
                    txn.completed_at = now

    elif body.status.lower() in ("failed", "timeout", "cancelled"):
        momo.status = MoMoStatus.FAILED
        momo.failure_reason = body.message or f"Payment {body.status}"
        momo.completed_at = now

        # For failed disbursements, reverse the debit
        if momo.direction == MoMoDirection.DISBURSEMENT:
            wallet_result = await db.execute(
                select(Wallet).where(Wallet.id == momo.wallet_id)
            )
            wallet = wallet_result.scalar_one()
            reversal_amount = float(momo.amount) + float(momo.fee)
            wallet.balance = float(wallet.balance) + reversal_amount
            wallet.total_withdrawn = float(wallet.total_withdrawn) - float(momo.amount)
            wallet.updated_at = now

        # Mark transaction as failed
        if momo.transaction_id:
            txn_result = await db.execute(
                select(Transaction).where(Transaction.id == momo.transaction_id)
            )
            txn = txn_result.scalar_one_or_none()
            if txn:
                txn.status = TransactionStatus.FAILED
                txn.completed_at = now

    await db.flush()
    return MessageResponse(message=f"Callback processed: {body.status}")


# ═══════════════════════════════════════════════════════════════
#  GET /wallets/me/escrow-holds — View my escrow holds
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/me/escrow-holds",
    response_model=EscrowListResponse,
    summary="View my escrow holds",
)
async def list_escrow_holds(
    escrow_status: Optional[str] = Query(None, description="Filter: held, released, refunded, disputed"),
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> EscrowListResponse:
    """View escrow holds related to the current user (as shipper or courier)."""
    wallet = await get_or_create_wallet(db, user)

    stmt = select(EscrowHold).where(
        (EscrowHold.shipper_wallet_id == wallet.id)
        | (EscrowHold.courier_wallet_id == wallet.id)
    )

    if escrow_status:
        stmt = stmt.where(EscrowHold.status == EscrowStatus(escrow_status.lower()))

    stmt = stmt.order_by(EscrowHold.created_at.desc())
    result = await db.execute(stmt)
    holds = result.scalars().all()

    items = []
    for h in holds:
        items.append(EscrowHoldResponse(
            id=h.id,
            trip_id=h.trip_id,
            listing_id=h.listing_id,
            amount=float(h.amount),
            currency=h.currency,
            platform_commission_rate=h.platform_commission_rate,
            platform_commission_amount=float(h.platform_commission_amount) if h.platform_commission_amount else None,
            courier_payout_amount=float(h.courier_payout_amount) if h.courier_payout_amount else None,
            status=h.status.value if hasattr(h.status, "value") else h.status,
            created_at=h.created_at,
            released_at=h.released_at,
            refunded_at=h.refunded_at,
        ))

    return EscrowListResponse(escrow_holds=items, total=len(items))
