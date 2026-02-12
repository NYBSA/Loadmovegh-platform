"""
LoadMoveGH — API Endpoints: Fraud Detection & Risk Management
=============================================================

GET  /fraud/risk/{user_id}             — View a user's risk profile
POST /fraud/scan/{user_id}             — Trigger a full fraud scan
GET  /fraud/alerts                     — List fraud alerts (paginated)
GET  /fraud/alerts/{alert_id}          — Get alert details
POST /fraud/alerts/{alert_id}/resolve  — Admin: resolve an alert
POST /fraud/alerts/{alert_id}/assign   — Admin: assign to investigator
GET  /fraud/dashboard                  — Admin fraud overview
GET  /fraud/signals/{user_id}          — List raw signals for a user
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import (
    get_current_active_user,
    require_system_admin,
)
from app.core.database import get_db
from app.models.fraud import (
    AlertStatus,
    DecisionAction,
    FraudAlert,
    FraudCategory,
    FraudDecision,
    FraudSignal as FraudSignalModel,
    RiskLevel,
    RiskProfile,
    SignalSeverity,
)
from app.models.freight import FreightBid, FreightListing, FreightTrip
from app.models.user import Organization, User
from app.models.wallet import MoMoPayment, Transaction, Wallet
from app.ml.fraud import (
    FraudScanResult,
    Signal,
    UserBehaviourSnapshot,
    run_fraud_scan,
)
from app.schemas.fraud import (
    ALERT_STATUSES,
    DECISION_ACTIONS,
    AlertListResponse,
    CategoryDashboardStat,
    CategoryScoreResponse,
    FraudAlertResponse,
    FraudDashboardResponse,
    FraudScanResponse,
    FraudSignalResponse,
    ResolveAlertRequest,
    ResolveAlertResponse,
    RiskProfileResponse,
)

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


# ───────────────────────────────────────────────────────────
#  SNAPSHOT BUILDER (hydrates from DB)
# ───────────────────────────────────────────────────────────

async def _build_snapshot(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> UserBehaviourSnapshot:
    """
    Query all relevant tables and build a UserBehaviourSnapshot
    that the fraud engine can evaluate without touching the DB.
    """
    # ── User & Org ───────────────────────────────────────────
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)
    account_age = (now - user.created_at).days if user.created_at else 0

    org_name = ""
    org_type = ""
    org_status = ""
    org_reg = ""
    org_created_days = 0
    org_id_str: Optional[str] = None
    if user.org_id:
        org = await db.get(Organization, user.org_id)
        if org:
            org_id_str = str(org.id)
            org_name = org.name or ""
            org_type = org.type.value if org.type else ""
            org_status = org.status.value if org.status else ""
            org_reg = org.registration_number or ""
            org_created_days = (now - org.created_at).days if org.created_at else 0

    roles = user.role_names

    # ── Listings ─────────────────────────────────────────────
    listing_q = select(FreightListing).where(FreightListing.shipper_id == user_id)
    listings_result = await db.execute(listing_q)
    listings = listings_result.scalars().all()

    total_listings = len(listings)
    active_listings = sum(1 for l in listings if l.status.value in ("active", "bidding"))
    cancelled_listings = sum(1 for l in listings if l.status.value == "cancelled")
    listings_no_bids = sum(1 for l in listings if l.bid_count == 0)
    month_ago = now - timedelta(days=30)
    listings_30d = sum(1 for l in listings if l.created_at and l.created_at >= month_ago)

    # ── Bids ─────────────────────────────────────────────────
    bid_q = select(FreightBid).where(FreightBid.courier_id == user_id)
    bids_result = await db.execute(bid_q)
    bids = bids_result.scalars().all()

    total_bids = len(bids)
    bids_accepted = sum(1 for b in bids if b.status.value == "accepted")
    bids_rejected = sum(1 for b in bids if b.status.value == "rejected")
    bids_withdrawn = sum(1 for b in bids if b.status.value == "withdrawn")

    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)
    bids_24h = sum(1 for b in bids if b.created_at and b.created_at >= day_ago)
    bids_7d = sum(1 for b in bids if b.created_at and b.created_at >= week_ago)

    bid_prices_30d = [
        float(b.price) for b in bids
        if b.created_at and b.created_at >= month_ago and b.price
    ]
    avg_bid = sum(bid_prices_30d) / len(bid_prices_30d) if bid_prices_30d else 0.0

    # ── Market pricing context ───────────────────────────────
    # Get average accepted bid price across all routes in the last 90 days
    ninety_days_ago = now - timedelta(days=90)
    market_q = select(func.avg(FreightBid.price), func.stddev(FreightBid.price)).where(
        and_(
            FreightBid.status == "accepted",
            FreightBid.created_at >= ninety_days_ago,
        )
    )
    market_result = await db.execute(market_q)
    market_row = market_result.one_or_none()
    market_avg = float(market_row[0]) if market_row and market_row[0] else 0.0
    market_std = float(market_row[1]) if market_row and market_row[1] else 0.0
    bid_vs_market = (avg_bid / market_avg) if market_avg > 0 and avg_bid > 0 else 1.0

    # ── Trips ────────────────────────────────────────────────
    trip_q = select(FreightTrip).where(FreightTrip.courier_id == user_id)
    trips_result = await db.execute(trip_q)
    trips = trips_result.scalars().all()

    total_trips = len(trips)
    trips_completed = sum(1 for t in trips if t.status.value in ("confirmed", "delivered"))
    trips_cancelled = sum(1 for t in trips if t.status.value == "cancelled")
    trips_disputed = sum(1 for t in trips if t.status.value == "disputed")
    cancel_7d = sum(
        1 for t in trips
        if t.status.value == "cancelled" and t.updated_at and t.updated_at >= week_ago
    )
    cancel_24h = sum(
        1 for t in trips
        if t.status.value == "cancelled" and t.updated_at and t.updated_at >= day_ago
    )
    # Cancel-after-accept: trips that were assigned (bid accepted) then cancelled
    cancel_after_accept = sum(
        1 for t in trips
        if t.status.value == "cancelled" and t.started_at is not None
    )

    # ── Wallet & Transactions ────────────────────────────────
    wallet_q = select(Wallet).where(Wallet.user_id == user_id)
    wallet_result = await db.execute(wallet_q)
    wallet = wallet_result.scalar_one_or_none()

    total_deposits = 0
    total_withdrawals = 0
    deposits_24h = 0
    withdrawals_24h = 0
    deposits_7d = 0
    withdrawals_7d = 0
    total_deposit_amount = 0.0
    total_withdrawal_amount = 0.0
    deposit_amount_24h = 0.0
    withdrawal_amount_24h = 0.0
    failed_payments_7d = 0
    largest_deposit = 0.0
    largest_withdrawal = 0.0

    if wallet:
        txn_q = select(Transaction).where(Transaction.wallet_id == wallet.id)
        txn_result = await db.execute(txn_q)
        txns = txn_result.scalars().all()

        for t in txns:
            amount = float(t.amount) if t.amount else 0.0
            is_deposit = t.type.value == "deposit"
            is_withdrawal = t.type.value == "withdrawal"
            in_24h = t.created_at and t.created_at >= day_ago
            in_7d = t.created_at and t.created_at >= week_ago

            if is_deposit:
                total_deposits += 1
                total_deposit_amount += amount
                if amount > largest_deposit:
                    largest_deposit = amount
                if in_24h:
                    deposits_24h += 1
                    deposit_amount_24h += amount
                if in_7d:
                    deposits_7d += 1
            elif is_withdrawal:
                total_withdrawals += 1
                total_withdrawal_amount += amount
                if amount > largest_withdrawal:
                    largest_withdrawal = amount
                if in_24h:
                    withdrawals_24h += 1
                    withdrawal_amount_24h += amount
                if in_7d:
                    withdrawals_7d += 1

            if t.status.value == "failed" and in_7d:
                failed_payments_7d += 1

        # Deposit→Withdraw cycle detection (deposits followed by withdrawal within 1h)
        deposit_times = sorted([
            t.created_at for t in txns
            if t.type.value == "deposit" and t.status.value == "completed" and t.created_at
        ])
        withdrawal_times = sorted([
            t.created_at for t in txns
            if t.type.value == "withdrawal" and t.status.value in ("completed", "processing")
            and t.created_at
        ])
        cycles = 0
        for dt in deposit_times:
            for wt in withdrawal_times:
                if timedelta(0) < (wt - dt) < timedelta(hours=1):
                    cycles += 1
                    break

        # Split transaction detection: multiple txns within 10 min summing to round number
        recent_deposits = sorted(
            [t for t in txns if t.type.value == "deposit" and in_7d and t.created_at],
            key=lambda x: x.created_at,  # type: ignore[arg-type]
        )
        split_count = 0
        for i in range(len(recent_deposits)):
            window_sum = 0.0
            for j in range(i, min(i + 5, len(recent_deposits))):
                if (recent_deposits[j].created_at - recent_deposits[i].created_at) < timedelta(minutes=10):  # type: ignore[operator]
                    window_sum += float(recent_deposits[j].amount)
            if window_sum > 0 and window_sum % 100 < 5:  # Near-round number
                split_count += 1

    else:
        cycles = 0
        split_count = 0

    # ── MoMo phone diversity ─────────────────────────────────
    distinct_phones = 0
    if wallet:
        momo_q = select(func.count(func.distinct(MoMoPayment.phone_number))).where(
            MoMoPayment.wallet_id == wallet.id
        )
        momo_result = await db.execute(momo_q)
        distinct_phones = momo_result.scalar() or 0

    # ── Disputes ─────────────────────────────────────────────
    from app.models.wallet import Dispute
    dispute_q = select(Dispute).where(
        (Dispute.raised_by_user_id == user_id) | (Dispute.against_user_id == user_id)
    )
    dispute_result = await db.execute(dispute_q)
    disputes = dispute_result.scalars().all()

    disputes_raised = sum(1 for d in disputes if str(d.raised_by_user_id) == str(user_id))
    disputes_lost = sum(
        1 for d in disputes
        if str(d.against_user_id) == str(user_id)
        and d.status.value in ("resolved_shipper", "resolved_courier")
    )
    disputes_fraud = sum(1 for d in disputes if d.reason.value == "fraud")

    # ── Counterparty patterns ────────────────────────────────
    pairs: list[tuple[str, str]] = []
    for b in bids:
        if b.listing:
            pairs.append((str(b.listing.shipper_id), str(b.courier_id)))

    return UserBehaviourSnapshot(
        user_id=str(user_id),
        full_name=user.full_name,
        org_id=org_id_str,
        org_name=org_name,
        org_type=org_type,
        org_status=org_status,
        org_registration_number=org_reg,
        org_created_days_ago=org_created_days,
        account_age_days=account_age,
        kyc_status=user.kyc_status.value if user.kyc_status else "not_started",
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        is_active=user.is_active,
        role_names=roles,
        total_listings=total_listings,
        active_listings=active_listings,
        cancelled_listings=cancelled_listings,
        listings_with_no_bids=listings_no_bids,
        listings_last_30d=listings_30d,
        total_bids_placed=total_bids,
        bids_accepted=bids_accepted,
        bids_rejected=bids_rejected,
        bids_withdrawn=bids_withdrawn,
        bids_last_24h=bids_24h,
        bids_last_7d=bids_7d,
        avg_bid_price=avg_bid,
        bid_prices_last_30d=bid_prices_30d,
        total_trips=total_trips,
        trips_completed=trips_completed,
        trips_cancelled=trips_cancelled,
        trips_disputed=trips_disputed,
        cancellations_last_7d=cancel_7d,
        cancellations_last_24h=cancel_24h,
        cancel_after_accept_count=cancel_after_accept,
        market_avg_price_for_routes=market_avg,
        price_std_dev=market_std,
        bid_vs_market_ratio=bid_vs_market,
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        deposits_last_24h=deposits_24h,
        withdrawals_last_24h=withdrawals_24h,
        deposits_last_7d=deposits_7d,
        withdrawals_last_7d=withdrawals_7d,
        total_deposit_amount=total_deposit_amount,
        total_withdrawal_amount=total_withdrawal_amount,
        deposit_amount_last_24h=deposit_amount_24h,
        withdrawal_amount_last_24h=withdrawal_amount_24h,
        failed_payments_last_7d=failed_payments_7d,
        distinct_momo_phones_used=distinct_phones,
        deposit_withdraw_cycles=cycles,
        split_transaction_count=split_count,
        largest_single_deposit=largest_deposit,
        largest_single_withdrawal=largest_withdrawal,
        disputes_raised=disputes_raised,
        disputes_lost=disputes_lost,
        disputes_as_fraud_reason=disputes_fraud,
        shipper_courier_pairs=pairs,
    )


# ───────────────────────────────────────────────────────────
#  HELPERS
# ───────────────────────────────────────────────────────────

def _build_alert_response(alert: FraudAlert) -> FraudAlertResponse:
    return FraudAlertResponse(
        id=str(alert.id),
        user_id=str(alert.user_id),
        user_name=alert.user.full_name if alert.user else "",
        category=alert.category.value,
        title=alert.title,
        description=alert.description,
        priority_score=alert.priority_score,
        status=alert.status.value,
        risk_score_at_alert=alert.risk_score_at_alert,
        assigned_to=str(alert.assigned_to_user_id) if alert.assigned_to_user_id else None,
        created_at=alert.created_at.isoformat() if alert.created_at else "",
        resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
    )


async def _persist_scan_results(
    scan: FraudScanResult,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Optional[str]:
    """
    Save signals and risk profile to DB.  Create alert if needed.
    Returns the alert_id if one was created.
    """
    now = datetime.now(timezone.utc)
    alert_id: Optional[str] = None

    # 1. Persist individual signals
    for sig in scan.signals:
        db.add(FraudSignalModel(
            user_id=user_id,
            category=FraudCategory(sig.category),
            signal_code=sig.code,
            severity=SignalSeverity(sig.severity),
            score_delta=sig.score_delta,
            description=sig.description,
            context_json=json.dumps(sig.context) if sig.context else None,
            entity_type=sig.entity_type or None,
            entity_id=sig.entity_id or None,
            is_processed=True,
        ))

    # 2. Upsert risk profile
    rp_q = select(RiskProfile).where(RiskProfile.user_id == user_id)
    rp_result = await db.execute(rp_q)
    rp = rp_result.scalar_one_or_none()

    if not rp:
        rp = RiskProfile(user_id=user_id)
        db.add(rp)

    rp.composite_score = scan.composite_score
    rp.risk_level = RiskLevel(scan.risk_level)
    rp.fake_company_score = scan.category_scores.get("fake_company", 0.0)
    rp.suspicious_bidding_score = scan.category_scores.get("suspicious_bidding", 0.0)
    rp.unusual_pricing_score = scan.category_scores.get("unusual_pricing", 0.0)
    rp.repeated_cancellation_score = scan.category_scores.get("repeated_cancellation", 0.0)
    rp.payment_abuse_score = scan.category_scores.get("payment_abuse", 0.0)
    rp.total_signals = (rp.total_signals or 0) + len(scan.signals)
    rp.is_flagged = scan.alert_required
    rp.last_scan_at = now

    # Apply auto-actions to profile flags
    if scan.auto_action in ("restrict_bidding", "restrict_withdrawals"):
        rp.is_restricted = True
    elif scan.auto_action in ("freeze_wallet", "suspend_account", "ban_account"):
        rp.is_restricted = True
        if scan.auto_action == "ban_account":
            rp.is_banned = True

    # 3. Create alert if required
    if scan.alert_required:
        # Find the top category
        top_cat = max(scan.category_scores, key=scan.category_scores.get)  # type: ignore[arg-type]
        signal_ids = [str(uuid.uuid4()) for _ in scan.signals]  # Already persisted above

        alert = FraudAlert(
            user_id=user_id,
            category=FraudCategory(top_cat),
            title=f"Risk alert: {scan.risk_level.upper()} ({scan.composite_score:.0f}/100)",
            description=(
                f"Fraud scan detected {len(scan.signals)} signal(s) across "
                f"{sum(1 for v in scan.category_scores.values() if v > 0)} categories. "
                f"Top concern: {top_cat.replace('_', ' ')} "
                f"(score {scan.category_scores[top_cat]:.0f}/100)."
            ),
            priority_score=scan.composite_score,
            signal_ids_json=json.dumps(signal_ids),
            risk_score_at_alert=scan.composite_score,
        )
        db.add(alert)
        rp.total_alerts = (rp.total_alerts or 0) + 1

        await db.flush()
        alert_id = str(alert.id)

    await db.commit()
    return alert_id


# ───────────────────────────────────────────────────────────
#  POST /fraud/scan/{user_id}
# ───────────────────────────────────────────────────────────

@router.post(
    "/scan/{user_id}",
    response_model=FraudScanResponse,
    summary="Trigger a full fraud scan for a user",
)
async def scan_user(
    user_id: str,
    admin: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Runs all 5 fraud detectors against the user's full activity
    history and returns the risk assessment.  Persists signals,
    updates the risk profile, and creates an alert if warranted.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    snapshot = await _build_snapshot(uid, db)
    scan = run_fraud_scan(snapshot)

    # Persist results
    alert_id = await _persist_scan_results(scan, uid, db)

    return FraudScanResponse(
        user_id=scan.user_id,
        composite_score=scan.composite_score,
        risk_level=scan.risk_level,
        category_scores=scan.category_scores,
        signals=[
            FraudSignalResponse(
                code=s.code,
                category=s.category,
                severity=s.severity,
                score_delta=s.score_delta,
                description=s.description,
                entity_type=s.entity_type,
                entity_id=s.entity_id,
                context=s.context,
            )
            for s in scan.signals
        ],
        signal_count=len(scan.signals),
        alert_required=scan.alert_required,
        auto_action=scan.auto_action,
        alert_id=alert_id,
        scan_timestamp=scan.scan_timestamp,
    )


# ───────────────────────────────────────────────────────────
#  GET /fraud/risk/{user_id}
# ───────────────────────────────────────────────────────────

@router.get(
    "/risk/{user_id}",
    response_model=RiskProfileResponse,
    summary="Get a user's risk profile",
)
async def get_risk_profile(
    user_id: str,
    admin: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the stored risk profile for a user.  If no profile
    exists, returns a clean profile with zero scores.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    # Verify user exists
    user = await db.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rp_q = select(RiskProfile).where(RiskProfile.user_id == uid)
    rp_result = await db.execute(rp_q)
    rp = rp_result.scalar_one_or_none()

    if not rp:
        return RiskProfileResponse(
            user_id=user_id,
            composite_score=0.0,
            risk_level="low",
            category_scores=[
                CategoryScoreResponse(category=c, score=0.0, signal_count=0)
                for c in [
                    "fake_company", "suspicious_bidding", "unusual_pricing",
                    "repeated_cancellation", "payment_abuse",
                ]
            ],
            total_signals=0,
            total_alerts=0,
            total_enforcements=0,
            is_flagged=False,
            is_restricted=False,
            is_banned=False,
        )

    # Get signal counts per category
    sig_q = (
        select(FraudSignalModel.category, func.count())
        .where(FraudSignalModel.user_id == uid)
        .group_by(FraudSignalModel.category)
    )
    sig_result = await db.execute(sig_q)
    sig_counts = {row[0].value: row[1] for row in sig_result.all()}

    cat_scores = [
        CategoryScoreResponse(
            category="fake_company",
            score=rp.fake_company_score,
            signal_count=sig_counts.get("fake_company", 0),
        ),
        CategoryScoreResponse(
            category="suspicious_bidding",
            score=rp.suspicious_bidding_score,
            signal_count=sig_counts.get("suspicious_bidding", 0),
        ),
        CategoryScoreResponse(
            category="unusual_pricing",
            score=rp.unusual_pricing_score,
            signal_count=sig_counts.get("unusual_pricing", 0),
        ),
        CategoryScoreResponse(
            category="repeated_cancellation",
            score=rp.repeated_cancellation_score,
            signal_count=sig_counts.get("repeated_cancellation", 0),
        ),
        CategoryScoreResponse(
            category="payment_abuse",
            score=rp.payment_abuse_score,
            signal_count=sig_counts.get("payment_abuse", 0),
        ),
    ]

    return RiskProfileResponse(
        user_id=user_id,
        composite_score=rp.composite_score,
        risk_level=rp.risk_level.value,
        category_scores=cat_scores,
        total_signals=rp.total_signals,
        total_alerts=rp.total_alerts,
        total_enforcements=rp.total_enforcements,
        is_flagged=rp.is_flagged,
        is_restricted=rp.is_restricted,
        is_banned=rp.is_banned,
        last_scan_at=rp.last_scan_at.isoformat() if rp.last_scan_at else None,
    )


# ───────────────────────────────────────────────────────────
#  GET /fraud/alerts
# ───────────────────────────────────────────────────────────

@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="List fraud alerts (paginated)",
)
async def list_alerts(
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns paginated fraud alerts, sorted by priority descending."""
    query = select(FraudAlert)

    if status_filter:
        if status_filter in ALERT_STATUSES:
            query = query.where(FraudAlert.status == AlertStatus(status_filter))

    if category:
        query = query.where(FraudAlert.category == FraudCategory(category))

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch page
    query = (
        query
        .order_by(FraudAlert.priority_score.desc(), FraudAlert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertListResponse(
        alerts=[_build_alert_response(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
    )


# ───────────────────────────────────────────────────────────
#  GET /fraud/alerts/{alert_id}
# ───────────────────────────────────────────────────────────

@router.get(
    "/alerts/{alert_id}",
    response_model=FraudAlertResponse,
    summary="Get alert details",
)
async def get_alert(
    alert_id: str,
    admin: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        aid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert_id")

    alert = await db.get(FraudAlert, aid)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return _build_alert_response(alert)


# ───────────────────────────────────────────────────────────
#  POST /fraud/alerts/{alert_id}/resolve
# ───────────────────────────────────────────────────────────

@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=ResolveAlertResponse,
    summary="Admin: resolve a fraud alert",
)
async def resolve_alert(
    alert_id: str,
    body: ResolveAlertRequest,
    admin: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin reviews the alert and decides on an enforcement action.
    The decision is logged and the action is applied to the user
    (e.g. freeze wallet, restrict bidding, ban account).
    """
    try:
        aid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert_id")

    alert = await db.get(FraudAlert, aid)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status.value.startswith("resolved_"):
        raise HTTPException(status_code=409, detail="Alert is already resolved")

    # Validate action
    if body.action not in DECISION_ACTIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid action. Must be one of: {', '.join(DECISION_ACTIONS)}",
        )

    now = datetime.now(timezone.utc)
    expires_at = None
    if body.expires_in_days:
        expires_at = now + timedelta(days=body.expires_in_days)

    # Map action to alert resolution status
    action_to_status = {
        "clear": AlertStatus.RESOLVED_CLEAR,
        "warning": AlertStatus.RESOLVED_WARNING,
        "freeze_wallet": AlertStatus.RESOLVED_RESTRICT,
        "suspend_account": AlertStatus.RESOLVED_RESTRICT,
        "restrict_bidding": AlertStatus.RESOLVED_RESTRICT,
        "restrict_withdrawals": AlertStatus.RESOLVED_RESTRICT,
        "ban_account": AlertStatus.RESOLVED_BAN,
        "manual_review": AlertStatus.INVESTIGATING,
    }

    # Create decision record
    decision = FraudDecision(
        alert_id=aid,
        target_user_id=alert.user_id,
        decided_by_user_id=admin.id,
        action=DecisionAction(body.action),
        reason=body.reason,
        expires_at=expires_at,
        is_automated=False,
    )
    db.add(decision)

    # Update alert status
    alert.status = action_to_status.get(body.action, AlertStatus.RESOLVED_CLEAR)
    alert.resolved_at = now

    # Apply enforcement to risk profile
    rp_q = select(RiskProfile).where(RiskProfile.user_id == alert.user_id)
    rp_result = await db.execute(rp_q)
    rp = rp_result.scalar_one_or_none()
    if rp:
        rp.total_enforcements = (rp.total_enforcements or 0) + 1
        if body.action == "clear":
            rp.is_flagged = False
        elif body.action in ("restrict_bidding", "restrict_withdrawals", "freeze_wallet", "suspend_account"):
            rp.is_restricted = True
        elif body.action == "ban_account":
            rp.is_banned = True
            rp.is_restricted = True
            # Also deactivate the user account
            target_user = await db.get(User, alert.user_id)
            if target_user:
                target_user.is_active = False

    # For wallet freeze: update wallet status
    if body.action == "freeze_wallet":
        wallet_q = select(Wallet).where(Wallet.user_id == alert.user_id)
        wallet_result = await db.execute(wallet_q)
        wallet = wallet_result.scalar_one_or_none()
        if wallet:
            from app.models.wallet import WalletStatus
            wallet.status = WalletStatus.FROZEN

    await db.commit()
    await db.refresh(decision)

    return ResolveAlertResponse(
        alert_id=alert_id,
        decision_id=str(decision.id),
        action=body.action,
        target_user_id=str(alert.user_id),
        status=alert.status.value,
        message=f"Alert resolved with action: {body.action}",
    )


# ───────────────────────────────────────────────────────────
#  POST /fraud/alerts/{alert_id}/assign
# ───────────────────────────────────────────────────────────

@router.post(
    "/alerts/{alert_id}/assign",
    response_model=FraudAlertResponse,
    summary="Assign alert to an investigator",
)
async def assign_alert(
    alert_id: str,
    assignee_id: str = Query(..., description="User ID of the admin/agent to assign"),
    admin: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        aid = uuid.UUID(alert_id)
        assignee_uuid = uuid.UUID(assignee_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    alert = await db.get(FraudAlert, aid)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.assigned_to_user_id = assignee_uuid
    if alert.status == AlertStatus.OPEN:
        alert.status = AlertStatus.INVESTIGATING

    await db.commit()
    await db.refresh(alert)

    return _build_alert_response(alert)


# ───────────────────────────────────────────────────────────
#  GET /fraud/signals/{user_id}
# ───────────────────────────────────────────────────────────

@router.get(
    "/signals/{user_id}",
    response_model=list[FraudSignalResponse],
    summary="List raw fraud signals for a user",
)
async def list_user_signals(
    user_id: str,
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    query = (
        select(FraudSignalModel)
        .where(FraudSignalModel.user_id == uid)
        .order_by(FraudSignalModel.created_at.desc())
        .limit(limit)
    )
    if category:
        query = query.where(FraudSignalModel.category == FraudCategory(category))

    result = await db.execute(query)
    signals = result.scalars().all()

    return [
        FraudSignalResponse(
            code=s.signal_code,
            category=s.category.value,
            severity=s.severity.value,
            score_delta=s.score_delta,
            description=s.description,
            entity_type=s.entity_type or "",
            entity_id=s.entity_id or "",
            context=json.loads(s.context_json) if s.context_json else {},
        )
        for s in signals
    ]


# ───────────────────────────────────────────────────────────
#  GET /fraud/dashboard
# ───────────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    response_model=FraudDashboardResponse,
    summary="Admin fraud dashboard overview",
)
async def fraud_dashboard(
    admin: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregated fraud stats for the admin dashboard.
    """
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # ── Risk profile counts ──────────────────────────────────
    rp_q = select(
        RiskProfile.risk_level,
        func.count(),
    ).group_by(RiskProfile.risk_level)
    rp_result = await db.execute(rp_q)
    level_counts = {row[0].value: row[1] for row in rp_result.all()}

    total_scanned_q = select(func.count()).select_from(RiskProfile)
    total_scanned = (await db.execute(total_scanned_q)).scalar() or 0

    # ── Alert counts ─────────────────────────────────────────
    open_q = select(func.count()).where(FraudAlert.status == AlertStatus.OPEN)
    investigating_q = select(func.count()).where(FraudAlert.status == AlertStatus.INVESTIGATING)
    escalated_q = select(func.count()).where(FraudAlert.status == AlertStatus.ESCALATED)

    total_open = (await db.execute(open_q)).scalar() or 0
    total_investigating = (await db.execute(investigating_q)).scalar() or 0
    total_escalated = (await db.execute(escalated_q)).scalar() or 0

    # ── Per-category stats ───────────────────────────────────
    category_stats: list[CategoryDashboardStat] = []
    for cat_val in ["fake_company", "suspicious_bidding", "unusual_pricing",
                     "repeated_cancellation", "payment_abuse"]:
        cat_enum = FraudCategory(cat_val)

        open_cat_q = select(func.count()).where(
            and_(FraudAlert.category == cat_enum, FraudAlert.status == AlertStatus.OPEN)
        )
        open_cat = (await db.execute(open_cat_q)).scalar() or 0

        resolved_cat_q = select(func.count()).where(
            and_(
                FraudAlert.category == cat_enum,
                FraudAlert.resolved_at >= week_ago,
            )
        )
        resolved_cat = (await db.execute(resolved_cat_q)).scalar() or 0

        # Average risk for this category
        score_col = {
            "fake_company": RiskProfile.fake_company_score,
            "suspicious_bidding": RiskProfile.suspicious_bidding_score,
            "unusual_pricing": RiskProfile.unusual_pricing_score,
            "repeated_cancellation": RiskProfile.repeated_cancellation_score,
            "payment_abuse": RiskProfile.payment_abuse_score,
        }[cat_val]
        avg_q = select(func.avg(score_col))
        avg_score = (await db.execute(avg_q)).scalar() or 0.0

        high_q = select(func.count()).where(score_col >= 50.0)
        high_count = (await db.execute(high_q)).scalar() or 0

        category_stats.append(CategoryDashboardStat(
            category=cat_val,
            open_alerts=open_cat,
            resolved_alerts_7d=resolved_cat,
            avg_risk_score=round(float(avg_score), 2),
            high_risk_users=high_count,
        ))

    # ── Recent alerts (top 10) ───────────────────────────────
    recent_q = (
        select(FraudAlert)
        .order_by(FraudAlert.created_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_q)
    recent_alerts = [_build_alert_response(a) for a in recent_result.scalars().all()]

    # ── Enforcement count (7d) ───────────────────────────────
    enforce_q = select(func.count()).where(FraudDecision.created_at >= week_ago)
    enforce_count = (await db.execute(enforce_q)).scalar() or 0

    return FraudDashboardResponse(
        total_users_scanned=total_scanned,
        total_open_alerts=total_open,
        total_investigating=total_investigating,
        total_escalated=total_escalated,
        critical_risk_users=level_counts.get("critical", 0),
        high_risk_users=level_counts.get("high", 0),
        medium_risk_users=level_counts.get("medium", 0),
        low_risk_users=level_counts.get("low", 0),
        category_stats=category_stats,
        recent_alerts=recent_alerts,
        enforcement_actions_7d=enforce_count,
    )
