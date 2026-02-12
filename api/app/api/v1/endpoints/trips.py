"""
LoadMoveGH — Freight Trips Endpoints
GET trip detail, PATCH trip status, GET my trips, confirm delivery.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import require_any_authenticated
from app.core.database import get_db
from app.models.freight import FreightListing, FreightTrip, ListingStatus, TripStatus
from app.models.user import User
from app.schemas.freight import (
    TRIP_STATUS_TRANSITIONS,
    TripResponse,
    UpdateTripStatusRequest,
    UpdateTripStatusResponse,
)

router = APIRouter(prefix="/trips", tags=["Freight Trips"])


def build_trip_response(trip: FreightTrip) -> TripResponse:
    courier_name = trip.courier.full_name if trip.courier else None
    pickup_city = delivery_city = None
    distance_km = None
    if trip.listing:
        if trip.listing.pickup_address:
            pickup_city = trip.listing.pickup_address.city
        if trip.listing.delivery_address:
            delivery_city = trip.listing.delivery_address.city
        distance_km = trip.listing.distance_km

    return TripResponse(
        id=trip.id, listing_id=trip.listing_id, bid_id=trip.bid_id,
        courier_id=trip.courier_id, courier_name=courier_name,
        pickup_city=pickup_city, delivery_city=delivery_city, distance_km=distance_km,
        status=trip.status.value if isinstance(trip.status, TripStatus) else trip.status,
        current_latitude=trip.current_latitude, current_longitude=trip.current_longitude,
        current_location_name=trip.current_location_name,
        proof_of_delivery_url=trip.proof_of_delivery_url, delivery_notes=trip.delivery_notes,
        started_at=trip.started_at, picked_up_at=trip.picked_up_at,
        delivered_at=trip.delivered_at, confirmed_at=trip.confirmed_at,
        created_at=trip.created_at, updated_at=trip.updated_at,
    )


@router.get("/{trip_id}", response_model=TripResponse, summary="Get trip detail")
async def get_trip(trip_id: uuid.UUID, user: User = Depends(require_any_authenticated),
                   db: AsyncSession = Depends(get_db)) -> TripResponse:
    result = await db.execute(select(FreightTrip).where(FreightTrip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    is_admin = any(r in user.role_names for r in ("system_admin", "org_admin"))
    is_courier = trip.courier_id == user.id
    is_shipper = trip.listing and trip.listing.shipper_id == user.id
    if not (is_courier or is_shipper or is_admin):
        raise HTTPException(status_code=403, detail="Not authorised")

    return build_trip_response(trip)


@router.patch("/{trip_id}/status", response_model=UpdateTripStatusResponse, summary="Update trip status")
async def update_trip_status(trip_id: uuid.UUID, body: UpdateTripStatusRequest,
                             user: User = Depends(require_any_authenticated),
                             db: AsyncSession = Depends(get_db)) -> UpdateTripStatusResponse:
    result = await db.execute(select(FreightTrip).where(FreightTrip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    is_admin = any(r in user.role_names for r in ("system_admin", "org_admin"))
    is_courier = trip.courier_id == user.id
    is_shipper = trip.listing and trip.listing.shipper_id == user.id
    if not (is_courier or is_shipper or is_admin):
        raise HTTPException(status_code=403, detail="Not authorised")

    current = trip.status.value if isinstance(trip.status, TripStatus) else trip.status
    new = body.status
    allowed = TRIP_STATUS_TRANSITIONS.get(current, [])
    if new not in allowed and not is_admin:
        raise HTTPException(status_code=400, detail=f"Invalid transition: {current} → {new}. Allowed: {', '.join(allowed) or 'none'}")

    courier_ok = {"picked_up", "in_transit", "at_waypoint", "delivered", "cancelled"}
    shipper_ok = {"confirmed", "disputed", "cancelled"}
    if not is_admin:
        if is_courier and new not in courier_ok:
            raise HTTPException(status_code=403, detail=f"Couriers cannot set status to '{new}'")
        if is_shipper and not is_courier and new not in shipper_ok:
            raise HTTPException(status_code=403, detail=f"Shippers cannot set status to '{new}'")

    if new == "delivered" and not body.proof_of_delivery_url and not trip.proof_of_delivery_url:
        raise HTTPException(status_code=400, detail="Proof of delivery URL required")

    previous = current
    trip.status = TripStatus(new)
    trip.updated_at = now = datetime.now(timezone.utc)
    if body.current_latitude is not None:
        trip.current_latitude = body.current_latitude
    if body.current_longitude is not None:
        trip.current_longitude = body.current_longitude
    if body.current_location_name is not None:
        trip.current_location_name = body.current_location_name
    if body.proof_of_delivery_url is not None:
        trip.proof_of_delivery_url = body.proof_of_delivery_url
    if body.delivery_notes is not None:
        trip.delivery_notes = body.delivery_notes

    if new == "picked_up":
        trip.picked_up_at = now
        trip.started_at = trip.started_at or now
        if trip.listing:
            trip.listing.status = ListingStatus.IN_TRANSIT
    elif new == "in_transit" and not trip.started_at:
        trip.started_at = now
    elif new == "delivered":
        trip.delivered_at = now
        if trip.listing:
            trip.listing.status = ListingStatus.DELIVERED
    elif new == "confirmed":
        trip.confirmed_at = now
        if trip.listing:
            trip.listing.status = ListingStatus.COMPLETED
    elif new == "cancelled" and trip.listing:
        trip.listing.status = ListingStatus.CANCELLED

    await db.flush()
    return UpdateTripStatusResponse(
        message=f"Trip status updated: {previous} → {new}",
        trip_id=trip.id, previous_status=previous, new_status=new, updated_at=trip.updated_at,
    )


@router.get("", response_model=list[TripResponse], summary="List my trips")
async def list_my_trips(
    trip_status: Optional[str] = Query(None), page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(require_any_authenticated), db: AsyncSession = Depends(get_db),
) -> list[TripResponse]:
    is_admin = any(r in user.role_names for r in ("system_admin", "org_admin"))
    stmt = select(FreightTrip)
    if not is_admin:
        stmt = stmt.join(FreightListing, FreightTrip.listing_id == FreightListing.id, isouter=True)
        stmt = stmt.where((FreightTrip.courier_id == user.id) | (FreightListing.shipper_id == user.id))
    if trip_status:
        stmt = stmt.where(FreightTrip.status == TripStatus(trip_status.lower()))
    stmt = stmt.order_by(FreightTrip.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    trips = (await db.execute(stmt)).scalars().unique().all()
    return [build_trip_response(t) for t in trips]


@router.post("/{trip_id}/confirm-delivery", response_model=UpdateTripStatusResponse, summary="Confirm delivery")
async def confirm_delivery(trip_id: uuid.UUID, user: User = Depends(require_any_authenticated),
                           db: AsyncSession = Depends(get_db)) -> UpdateTripStatusResponse:
    return await update_trip_status(trip_id, UpdateTripStatusRequest(status="confirmed"), user, db)
