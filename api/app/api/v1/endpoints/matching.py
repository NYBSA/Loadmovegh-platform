"""
LoadMoveGH — API Endpoints: AI Load Matching
=============================================

POST /matching/recommend          — Get ranked courier recommendations for a listing
GET  /matching/score/{l}/{c}      — Score a single courier against a listing
POST /matching/location           — Update courier live GPS location
GET  /matching/profile/me         — Get own courier matching profile
GET  /matching/profile/{user_id}  — Admin: view any courier profile
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import (
    get_current_active_user,
    require_any_authenticated,
    require_courier,
    require_system_admin,
)
from app.core.database import get_db
from app.models.freight import Address, FreightListing
from app.models.matching import CourierProfile, MatchRecommendation
from app.models.user import User
from app.ml.matching import (
    CourierStats,
    ListingContext,
    ml_rerank,
    rank_couriers,
    score_courier,
    select_weights,
    MAX_PROXIMITY_RADIUS_KM,
)
from app.schemas.matching import (
    CourierProfileResponse,
    CourierScoreResponse,
    DimensionScoreResponse,
    LocationUpdateResponse,
    MatchedCourier,
    MatchRequest,
    MatchResponse,
    ScoreCourierRequest,
    UpdateLocationRequest,
)

router = APIRouter(prefix="/matching", tags=["Load Matching"])

ALGORITHM_VERSION = "v1.0-formula"


# ───────────────────────────────────────────────────────────
#  HELPERS
# ───────────────────────────────────────────────────────────

def _profile_to_stats(profile: CourierProfile) -> CourierStats:
    """Convert a DB CourierProfile to an in-memory CourierStats."""
    return CourierStats(
        user_id=str(profile.user_id),
        full_name=profile.user.full_name if profile.user else "Unknown",
        latitude=profile.current_latitude,
        longitude=profile.current_longitude,
        current_city=profile.current_city or "",
        current_region=profile.current_region or "",
        vehicle_type=profile.vehicle_type or "any",
        vehicle_capacity_kg=profile.vehicle_capacity_kg,
        has_refrigeration=profile.has_refrigeration,
        has_gps_tracker=profile.has_gps_tracker,
        acceptance_rate=profile.acceptance_rate,
        completion_rate=profile.completion_rate,
        on_time_rate=profile.on_time_rate,
        avg_rating=profile.avg_rating,
        total_ratings=profile.total_ratings,
        total_trips_completed=profile.total_trips_completed,
        total_trips_cancelled=profile.total_trips_cancelled,
        total_disputes=profile.total_disputes,
        disputes_lost=profile.disputes_lost,
        member_since_days=profile.member_since_days,
        avg_price_vs_market=float(profile.avg_price_vs_market),
    )


async def _build_listing_context(
    listing: FreightListing,
    db: AsyncSession,
) -> ListingContext:
    """Build a ListingContext from a DB FreightListing."""
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    pickup_city = ""
    delivery_city = ""

    if listing.pickup_address_id:
        addr = await db.get(Address, listing.pickup_address_id)
        if addr:
            pickup_lat = addr.latitude
            pickup_lng = addr.longitude
            pickup_city = addr.city or ""
    if listing.delivery_address_id:
        addr = await db.get(Address, listing.delivery_address_id)
        if addr:
            delivery_city = addr.city or ""

    return ListingContext(
        listing_id=str(listing.id),
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        pickup_city=pickup_city,
        delivery_city=delivery_city,
        weight_kg=listing.weight_kg or 0,
        cargo_type=listing.cargo_type or "general",
        required_vehicle_type=listing.vehicle_type or "any",
        urgency=listing.urgency or "standard",
        shipper_price=float(listing.shipper_price) if listing.shipper_price else None,
        ai_suggested_price=float(listing.ai_suggested_price) if listing.ai_suggested_price else None,
    )


def _build_profile_response(p: CourierProfile) -> CourierProfileResponse:
    return CourierProfileResponse(
        user_id=str(p.user_id),
        full_name=p.user.full_name if p.user else "Unknown",
        vehicle_type=p.vehicle_type,
        vehicle_capacity_kg=p.vehicle_capacity_kg,
        current_city=p.current_city,
        current_region=p.current_region,
        is_available=p.is_available,
        is_on_trip=p.is_on_trip,
        acceptance_rate=p.acceptance_rate,
        completion_rate=p.completion_rate,
        on_time_rate=p.on_time_rate,
        avg_rating=p.avg_rating,
        total_ratings=p.total_ratings,
        total_trips_completed=p.total_trips_completed,
        member_since_days=p.member_since_days,
        has_gps_tracker=p.has_gps_tracker,
    )


# ───────────────────────────────────────────────────────────
#  POST /matching/recommend
# ───────────────────────────────────────────────────────────

@router.post(
    "/recommend",
    response_model=MatchResponse,
    summary="Get ranked courier recommendations for a listing",
)
async def recommend_couriers(
    body: MatchRequest,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    """
    Main matching endpoint. Retrieves available couriers,
    scores them against the listing, and returns a ranked list.
    """
    # 1. Load listing
    try:
        listing_uuid = uuid.UUID(body.listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid listing_id")

    listing = await db.get(FreightListing, listing_uuid)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing_ctx = await _build_listing_context(listing, db)

    # 2. Fetch available courier profiles within max radius
    max_radius = min(body.max_radius_km, MAX_PROXIMITY_RADIUS_KM)
    query = select(CourierProfile).where(
        and_(
            CourierProfile.is_available.is_(True),
            CourierProfile.is_on_trip.is_(False),
        )
    )
    result = await db.execute(query)
    profiles = result.scalars().all()

    # 3. Convert to stats
    courier_stats = [_profile_to_stats(p) for p in profiles]

    # 4. Build weights
    weights = select_weights(listing_ctx)
    if body.weight_overrides:
        overrides = body.weight_overrides.model_dump(exclude_none=True)
        if overrides:
            weights.update(overrides)
            # Re-normalise so they sum to 1.0
            total = sum(weights.values())
            if total > 0:
                weights = {k: v / total for k, v in weights.items()}

    # 5. Rank
    matches = rank_couriers(
        courier_stats, listing_ctx,
        top_k=body.top_k,
        min_score=body.min_score,
        weights=weights,
    )

    # 6. Optional ML re-rank
    if body.use_ml_reranker:
        matches = ml_rerank(matches, listing_ctx)

    # 7. Build response
    matched_couriers = [
        MatchedCourier(
            courier_id=m.courier_id,
            courier_name=m.courier_name,
            rank=m.rank,
            composite_score=m.composite_score,
            dimensions=DimensionScoreResponse(
                proximity=m.dimensions.proximity,
                reliability=m.dimensions.reliability,
                acceptance=m.dimensions.acceptance,
                vehicle_fit=m.dimensions.vehicle_fit,
                pricing=m.dimensions.pricing,
            ),
            distance_km=m.distance_km,
            vehicle_type=m.vehicle_type,
        )
        for m in matches
    ]

    # 8. Log recommendation for audit / ML feedback
    rec = MatchRecommendation(
        listing_id=listing_uuid,
        algorithm_version=ALGORITHM_VERSION,
        ranked_results_json=json.dumps([m.to_dict() for m in matches]),
        total_candidates=len(courier_stats),
        returned_count=len(matched_couriers),
    )
    db.add(rec)
    await db.commit()

    return MatchResponse(
        listing_id=str(listing.id),
        algorithm_version=ALGORITHM_VERSION,
        total_candidates=len(courier_stats),
        returned_count=len(matched_couriers),
        weights_used={k: round(v, 4) for k, v in weights.items()},
        matches=matched_couriers,
    )


# ───────────────────────────────────────────────────────────
#  GET /matching/score/{listing_id}/{courier_id}
# ───────────────────────────────────────────────────────────

@router.get(
    "/score/{listing_id}/{courier_id}",
    response_model=CourierScoreResponse,
    summary="Score a single courier against a listing",
)
async def score_single_courier(
    listing_id: str,
    courier_id: str,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    """
    Detailed scoring breakdown for a specific courier–listing pair.
    Useful for debugging and understanding why a courier ranked where they did.
    """
    try:
        listing_uuid = uuid.UUID(listing_id)
        courier_uuid = uuid.UUID(courier_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    listing = await db.get(FreightListing, listing_uuid)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    result = await db.execute(
        select(CourierProfile).where(CourierProfile.user_id == courier_uuid)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Courier profile not found")

    listing_ctx = await _build_listing_context(listing, db)
    courier_st = _profile_to_stats(profile)
    weights = select_weights(listing_ctx)

    match = score_courier(courier_st, listing_ctx, weights)

    # Check disqualification reasons
    reasons: list[str] = []
    is_eligible = True
    if match.dimensions.vehicle_fit == 0:
        reasons.append("Incompatible vehicle type or insufficient capacity")
        is_eligible = False
    if not profile.is_available:
        reasons.append("Courier is not currently available")
        is_eligible = False
    if profile.is_on_trip:
        reasons.append("Courier is currently on another trip")
        is_eligible = False

    return CourierScoreResponse(
        listing_id=listing_id,
        courier_id=courier_id,
        courier_name=match.courier_name,
        composite_score=match.composite_score,
        dimensions=DimensionScoreResponse(
            proximity=match.dimensions.proximity,
            reliability=match.dimensions.reliability,
            acceptance=match.dimensions.acceptance,
            vehicle_fit=match.dimensions.vehicle_fit,
            pricing=match.dimensions.pricing,
        ),
        distance_km=match.distance_km,
        vehicle_type=match.vehicle_type,
        weights_used={k: round(v, 4) for k, v in weights.items()},
        is_eligible=is_eligible,
        disqualification_reasons=reasons,
    )


# ───────────────────────────────────────────────────────────
#  POST /matching/location
# ───────────────────────────────────────────────────────────

@router.post(
    "/location",
    response_model=LocationUpdateResponse,
    summary="Update courier live GPS location",
)
async def update_courier_location(
    body: UpdateLocationRequest,
    user: User = Depends(require_courier),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the driver app to push real-time GPS coordinates.
    Creates a courier profile if one doesn't exist yet.
    """
    result = await db.execute(
        select(CourierProfile).where(CourierProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if not profile:
        profile = CourierProfile(
            user_id=user.id,
            current_latitude=body.latitude,
            current_longitude=body.longitude,
            current_city=body.city,
            current_region=body.region,
            location_updated_at=now,
        )
        db.add(profile)
    else:
        profile.current_latitude = body.latitude
        profile.current_longitude = body.longitude
        profile.current_city = body.city or profile.current_city
        profile.current_region = body.region or profile.current_region
        profile.location_updated_at = now

    await db.commit()
    await db.refresh(profile)

    return LocationUpdateResponse(
        user_id=str(user.id),
        latitude=body.latitude,
        longitude=body.longitude,
        city=profile.current_city,
        region=profile.current_region,
        updated_at=now.isoformat(),
    )


# ───────────────────────────────────────────────────────────
#  GET /matching/profile/me
# ───────────────────────────────────────────────────────────

@router.get(
    "/profile/me",
    response_model=CourierProfileResponse,
    summary="Get own courier matching profile",
)
async def get_my_courier_profile(
    user: User = Depends(require_courier),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the authenticated courier's matching profile and stats."""
    result = await db.execute(
        select(CourierProfile).where(CourierProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Courier profile not found. Update your location to create one.",
        )

    return _build_profile_response(profile)


# ───────────────────────────────────────────────────────────
#  GET /matching/profile/{user_id}
# ───────────────────────────────────────────────────────────

@router.get(
    "/profile/{user_id}",
    response_model=CourierProfileResponse,
    summary="Admin: view any courier profile",
)
async def get_courier_profile(
    user_id: str,
    user: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint to inspect any courier's matching profile."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    result = await db.execute(
        select(CourierProfile).where(CourierProfile.user_id == uid)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Courier profile not found")

    return _build_profile_response(profile)
