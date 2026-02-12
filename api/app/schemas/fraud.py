"""
LoadMoveGH — Pydantic Schemas for Fraud Detection API
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
#  ENUMS / CONSTANTS (mirrored from models for validation)
# ═══════════════════════════════════════════════════════════════

FRAUD_CATEGORIES = [
    "fake_company", "suspicious_bidding", "unusual_pricing",
    "repeated_cancellation", "payment_abuse",
]

RISK_LEVELS = ["low", "medium", "high", "critical"]

ALERT_STATUSES = [
    "open", "investigating", "escalated",
    "resolved_clear", "resolved_warning", "resolved_restrict", "resolved_ban",
]

DECISION_ACTIONS = [
    "clear", "warning", "freeze_wallet", "suspend_account",
    "ban_account", "restrict_bidding", "restrict_withdrawals", "manual_review",
]


# ═══════════════════════════════════════════════════════════════
#  SIGNAL / SCORE RESPONSES
# ═══════════════════════════════════════════════════════════════

class FraudSignalResponse(BaseModel):
    """A single fraud signal."""
    code: str
    category: str
    severity: str
    score_delta: float
    description: str
    entity_type: str = ""
    entity_id: str = ""
    context: dict = Field(default_factory=dict)


class CategoryScoreResponse(BaseModel):
    """Score breakdown for one fraud category."""
    category: str
    score: float = Field(..., ge=0, le=100)
    signal_count: int = 0


class RiskProfileResponse(BaseModel):
    """A user's full risk profile."""
    user_id: str
    composite_score: float = Field(..., ge=0, le=100)
    risk_level: str
    category_scores: list[CategoryScoreResponse]
    total_signals: int
    total_alerts: int
    total_enforcements: int
    is_flagged: bool
    is_restricted: bool
    is_banned: bool
    last_scan_at: Optional[str] = None


class FraudScanResponse(BaseModel):
    """Result of a fraud scan for a user."""
    user_id: str
    composite_score: float
    risk_level: str
    category_scores: dict[str, float]
    signals: list[FraudSignalResponse]
    signal_count: int
    alert_required: bool
    auto_action: Optional[str] = None
    alert_id: Optional[str] = None
    scan_timestamp: str


# ═══════════════════════════════════════════════════════════════
#  ALERT MODELS
# ═══════════════════════════════════════════════════════════════

class FraudAlertResponse(BaseModel):
    """A fraud alert."""
    id: str
    user_id: str
    user_name: str = ""
    category: str
    title: str
    description: str
    priority_score: float
    status: str
    risk_score_at_alert: float
    assigned_to: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None


class AlertListResponse(BaseModel):
    """Paginated list of fraud alerts."""
    alerts: list[FraudAlertResponse]
    total: int
    page: int
    page_size: int


class ResolveAlertRequest(BaseModel):
    """Admin request to resolve a fraud alert."""
    action: str = Field(
        ...,
        description="Enforcement action to take",
    )
    reason: str = Field(
        ..., min_length=10, max_length=2000,
        description="Explanation for the decision",
    )
    expires_in_days: Optional[int] = Field(
        None, ge=1, le=365,
        description="For temporary restrictions: days until expiry (null = permanent)",
    )

    def validate_action(self) -> str:
        if self.action not in DECISION_ACTIONS:
            raise ValueError(f"action must be one of: {', '.join(DECISION_ACTIONS)}")
        return self.action


class ResolveAlertResponse(BaseModel):
    """Confirmation of alert resolution."""
    alert_id: str
    decision_id: str
    action: str
    target_user_id: str
    status: str
    message: str


# ═══════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════

class CategoryDashboardStat(BaseModel):
    """Stats for one fraud category."""
    category: str
    open_alerts: int
    resolved_alerts_7d: int
    avg_risk_score: float
    high_risk_users: int


class FraudDashboardResponse(BaseModel):
    """Admin fraud dashboard overview."""
    total_users_scanned: int
    total_open_alerts: int
    total_investigating: int
    total_escalated: int
    critical_risk_users: int
    high_risk_users: int
    medium_risk_users: int
    low_risk_users: int
    category_stats: list[CategoryDashboardStat]
    recent_alerts: list[FraudAlertResponse]
    enforcement_actions_7d: int
