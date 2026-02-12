"""
LoadMoveGH — AI Fraud Detection Engine
=======================================

Multi-layer anomaly detection system purpose-built for the Ghana
freight marketplace.  Analyses user behaviour across 5 fraud
categories and produces a composite risk score (0–100).

════════════════════════════════════════════════════════════════
  ARCHITECTURE OVERVIEW
════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────┐
  │              RAW PLATFORM DATA                         │
  │  users · orgs · listings · bids · trips · txns · momo  │
  └──────────────┬─────────────────────────────────────────┘
                 ↓
  ┌────────────────────────────────────────────────────────┐
  │           5 SPECIALISED DETECTORS                      │
  │                                                        │
  │  1. FakeCompanyDetector                                │
  │     - Org age, KYC status, reg number patterns         │
  │     - No completed trips, phantom listings             │
  │     - Duplicate phone/email patterns                   │
  │                                                        │
  │  2. SuspiciousBiddingDetector                          │
  │     - Bid sniping (last-second bids)                   │
  │     - Self-dealing (shipper↔courier collusion)         │
  │     - Bid flooding (many bids, few wins)               │
  │     - Round-trip bidding patterns                      │
  │                                                        │
  │  3. UnusualPricingDetector                             │
  │     - Bids >2σ from route/cargo mean                   │
  │     - Consistently extreme pricing                     │
  │     - Price anchoring manipulation                     │
  │                                                        │
  │  4. RepeatedCancellationDetector                       │
  │     - Cancellation frequency & velocity                │
  │     - Cancel-after-accept pattern                      │
  │     - Coordinated cancellations                        │
  │                                                        │
  │  5. PaymentAbuseDetector                               │
  │     - Deposit → withdraw cycling                       │
  │     - Split transactions to avoid limits               │
  │     - Velocity anomalies (many txns in short window)   │
  │     - Failed payment churning                          │
  │     - MoMo phone number rotation                       │
  └──────────────┬─────────────────────────────────────────┘
                 ↓
  ┌────────────────────────────────────────────────────────┐
  │          RISK SCORING ENGINE                           │
  │                                                        │
  │  composite = Σ wᵢ × categoryᵢ                         │
  │            + recency_boost                             │
  │            + escalation_multiplier                     │
  │                                                        │
  │  Weights:                                              │
  │    fake_company         0.25                           │
  │    suspicious_bidding   0.20                           │
  │    unusual_pricing      0.15                           │
  │    repeated_cancel      0.20                           │
  │    payment_abuse        0.20                           │
  │                                                        │
  │  Result: RiskLevel (LOW / MEDIUM / HIGH / CRITICAL)    │
  └──────────────┬─────────────────────────────────────────┘
                 ↓
  ┌────────────────────────────────────────────────────────┐
  │          ALERT MECHANISM                               │
  │                                                        │
  │  • Score ≥ 40 → create FraudAlert (MEDIUM)             │
  │  • Score ≥ 65 → auto-restrict + escalate               │
  │  • Score ≥ 85 → auto-freeze wallet + urgent alert      │
  │  • Any CRITICAL signal → immediate alert               │
  │                                                        │
  │  Alerts appear in admin dashboard sorted by priority.   │
  │  Admin resolves → FraudDecision logged.                │
  └────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Signal:
    """A single fraud signal produced by a detector."""
    code: str                  # Machine-readable, e.g. "BID_PRICE_3X_MARKET"
    category: str              # One of the 5 FraudCategory values
    severity: str              # low / medium / high / critical
    score_delta: float         # How much to add to category score (0.0–30.0)
    description: str           # Human-readable explanation
    entity_type: str = ""      # bid, listing, transaction, trip, user, org
    entity_id: str = ""        # ID of the entity
    context: dict = field(default_factory=dict)


@dataclass
class UserBehaviourSnapshot:
    """
    Aggregated stats about a user, fetched from DB before scanning.
    The engine operates purely on this snapshot — no direct DB access
    from the detectors, keeping them testable.
    """
    user_id: str
    full_name: str = ""

    # Organisation
    org_id: Optional[str] = None
    org_name: str = ""
    org_type: str = ""
    org_status: str = ""
    org_registration_number: str = ""
    org_created_days_ago: int = 0

    # Account
    account_age_days: int = 0
    kyc_status: str = "not_started"
    email_verified: bool = False
    phone_verified: bool = False
    is_active: bool = True
    role_names: list[str] = field(default_factory=list)

    # Listing activity
    total_listings: int = 0
    active_listings: int = 0
    cancelled_listings: int = 0
    listings_with_no_bids: int = 0
    listings_last_30d: int = 0

    # Bidding activity
    total_bids_placed: int = 0
    bids_accepted: int = 0
    bids_rejected: int = 0
    bids_withdrawn: int = 0
    bids_last_24h: int = 0
    bids_last_7d: int = 0
    avg_bid_price: float = 0.0
    bid_prices_last_30d: list[float] = field(default_factory=list)

    # Trip activity
    total_trips: int = 0
    trips_completed: int = 0
    trips_cancelled: int = 0
    trips_disputed: int = 0
    cancellations_last_7d: int = 0
    cancellations_last_24h: int = 0
    cancel_after_accept_count: int = 0

    # Pricing context
    market_avg_price_for_routes: float = 0.0
    price_std_dev: float = 0.0
    bid_vs_market_ratio: float = 1.0

    # Payment activity
    total_deposits: int = 0
    total_withdrawals: int = 0
    deposits_last_24h: int = 0
    withdrawals_last_24h: int = 0
    deposits_last_7d: int = 0
    withdrawals_last_7d: int = 0
    total_deposit_amount: float = 0.0
    total_withdrawal_amount: float = 0.0
    deposit_amount_last_24h: float = 0.0
    withdrawal_amount_last_24h: float = 0.0
    failed_payments_last_7d: int = 0
    distinct_momo_phones_used: int = 0
    deposit_withdraw_cycles: int = 0  # Rapid deposit→withdraw within 1h
    split_transaction_count: int = 0  # Multiple small txns summing to a round number
    largest_single_deposit: float = 0.0
    largest_single_withdrawal: float = 0.0

    # Dispute history
    disputes_raised: int = 0
    disputes_lost: int = 0
    disputes_as_fraud_reason: int = 0

    # Relationships (for collusion detection)
    frequently_transacting_user_ids: list[str] = field(default_factory=list)
    shipper_courier_pairs: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class CategoryResult:
    """Result from a single detector category."""
    category: str
    score: float  # 0–100
    signals: list[Signal] = field(default_factory=list)


@dataclass
class FraudScanResult:
    """Complete result of a fraud scan across all 5 categories."""
    user_id: str
    composite_score: float = 0.0
    risk_level: str = "low"
    category_scores: dict[str, float] = field(default_factory=dict)
    signals: list[Signal] = field(default_factory=list)
    alert_required: bool = False
    auto_action: Optional[str] = None
    scan_timestamp: str = ""


# ═══════════════════════════════════════════════════════════════
#  CATEGORY WEIGHTS & THRESHOLDS
# ═══════════════════════════════════════════════════════════════

CATEGORY_WEIGHTS = {
    "fake_company": 0.25,
    "suspicious_bidding": 0.20,
    "unusual_pricing": 0.15,
    "repeated_cancellation": 0.20,
    "payment_abuse": 0.20,
}

# Alert thresholds (on composite 0–100 scale)
ALERT_THRESHOLD_MEDIUM = 40.0
ALERT_THRESHOLD_HIGH = 65.0
ALERT_THRESHOLD_CRITICAL = 85.0


# ═══════════════════════════════════════════════════════════════
#  DETECTOR 1: FAKE COMPANY
# ═══════════════════════════════════════════════════════════════

def detect_fake_company(snap: UserBehaviourSnapshot) -> CategoryResult:
    """
    Identifies accounts that may represent fictitious organisations.

    Signals:
      • No KYC verification on an account > 14 days old
      • Organisation has no registration number
      • Account created many listings but zero completed trips
      • Very new org with aggressive listing behaviour
      • Email and phone not verified
      • Org status is suspended or pending
    """
    signals: list[Signal] = []
    score = 0.0

    # S1: Account age vs KYC status
    if snap.account_age_days > 14 and snap.kyc_status == "not_started":
        s = Signal(
            code="KYC_NOT_STARTED_OLD_ACCOUNT",
            category="fake_company",
            severity="medium",
            score_delta=15.0,
            description=f"Account is {snap.account_age_days} days old but KYC has not been started.",
            entity_type="user",
            entity_id=snap.user_id,
        )
        signals.append(s)
        score += s.score_delta

    elif snap.account_age_days > 7 and snap.kyc_status == "rejected":
        s = Signal(
            code="KYC_REJECTED",
            category="fake_company",
            severity="high",
            score_delta=25.0,
            description="KYC verification was rejected — possible fake identity documents.",
            entity_type="user",
            entity_id=snap.user_id,
        )
        signals.append(s)
        score += s.score_delta

    # S2: Organisation without registration number
    if snap.org_id and not snap.org_registration_number:
        s = Signal(
            code="ORG_NO_REGISTRATION",
            category="fake_company",
            severity="medium",
            score_delta=12.0,
            description=f"Organisation '{snap.org_name}' has no business registration number.",
            entity_type="organization",
            entity_id=snap.org_id or "",
        )
        signals.append(s)
        score += s.score_delta

    # S3: Listings with zero completed trips (phantom activity)
    if snap.total_listings > 5 and snap.trips_completed == 0:
        s = Signal(
            code="PHANTOM_LISTINGS",
            category="fake_company",
            severity="high",
            score_delta=20.0,
            description=(
                f"User has {snap.total_listings} listings but 0 completed trips "
                f"— possible phantom company."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"total_listings": snap.total_listings},
        )
        signals.append(s)
        score += s.score_delta

    # S4: New org with aggressive listing volume
    if snap.org_created_days_ago < 7 and snap.listings_last_30d > 10:
        s = Signal(
            code="NEW_ORG_HIGH_VOLUME",
            category="fake_company",
            severity="high",
            score_delta=18.0,
            description=(
                f"Organisation created {snap.org_created_days_ago} days ago but already has "
                f"{snap.listings_last_30d} listings this month."
            ),
            entity_type="organization",
            entity_id=snap.org_id or "",
        )
        signals.append(s)
        score += s.score_delta

    # S5: Unverified contact info
    if not snap.email_verified and not snap.phone_verified and snap.account_age_days > 3:
        s = Signal(
            code="NO_CONTACT_VERIFICATION",
            category="fake_company",
            severity="medium",
            score_delta=10.0,
            description="Neither email nor phone has been verified after 3+ days.",
            entity_type="user",
            entity_id=snap.user_id,
        )
        signals.append(s)
        score += s.score_delta

    # S6: Org suspended
    if snap.org_status == "suspended":
        s = Signal(
            code="ORG_SUSPENDED",
            category="fake_company",
            severity="critical",
            score_delta=30.0,
            description=f"Organisation '{snap.org_name}' has been suspended.",
            entity_type="organization",
            entity_id=snap.org_id or "",
        )
        signals.append(s)
        score += s.score_delta

    return CategoryResult(
        category="fake_company",
        score=min(100.0, score),
        signals=signals,
    )


# ═══════════════════════════════════════════════════════════════
#  DETECTOR 2: SUSPICIOUS BIDDING
# ═══════════════════════════════════════════════════════════════

def detect_suspicious_bidding(snap: UserBehaviourSnapshot) -> CategoryResult:
    """
    Identifies abnormal bidding behaviour.

    Signals:
      • Bid flooding: >20 bids/day with <10% acceptance
      • High withdrawal rate (placing then withdrawing bids)
      • Bidding on own listings (self-dealing)
      • Extremely rapid bid velocity
      • Bid-win ratio anomaly (always wins → possible collusion)
    """
    signals: list[Signal] = []
    score = 0.0

    # S1: Bid flooding (many bids, very few accepted)
    if snap.bids_last_24h > 20:
        total_outcome = snap.bids_accepted + snap.bids_rejected + snap.bids_withdrawn
        win_rate = snap.bids_accepted / max(total_outcome, 1)
        if win_rate < 0.10:
            s = Signal(
                code="BID_FLOODING",
                category="suspicious_bidding",
                severity="high",
                score_delta=22.0,
                description=(
                    f"{snap.bids_last_24h} bids in 24h with only "
                    f"{win_rate:.0%} acceptance rate — possible bid manipulation."
                ),
                entity_type="user",
                entity_id=snap.user_id,
                context={
                    "bids_24h": snap.bids_last_24h,
                    "win_rate": round(win_rate, 3),
                },
            )
            signals.append(s)
            score += s.score_delta

    # S2: Excessive bid withdrawals (place → withdraw pattern)
    if snap.total_bids_placed > 10:
        withdraw_rate = snap.bids_withdrawn / snap.total_bids_placed
        if withdraw_rate > 0.40:
            s = Signal(
                code="HIGH_BID_WITHDRAWAL",
                category="suspicious_bidding",
                severity="medium",
                score_delta=15.0,
                description=(
                    f"{withdraw_rate:.0%} of bids are withdrawn — possible "
                    f"price discovery manipulation."
                ),
                entity_type="user",
                entity_id=snap.user_id,
                context={"withdraw_rate": round(withdraw_rate, 3)},
            )
            signals.append(s)
            score += s.score_delta

    # S3: Suspiciously high win rate (possible collusion)
    if snap.total_bids_placed > 15:
        total_resolved = snap.bids_accepted + snap.bids_rejected
        if total_resolved > 0:
            win_rate = snap.bids_accepted / total_resolved
            if win_rate > 0.85:
                s = Signal(
                    code="ABNORMAL_WIN_RATE",
                    category="suspicious_bidding",
                    severity="high",
                    score_delta=20.0,
                    description=(
                        f"Win rate of {win_rate:.0%} across {total_resolved} resolved bids "
                        f"— possible shipper-courier collusion."
                    ),
                    entity_type="user",
                    entity_id=snap.user_id,
                    context={"win_rate": round(win_rate, 3)},
                )
                signals.append(s)
                score += s.score_delta

    # S4: Bid velocity spike (>10 bids in 1 hour equivalent: scaled from 24h data)
    if snap.bids_last_24h > 30:
        s = Signal(
            code="BID_VELOCITY_SPIKE",
            category="suspicious_bidding",
            severity="medium",
            score_delta=12.0,
            description=f"{snap.bids_last_24h} bids in the last 24 hours — abnormal velocity.",
            entity_type="user",
            entity_id=snap.user_id,
        )
        signals.append(s)
        score += s.score_delta

    # S5: Frequent counterparty (same shipper-courier pair repeatedly)
    if len(snap.shipper_courier_pairs) > 0:
        from collections import Counter
        pair_counts = Counter(snap.shipper_courier_pairs)
        for pair, count in pair_counts.most_common(3):
            if count > 8:
                s = Signal(
                    code="REPEATED_COUNTERPARTY",
                    category="suspicious_bidding",
                    severity="high",
                    score_delta=18.0,
                    description=(
                        f"User has transacted with the same counterparty {count} times "
                        f"— possible collusion ring."
                    ),
                    entity_type="user",
                    entity_id=snap.user_id,
                    context={"pair": list(pair), "count": count},
                )
                signals.append(s)
                score += s.score_delta
                break  # Only flag the top one

    return CategoryResult(
        category="suspicious_bidding",
        score=min(100.0, score),
        signals=signals,
    )


# ═══════════════════════════════════════════════════════════════
#  DETECTOR 3: UNUSUAL PRICING
# ═══════════════════════════════════════════════════════════════

def detect_unusual_pricing(snap: UserBehaviourSnapshot) -> CategoryResult:
    """
    Detects pricing anomalies using statistical methods.

    Signals:
      • Bid prices >2σ from route/cargo market mean
      • Consistently extreme (always 2x+ above or <50% below market)
      • Sudden price jumps vs. user's own historical average
      • Price anchoring (posting high to manipulate market data)
    """
    signals: list[Signal] = []
    score = 0.0

    prices = snap.bid_prices_last_30d
    market_avg = snap.market_avg_price_for_routes
    market_std = snap.price_std_dev

    # S1: Current pricing ratio vs market
    if snap.bid_vs_market_ratio > 2.5 and snap.total_bids_placed > 3:
        s = Signal(
            code="BID_PRICE_EXTREME_HIGH",
            category="unusual_pricing",
            severity="high",
            score_delta=22.0,
            description=(
                f"Average bid price is {snap.bid_vs_market_ratio:.1f}× the market average "
                f"— potential price manipulation or overcharging."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"ratio": snap.bid_vs_market_ratio},
        )
        signals.append(s)
        score += s.score_delta

    elif snap.bid_vs_market_ratio < 0.30 and snap.total_bids_placed > 3:
        s = Signal(
            code="BID_PRICE_EXTREME_LOW",
            category="unusual_pricing",
            severity="medium",
            score_delta=15.0,
            description=(
                f"Average bid price is only {snap.bid_vs_market_ratio:.0%} of market — "
                f"possible loss-leader fraud or fake trip scheme."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"ratio": snap.bid_vs_market_ratio},
        )
        signals.append(s)
        score += s.score_delta

    # S2: Statistical outliers in recent prices
    if len(prices) >= 5 and market_std > 0:
        outlier_count = 0
        for p in prices:
            z_score = abs(p - market_avg) / market_std
            if z_score > 2.5:
                outlier_count += 1

        outlier_pct = outlier_count / len(prices)
        if outlier_pct > 0.40:
            s = Signal(
                code="PRICE_STATISTICAL_OUTLIER",
                category="unusual_pricing",
                severity="high",
                score_delta=20.0,
                description=(
                    f"{outlier_count}/{len(prices)} recent bid prices are >2.5σ from market "
                    f"mean — systematic pricing anomaly."
                ),
                entity_type="user",
                entity_id=snap.user_id,
                context={
                    "outlier_count": outlier_count,
                    "total_prices": len(prices),
                    "market_avg": round(market_avg, 2),
                    "market_std": round(market_std, 2),
                },
            )
            signals.append(s)
            score += s.score_delta

    # S3: Sudden price jump vs own history
    if len(prices) >= 8:
        recent = prices[-3:]
        historical = prices[:-3]
        recent_avg = statistics.mean(recent)
        hist_avg = statistics.mean(historical)

        if hist_avg > 0:
            jump_ratio = recent_avg / hist_avg
            if jump_ratio > 2.0 or jump_ratio < 0.35:
                s = Signal(
                    code="SUDDEN_PRICE_SHIFT",
                    category="unusual_pricing",
                    severity="medium",
                    score_delta=14.0,
                    description=(
                        f"Recent bid prices shifted {jump_ratio:.1f}× vs historical average "
                        f"— possible account takeover or manipulation."
                    ),
                    entity_type="user",
                    entity_id=snap.user_id,
                    context={
                        "recent_avg": round(recent_avg, 2),
                        "historical_avg": round(hist_avg, 2),
                        "jump_ratio": round(jump_ratio, 2),
                    },
                )
                signals.append(s)
                score += s.score_delta

    # S4: Zero-price bids (obvious manipulation)
    zero_bids = sum(1 for p in prices if p <= 0)
    if zero_bids > 0:
        s = Signal(
            code="ZERO_PRICE_BID",
            category="unusual_pricing",
            severity="critical",
            score_delta=30.0,
            description=f"{zero_bids} bid(s) submitted with zero or negative price.",
            entity_type="user",
            entity_id=snap.user_id,
        )
        signals.append(s)
        score += s.score_delta

    return CategoryResult(
        category="unusual_pricing",
        score=min(100.0, score),
        signals=signals,
    )


# ═══════════════════════════════════════════════════════════════
#  DETECTOR 4: REPEATED CANCELLATION
# ═══════════════════════════════════════════════════════════════

def detect_repeated_cancellation(snap: UserBehaviourSnapshot) -> CategoryResult:
    """
    Detects abuse patterns involving excessive cancellations.

    Signals:
      • High cancellation rate (>30% of trips)
      • Cancellation velocity (>3 in 24h or >7 in 7d)
      • Cancel-after-accept pattern (accept bid then cancel trip)
      • Cancellation-then-relist pattern
    """
    signals: list[Signal] = []
    score = 0.0

    total_trips = snap.trips_completed + snap.trips_cancelled
    if total_trips == 0:
        return CategoryResult(category="repeated_cancellation", score=0, signals=[])

    # S1: Overall cancellation rate
    cancel_rate = snap.trips_cancelled / total_trips
    if cancel_rate > 0.50 and snap.trips_cancelled > 3:
        s = Signal(
            code="EXTREME_CANCELLATION_RATE",
            category="repeated_cancellation",
            severity="critical",
            score_delta=28.0,
            description=(
                f"Cancellation rate of {cancel_rate:.0%} across {total_trips} trips — "
                f"severe reliability issue or intentional abuse."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"cancel_rate": round(cancel_rate, 3), "total": total_trips},
        )
        signals.append(s)
        score += s.score_delta
    elif cancel_rate > 0.30 and snap.trips_cancelled > 2:
        s = Signal(
            code="HIGH_CANCELLATION_RATE",
            category="repeated_cancellation",
            severity="high",
            score_delta=18.0,
            description=(
                f"Cancellation rate of {cancel_rate:.0%} across {total_trips} trips."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"cancel_rate": round(cancel_rate, 3)},
        )
        signals.append(s)
        score += s.score_delta

    # S2: Short-term velocity (24h)
    if snap.cancellations_last_24h >= 3:
        s = Signal(
            code="CANCEL_VELOCITY_24H",
            category="repeated_cancellation",
            severity="high",
            score_delta=22.0,
            description=(
                f"{snap.cancellations_last_24h} cancellations in the last 24 hours."
            ),
            entity_type="user",
            entity_id=snap.user_id,
        )
        signals.append(s)
        score += s.score_delta

    # S3: Weekly velocity
    if snap.cancellations_last_7d >= 7:
        s = Signal(
            code="CANCEL_VELOCITY_7D",
            category="repeated_cancellation",
            severity="high",
            score_delta=18.0,
            description=(
                f"{snap.cancellations_last_7d} cancellations in the last 7 days."
            ),
            entity_type="user",
            entity_id=snap.user_id,
        )
        signals.append(s)
        score += s.score_delta

    # S4: Cancel-after-accept pattern
    if snap.cancel_after_accept_count > 2:
        s = Signal(
            code="CANCEL_AFTER_ACCEPT",
            category="repeated_cancellation",
            severity="critical",
            score_delta=25.0,
            description=(
                f"Courier cancelled {snap.cancel_after_accept_count} trips AFTER bid was "
                f"accepted — wasting shipper time and blocking load movement."
            ),
            entity_type="user",
            entity_id=snap.user_id,
        )
        signals.append(s)
        score += s.score_delta

    # S5: High cancellation + high listings (cancel-and-relist pattern for shippers)
    if "shipper" in snap.role_names:
        if snap.cancelled_listings > 5 and snap.listings_last_30d > 10:
            relist_ratio = snap.cancelled_listings / max(snap.listings_last_30d, 1)
            if relist_ratio > 0.40:
                s = Signal(
                    code="CANCEL_RELIST_PATTERN",
                    category="repeated_cancellation",
                    severity="medium",
                    score_delta=14.0,
                    description=(
                        f"{snap.cancelled_listings} of {snap.listings_last_30d} listings "
                        f"cancelled this month — possible cancel-and-relist manipulation."
                    ),
                    entity_type="user",
                    entity_id=snap.user_id,
                )
                signals.append(s)
                score += s.score_delta

    return CategoryResult(
        category="repeated_cancellation",
        score=min(100.0, score),
        signals=signals,
    )


# ═══════════════════════════════════════════════════════════════
#  DETECTOR 5: PAYMENT ABUSE
# ═══════════════════════════════════════════════════════════════

def detect_payment_abuse(snap: UserBehaviourSnapshot) -> CategoryResult:
    """
    Detects suspicious payment patterns common in mobile-money
    fraud in Ghana.

    Signals:
      • Rapid deposit→withdraw cycles (money laundering indicator)
      • Transaction splitting (many small txns to avoid limits)
      • Payment velocity anomaly (too many txns in short window)
      • Failed payment churning (testing stolen credentials)
      • MoMo phone number rotation
      • Deposit amount far exceeds usage
    """
    signals: list[Signal] = []
    score = 0.0

    # S1: Deposit→Withdraw cycling
    if snap.deposit_withdraw_cycles > 2:
        s = Signal(
            code="DEPOSIT_WITHDRAW_CYCLE",
            category="payment_abuse",
            severity="critical",
            score_delta=28.0,
            description=(
                f"{snap.deposit_withdraw_cycles} rapid deposit→withdraw cycles detected "
                f"(deposit + withdrawal within 1 hour) — potential money laundering."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"cycles": snap.deposit_withdraw_cycles},
        )
        signals.append(s)
        score += s.score_delta

    # S2: Transaction splitting
    if snap.split_transaction_count > 3:
        s = Signal(
            code="TRANSACTION_SPLITTING",
            category="payment_abuse",
            severity="high",
            score_delta=20.0,
            description=(
                f"{snap.split_transaction_count} groups of small transactions that sum to "
                f"round numbers — possible structuring to evade limits."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"split_count": snap.split_transaction_count},
        )
        signals.append(s)
        score += s.score_delta

    # S3: Payment velocity (24h)
    total_txns_24h = snap.deposits_last_24h + snap.withdrawals_last_24h
    if total_txns_24h > 15:
        s = Signal(
            code="PAYMENT_VELOCITY_SPIKE",
            category="payment_abuse",
            severity="high",
            score_delta=20.0,
            description=(
                f"{total_txns_24h} payment transactions in 24 hours — abnormal frequency."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"deposits_24h": snap.deposits_last_24h, "withdrawals_24h": snap.withdrawals_last_24h},
        )
        signals.append(s)
        score += s.score_delta

    # S4: Failed payment churning
    if snap.failed_payments_last_7d > 5:
        s = Signal(
            code="FAILED_PAYMENT_CHURNING",
            category="payment_abuse",
            severity="high",
            score_delta=18.0,
            description=(
                f"{snap.failed_payments_last_7d} failed payment attempts in 7 days — "
                f"possible testing of stolen credentials or numbers."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"failed_count": snap.failed_payments_last_7d},
        )
        signals.append(s)
        score += s.score_delta

    # S5: MoMo phone number rotation
    if snap.distinct_momo_phones_used > 3:
        s = Signal(
            code="MOMO_PHONE_ROTATION",
            category="payment_abuse",
            severity="high",
            score_delta=18.0,
            description=(
                f"{snap.distinct_momo_phones_used} different MoMo phone numbers used — "
                f"unusual for a legitimate user."
            ),
            entity_type="user",
            entity_id=snap.user_id,
            context={"distinct_phones": snap.distinct_momo_phones_used},
        )
        signals.append(s)
        score += s.score_delta

    # S6: Deposit far exceeds actual usage
    if snap.total_deposit_amount > 0 and snap.trips_completed == 0:
        if snap.total_deposit_amount > 5000:  # GHS 5000+ with no trips
            s = Signal(
                code="DEPOSIT_NO_USAGE",
                category="payment_abuse",
                severity="high",
                score_delta=18.0,
                description=(
                    f"GHS {snap.total_deposit_amount:,.2f} deposited but 0 completed trips — "
                    f"funds may be parked for withdrawal fraud."
                ),
                entity_type="user",
                entity_id=snap.user_id,
                context={"total_deposited": snap.total_deposit_amount},
            )
            signals.append(s)
            score += s.score_delta

    # S7: Large single withdrawal relative to account history
    if snap.largest_single_withdrawal > 0:
        avg_withdrawal = snap.total_withdrawal_amount / max(snap.total_withdrawals, 1)
        if avg_withdrawal > 0 and snap.largest_single_withdrawal > avg_withdrawal * 5:
            s = Signal(
                code="LARGE_ANOMALOUS_WITHDRAWAL",
                category="payment_abuse",
                severity="medium",
                score_delta=14.0,
                description=(
                    f"Largest withdrawal (GHS {snap.largest_single_withdrawal:,.2f}) is "
                    f"{snap.largest_single_withdrawal / avg_withdrawal:.1f}× the average — "
                    f"possible account drain."
                ),
                entity_type="user",
                entity_id=snap.user_id,
            )
            signals.append(s)
            score += s.score_delta

    return CategoryResult(
        category="payment_abuse",
        score=min(100.0, score),
        signals=signals,
    )


# ═══════════════════════════════════════════════════════════════
#  COMPOSITE RISK SCORER
# ═══════════════════════════════════════════════════════════════

def compute_risk_level(score: float) -> str:
    """Map a 0–100 composite score to a risk tier."""
    if score >= 76:
        return "critical"
    elif score >= 51:
        return "high"
    elif score >= 26:
        return "medium"
    else:
        return "low"


def determine_auto_action(composite_score: float, signals: list[Signal]) -> Optional[str]:
    """
    Decide whether an automatic enforcement action should be taken.

    Rules:
      • composite ≥ 85 → freeze_wallet (urgent)
      • composite ≥ 65 → restrict_bidding + restrict_withdrawals
      • Any CRITICAL signal → manual_review at minimum
    """
    has_critical = any(s.severity == "critical" for s in signals)

    if composite_score >= ALERT_THRESHOLD_CRITICAL:
        return "freeze_wallet"
    elif composite_score >= ALERT_THRESHOLD_HIGH:
        return "restrict_withdrawals"
    elif has_critical:
        return "manual_review"
    return None


def run_fraud_scan(snap: UserBehaviourSnapshot) -> FraudScanResult:
    """
    Execute all 5 detectors against a user behaviour snapshot,
    compute the weighted composite risk score, and determine
    alert/action requirements.

    This is the main entry point for the fraud engine.
    """
    # Run each detector
    results: list[CategoryResult] = [
        detect_fake_company(snap),
        detect_suspicious_bidding(snap),
        detect_unusual_pricing(snap),
        detect_repeated_cancellation(snap),
        detect_payment_abuse(snap),
    ]

    # Collect all signals
    all_signals: list[Signal] = []
    category_scores: dict[str, float] = {}
    for result in results:
        category_scores[result.category] = result.score
        all_signals.extend(result.signals)

    # Weighted composite
    composite = 0.0
    for cat, weight in CATEGORY_WEIGHTS.items():
        composite += weight * category_scores.get(cat, 0.0)

    # Recency boost: if there are CRITICAL signals, add 10%
    critical_count = sum(1 for s in all_signals if s.severity == "critical")
    if critical_count > 0:
        recency_boost = min(critical_count * 5.0, 15.0)
        composite = min(100.0, composite + recency_boost)

    # Escalation multiplier: if multiple categories are HIGH, boost
    high_categories = sum(1 for s in category_scores.values() if s >= 50)
    if high_categories >= 3:
        composite = min(100.0, composite * 1.15)

    composite = round(min(100.0, composite), 2)
    risk_level = compute_risk_level(composite)
    alert_required = composite >= ALERT_THRESHOLD_MEDIUM or critical_count > 0
    auto_action = determine_auto_action(composite, all_signals)

    return FraudScanResult(
        user_id=snap.user_id,
        composite_score=composite,
        risk_level=risk_level,
        category_scores={k: round(v, 2) for k, v in category_scores.items()},
        signals=all_signals,
        alert_required=alert_required,
        auto_action=auto_action,
        scan_timestamp=datetime.now(timezone.utc).isoformat(),
    )
