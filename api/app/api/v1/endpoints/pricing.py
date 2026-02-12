"""
LoadMoveGH — AI Pricing Engine Endpoints
POST /pricing/estimate   — Get price recommendation for a load
GET  /pricing/breakdown   — Detailed breakdown for an existing listing
GET  /pricing/model-status — Current model info
POST /pricing/train       — Trigger model training (admin)
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import require_any_authenticated, require_system_admin
from app.core.database import get_db
from app.ml.features import extract_features, haversine_km
from app.ml.predictor import get_predictor
from app.models.freight import FreightBid, FreightListing, BidStatus
from app.models.pricing import AIPricingRun, PricingModelVersion, ModelStatus
from app.models.user import User
from app.schemas.pricing import (
    FeatureImportanceItem,
    MessageResponse,
    ModelStatusResponse,
    ModelVersionResponse,
    PriceBreakdownResponse,
    PriceEstimateRequest,
    PriceEstimateResponse,
    TrainModelRequest,
    TrainModelResponse,
)

router = APIRouter(prefix="/pricing", tags=["AI Pricing"])


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

async def _get_historical_prices(
    db: AsyncSession,
    cargo_type: str,
    pickup_city: str,
    delivery_city: str,
) -> tuple[Optional[float], int, Optional[float], int]:
    """
    Query historical accepted bid prices for:
    1. Same cargo type (across all routes)
    2. Same route corridor (city pair)
    Returns (cargo_avg, cargo_count, route_avg, route_count)
    """
    # Cargo type average
    cargo_result = await db.execute(
        select(
            func.avg(FreightBid.price),
            func.count(FreightBid.id),
        )
        .join(FreightListing, FreightBid.listing_id == FreightListing.id)
        .where(
            FreightBid.status == BidStatus.ACCEPTED,
            FreightListing.cargo_type == cargo_type,
        )
    )
    cargo_row = cargo_result.one_or_none()
    cargo_avg = float(cargo_row[0]) if cargo_row and cargo_row[0] else None
    cargo_count = int(cargo_row[1]) if cargo_row and cargo_row[1] else 0

    # Route-specific average (match pickup AND delivery city via addresses)
    # Simplified: use listing's pickup/delivery address cities
    route_avg = None
    route_count = 0
    try:
        from app.models.freight import Address
        route_result = await db.execute(
            select(
                func.avg(FreightBid.price),
                func.count(FreightBid.id),
            )
            .join(FreightListing, FreightBid.listing_id == FreightListing.id)
            .join(
                Address,
                FreightListing.pickup_address_id == Address.id,
            )
            .where(
                FreightBid.status == BidStatus.ACCEPTED,
                Address.city.ilike(f"%{pickup_city}%"),
            )
        )
        route_row = route_result.one_or_none()
        if route_row and route_row[0]:
            route_avg = float(route_row[0])
            route_count = int(route_row[1])
    except Exception:
        pass

    return cargo_avg, cargo_count, route_avg, route_count


# ═══════════════════════════════════════════════════════════════
#  POST /pricing/estimate — Get price recommendation
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/estimate",
    response_model=PriceEstimateResponse,
    summary="Get AI-powered price recommendation for a freight load",
)
async def estimate_price(
    body: PriceEstimateRequest,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> PriceEstimateResponse:
    """
    Provide load details and receive a recommended bid price range.

    The engine uses:
    - **35+ engineered features** covering distance, fuel, weight,
      cargo risk, urgency, regional demand, temporal patterns, and
      historical prices
    - **LightGBM gradient boosted trees** trained on Ghana freight data
    - **Quantile regression** for confidence intervals (15th–85th percentile)
    - Falls back to a calibrated rule-based estimator if no ML model is loaded

    Returns a price range (low/mid/high) in GHS with confidence score
    and feature importance for transparency.
    """
    # Calculate distance if not provided
    distance_km = body.distance_km
    if distance_km is None:
        if all([body.pickup_lat, body.pickup_lng, body.delivery_lat, body.delivery_lng]):
            straight_line = haversine_km(
                body.pickup_lat, body.pickup_lng,
                body.delivery_lat, body.delivery_lng,
            )
            # Road distance multiplier for Ghana (~1.3× straight line)
            distance_km = round(straight_line * 1.3, 1)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either distance_km or both pickup and delivery coordinates are required",
            )

    # Calculate volume if dimensions provided
    volume_cm3 = None
    if all([body.dimensions_length_cm, body.dimensions_width_cm, body.dimensions_height_cm]):
        volume_cm3 = (
            body.dimensions_length_cm
            * body.dimensions_width_cm
            * body.dimensions_height_cm
        )

    # Get historical prices from database
    hist_avg, hist_count, route_avg, route_count = await _get_historical_prices(
        db, body.cargo_type, body.pickup_city, body.delivery_city,
    )

    # Extract features
    features = extract_features(
        distance_km=distance_km,
        pickup_lat=body.pickup_lat,
        pickup_lng=body.pickup_lng,
        delivery_lat=body.delivery_lat,
        delivery_lng=body.delivery_lng,
        pickup_city=body.pickup_city,
        delivery_city=body.delivery_city,
        pickup_region=body.pickup_region,
        delivery_region=body.delivery_region,
        weight_kg=body.weight_kg,
        cargo_type=body.cargo_type,
        vehicle_type=body.vehicle_type,
        dimensions_volume_cm3=volume_cm3,
        urgency=body.urgency,
        historical_avg_price=hist_avg,
        historical_price_count=hist_count,
        route_avg_price=route_avg,
        route_price_count=route_count,
    )

    # Get prediction
    predictor = get_predictor()
    prediction = predictor.predict(features)

    # Log the pricing run to database
    pricing_run = AIPricingRun(
        listing_id=body.listing_id,
        model_version=prediction["model_version"],
        features_json=json.dumps({
            k: round(v, 6) if isinstance(v, float) else v
            for k, v in features.items()
        }),
        suggested_price=prediction["price_mid"],
        price_low=prediction["price_low"],
        price_high=prediction["price_high"],
        confidence=prediction["confidence"],
        currency="GHS",
        explanation_json=json.dumps(prediction["feature_importance"]),
    )
    db.add(pricing_run)
    await db.flush()

    # Build response
    importance_items = [
        FeatureImportanceItem(**fi)
        for fi in prediction["feature_importance"]
    ]

    return PriceEstimateResponse(
        price_low=prediction["price_low"],
        price_mid=prediction["price_mid"],
        price_high=prediction["price_high"],
        currency="GHS",
        confidence=prediction["confidence"],
        model_version=prediction["model_version"],
        method=prediction["method"],
        feature_importance=importance_items,
        fuel_cost_estimate=round(features.get("fuel_cost_estimate", 0), 2),
        distance_km=distance_km,
        weight_kg=body.weight_kg,
        pricing_run_id=pricing_run.id,
    )


# ═══════════════════════════════════════════════════════════════
#  GET /pricing/breakdown/{listing_id} — Breakdown for listing
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/breakdown/{listing_id}",
    response_model=PriceBreakdownResponse,
    summary="Price breakdown for an existing listing",
)
async def price_breakdown(
    listing_id: uuid.UUID,
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> PriceBreakdownResponse:
    """
    Get a detailed price analysis for an existing listing, including:
    - AI price recommendation
    - Comparison with the shipper's asking price
    - Average bid price and bid count
    - Market position assessment
    """
    # Get listing
    result = await db.execute(
        select(FreightListing).where(FreightListing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Build estimate request from listing data
    pickup = listing.pickup_address
    delivery = listing.delivery_address

    distance_km = listing.distance_km
    if not distance_km and pickup and delivery:
        if all([pickup.latitude, pickup.longitude, delivery.latitude, delivery.longitude]):
            distance_km = round(
                haversine_km(pickup.latitude, pickup.longitude,
                             delivery.latitude, delivery.longitude) * 1.3,
                1,
            )
    distance_km = distance_km or 100.0

    volume_cm3 = None
    if all([listing.dimensions_length_cm, listing.dimensions_width_cm, listing.dimensions_height_cm]):
        volume_cm3 = (
            listing.dimensions_length_cm
            * listing.dimensions_width_cm
            * listing.dimensions_height_cm
        )

    cargo_type = listing.cargo_type.value if hasattr(listing.cargo_type, "value") else listing.cargo_type
    vehicle_type = listing.vehicle_type.value if hasattr(listing.vehicle_type, "value") else listing.vehicle_type
    urgency = listing.urgency.value if hasattr(listing.urgency, "value") else listing.urgency
    pickup_city = pickup.city if pickup else ""
    delivery_city = delivery.city if delivery else ""
    pickup_region = pickup.region or "" if pickup else ""
    delivery_region = delivery.region or "" if delivery else ""

    hist_avg, hist_count, route_avg, route_count = await _get_historical_prices(
        db, cargo_type, pickup_city, delivery_city,
    )

    features = extract_features(
        distance_km=distance_km,
        pickup_lat=pickup.latitude if pickup else None,
        pickup_lng=pickup.longitude if pickup else None,
        delivery_lat=delivery.latitude if delivery else None,
        delivery_lng=delivery.longitude if delivery else None,
        pickup_city=pickup_city,
        delivery_city=delivery_city,
        pickup_region=pickup_region,
        delivery_region=delivery_region,
        weight_kg=listing.weight_kg,
        cargo_type=cargo_type,
        vehicle_type=vehicle_type,
        dimensions_volume_cm3=volume_cm3,
        urgency=urgency,
        historical_avg_price=hist_avg,
        historical_price_count=hist_count,
        route_avg_price=route_avg,
        route_price_count=route_count,
    )

    predictor = get_predictor()
    prediction = predictor.predict(features)

    # Log pricing run
    pricing_run = AIPricingRun(
        listing_id=listing_id,
        model_version=prediction["model_version"],
        features_json=json.dumps({
            k: round(v, 6) if isinstance(v, float) else v
            for k, v in features.items()
        }),
        suggested_price=prediction["price_mid"],
        price_low=prediction["price_low"],
        price_high=prediction["price_high"],
        confidence=prediction["confidence"],
        currency="GHS",
        explanation_json=json.dumps(prediction["feature_importance"]),
    )
    db.add(pricing_run)
    await db.flush()

    # Get bid statistics
    bid_result = await db.execute(
        select(
            func.avg(FreightBid.price),
            func.count(FreightBid.id),
        ).where(
            FreightBid.listing_id == listing_id,
            FreightBid.status.in_([BidStatus.PENDING, BidStatus.ACCEPTED]),
        )
    )
    bid_row = bid_result.one_or_none()
    avg_bid = float(bid_row[0]) if bid_row and bid_row[0] else None
    bid_count = int(bid_row[1]) if bid_row else 0

    # Market position
    shipper_price = float(listing.shipper_price) if listing.shipper_price else None
    price_vs_market = None
    if shipper_price and prediction["price_mid"]:
        ratio = shipper_price / prediction["price_mid"]
        if ratio < 0.90:
            price_vs_market = "below_market"
        elif ratio > 1.15:
            price_vs_market = "above_market"
        else:
            price_vs_market = "at_market"

    importance_items = [
        FeatureImportanceItem(**fi)
        for fi in prediction["feature_importance"]
    ]

    estimate = PriceEstimateResponse(
        price_low=prediction["price_low"],
        price_mid=prediction["price_mid"],
        price_high=prediction["price_high"],
        currency="GHS",
        confidence=prediction["confidence"],
        model_version=prediction["model_version"],
        method=prediction["method"],
        feature_importance=importance_items,
        fuel_cost_estimate=round(features.get("fuel_cost_estimate", 0), 2),
        distance_km=distance_km,
        weight_kg=listing.weight_kg,
        pricing_run_id=pricing_run.id,
    )

    return PriceBreakdownResponse(
        listing_id=listing_id,
        estimate=estimate,
        listing_shipper_price=shipper_price,
        avg_bid_price=round(avg_bid, 2) if avg_bid else None,
        bid_count=bid_count,
        price_vs_market=price_vs_market,
    )


# ═══════════════════════════════════════════════════════════════
#  GET /pricing/model-status — Current model info
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/model-status",
    response_model=ModelStatusResponse,
    summary="Get current pricing model status",
)
async def model_status(
    user: User = Depends(require_any_authenticated),
) -> ModelStatusResponse:
    predictor = get_predictor()
    info = predictor.status
    return ModelStatusResponse(
        version=info["version"],
        is_ml_loaded=info["is_ml_loaded"],
        feature_count=info["feature_count"],
    )


# ═══════════════════════════════════════════════════════════════
#  POST /pricing/train — Train a new model (admin only)
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/train",
    response_model=TrainModelResponse,
    summary="Train a new pricing model (admin only)",
)
async def train_model(
    body: TrainModelRequest,
    user: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
) -> TrainModelResponse:
    """
    Trigger training of a new pricing model.

    Uses synthetic data calibrated to Ghana freight market parameters.
    In production, this would query real historical data from the database.

    **Admin only.** Training takes 10–30 seconds depending on dataset size.
    """
    from app.ml.training import train_pricing_model

    try:
        result = train_pricing_model(
            n_synthetic=body.n_samples,
            version_tag=body.version_tag,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    metrics = result["metrics"]

    # Save model version to database
    model_version = PricingModelVersion(
        version=result["version"],
        algorithm="LightGBM",
        status=ModelStatus.ACTIVE,
        feature_names_json=json.dumps(result["feature_names"]),
        feature_count=len(result["feature_names"]),
        training_samples=metrics["training_samples"],
        validation_samples=metrics["validation_samples"],
        metrics_json=json.dumps(metrics),
        mae=metrics.get("mae"),
        rmse=metrics.get("rmse"),
        r2_score=metrics.get("r2_score"),
        mape=metrics.get("mape"),
        model_artifact_path=result["artifact_path"],
        trained_at=datetime.now(timezone.utc),
        activated_at=datetime.now(timezone.utc),
    )
    db.add(model_version)

    # Retire previous active models
    prev_result = await db.execute(
        select(PricingModelVersion).where(
            PricingModelVersion.status == ModelStatus.ACTIVE,
            PricingModelVersion.version != result["version"],
        )
    )
    for prev in prev_result.scalars().all():
        prev.status = ModelStatus.RETIRED
        prev.retired_at = datetime.now(timezone.utc)

    await db.flush()

    # Hot-reload the predictor
    predictor = get_predictor()
    predictor.load_model(result["artifact_path"])

    return TrainModelResponse(
        message=f"Model {result['version']} trained and activated successfully",
        version=result["version"],
        metrics=metrics,
        artifact_path=result["artifact_path"],
        training_samples=metrics["training_samples"],
        validation_samples=metrics["validation_samples"],
    )


# ═══════════════════════════════════════════════════════════════
#  GET /pricing/models — List model versions (admin)
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/models",
    response_model=list[ModelVersionResponse],
    summary="List pricing model versions (admin)",
)
async def list_models(
    user: User = Depends(require_system_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ModelVersionResponse]:
    result = await db.execute(
        select(PricingModelVersion).order_by(PricingModelVersion.created_at.desc()).limit(20)
    )
    versions = result.scalars().all()
    return [
        ModelVersionResponse(
            id=v.id,
            version=v.version,
            algorithm=v.algorithm,
            status=v.status.value if hasattr(v.status, "value") else v.status,
            feature_count=v.feature_count,
            training_samples=v.training_samples,
            validation_samples=v.validation_samples,
            mae=v.mae,
            rmse=v.rmse,
            r2_score=v.r2_score,
            mape=v.mape,
            model_artifact_path=v.model_artifact_path,
            trained_at=v.trained_at,
            created_at=v.created_at,
        )
        for v in versions
    ]
