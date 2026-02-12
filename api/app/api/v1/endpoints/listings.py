"""
LoadMoveGH — Freight Listings Endpoints
POST, GET (search+geo), GET/:id, PATCH, DELETE, bids, accept-bid.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import require_any_authenticated, require_shipper
from app.core.database import get_db
from app.models.freight import (
    Address,
    BidStatus,
    CargoType,
    FreightBid,
    FreightListing,
    FreightTrip,
    ListingStatus,
    TripStatus,
    Urgency,
    VehicleType,
)
from app.models.user import User
from app.schemas.freight import (
    CARGO_TYPES,
    VEHICLE_TYPES,
    AcceptBidRequest,
    AcceptBidResponse,
    AddressResponse,
    BidListResponse,
    BidResponse,
    CreateBidRequest,
    CreateListingRequest,
    ListingResponse,
    ListingSummary,
    MessageResponse,
    PaginatedListings,
    UpdateListingRequest,
)

router = APIRouter(prefix="/listings", tags=["Freight Listings"])


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_listing_response(listing: FreightListing) -> ListingResponse:
    shipper_name = listing.shipper.full_name if listing.shipper else None
    return ListingResponse(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        shipper_id=listing.shipper_id,
        shipper_name=shipper_name,
        pickup=AddressResponse.model_validate(listing.pickup_address),
        delivery=AddressResponse.model_validate(listing.delivery_address),
        distance_km=listing.distance_km,
        cargo_type=listing.cargo_type.value if isinstance(listing.cargo_type, CargoType) else listing.cargo_type,
        weight_kg=listing.weight_kg,
        dimensions_length_cm=listing.dimensions_length_cm,
        dimensions_width_cm=listing.dimensions_width_cm,
        dimensions_height_cm=listing.dimensions_height_cm,
        vehicle_type=listing.vehicle_type.value if isinstance(listing.vehicle_type, VehicleType) else listing.vehicle_type,
        shipper_price=float(listing.shipper_price) if listing.shipper_price else None,
        ai_suggested_price=float(listing.ai_suggested_price) if listing.ai_suggested_price else None,
        currency=listing.currency,
        urgency=listing.urgency.value if isinstance(listing.urgency, Urgency) else listing.urgency,
        status=listing.status.value if isinstance(listing.status, ListingStatus) else listing.status,
        special_instructions=listing.special_instructions,
        bid_count=listing.bid_count,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        expires_at=listing.expires_at,
    )


def build_listing_summary(listing: FreightListing) -> ListingSummary:
    return ListingSummary(
        id=listing.id,
        title=listing.title,
        pickup_city=listing.pickup_address.city if listing.pickup_address else "N/A",
        delivery_city=listing.delivery_address.city if listing.delivery_address else "N/A",
        distance_km=listing.distance_km,
        cargo_type=listing.cargo_type.value if isinstance(listing.cargo_type, CargoType) else listing.cargo_type,
        weight_kg=listing.weight_kg,
        vehicle_type=listing.vehicle_type.value if isinstance(listing.vehicle_type, VehicleType) else listing.vehicle_type,
        shipper_price=float(listing.shipper_price) if listing.shipper_price else None,
        ai_suggested_price=float(listing.ai_suggested_price) if listing.ai_suggested_price else None,
        currency=listing.currency,
        urgency=listing.urgency.value if isinstance(listing.urgency, Urgency) else listing.urgency,
        status=listing.status.value if isinstance(listing.status, ListingStatus) else listing.status,
        bid_count=listing.bid_count,
        created_at=listing.created_at,
    )


# ── POST /listings ───────────────────────────────────────────

@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED, summary="Post a new freight load")
async def create_listing(
    body: CreateListingRequest,
    user: User = Depends(require_shipper),
    db: AsyncSession = Depends(get_db),
) -> ListingResponse:
    pickup = Address(city=body.pickup.city, region=body.pickup.region, street=body.pickup.street,
                     postal_code=body.pickup.postal_code, latitude=body.pickup.latitude,
                     longitude=body.pickup.longitude, country=body.pickup.country)
    db.add(pickup)

    delivery = Address(city=body.delivery.city, region=body.delivery.region, street=body.delivery.street,
                       postal_code=body.delivery.postal_code, latitude=body.delivery.latitude,
                       longitude=body.delivery.longitude, country=body.delivery.country)
    db.add(delivery)
    await db.flush()

    distance_km = None
    if all([pickup.latitude, pickup.longitude, delivery.latitude, delivery.longitude]):
        distance_km = round(haversine_km(pickup.latitude, pickup.longitude, delivery.latitude, delivery.longitude), 1)

    listing = FreightListing(
        shipper_id=user.id, pickup_address_id=pickup.id, delivery_address_id=delivery.id,
        title=body.title, description=body.description, cargo_type=CargoType(body.cargo_type),
        weight_kg=body.weight_kg, dimensions_length_cm=body.dimensions_length_cm,
        dimensions_width_cm=body.dimensions_width_cm, dimensions_height_cm=body.dimensions_height_cm,
        vehicle_type=VehicleType(body.vehicle_type), shipper_price=body.shipper_price,
        currency=body.currency, urgency=Urgency(body.urgency), status=ListingStatus.ACTIVE,
        special_instructions=body.special_instructions, distance_km=distance_km,
    )
    db.add(listing)
    await db.flush()
    await db.refresh(listing, attribute_names=["shipper", "pickup_address", "delivery_address"])
    return build_listing_response(listing)


# ── GET /listings (search) ───────────────────────────────────

@router.get("", response_model=PaginatedListings, summary="Search and filter freight listings")
async def search_listings(
    q: Optional[str] = Query(None, max_length=200),
    origin_city: Optional[str] = Query(None, max_length=100),
    origin_region: Optional[str] = Query(None, max_length=100),
    destination_city: Optional[str] = Query(None, max_length=100),
    origin_lat: Optional[float] = Query(None, ge=-90, le=90),
    origin_lng: Optional[float] = Query(None, ge=-180, le=180),
    origin_radius_km: float = Query(50, ge=1, le=500),
    cargo_type: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    max_distance_km: Optional[float] = Query(None, ge=0),
    listing_status: Optional[str] = Query("active"),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(require_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> PaginatedListings:
    stmt = select(FreightListing).join(Address, FreightListing.pickup_address_id == Address.id, isouter=True)
    delivery_alias = Address.__table__.alias("delivery_addr")
    conditions = []

    if listing_status:
        conditions.append(FreightListing.status == ListingStatus(listing_status.lower()))
    if q:
        term = f"%{q}%"
        conditions.append(or_(FreightListing.title.ilike(term), FreightListing.description.ilike(term)))
    if origin_city:
        conditions.append(Address.city.ilike(f"%{origin_city}%"))
    if origin_region:
        conditions.append(Address.region.ilike(f"%{origin_region}%"))
    if destination_city:
        stmt = stmt.join(delivery_alias, FreightListing.delivery_address_id == delivery_alias.c.id)
        conditions.append(delivery_alias.c.city.ilike(f"%{destination_city}%"))
    if origin_lat is not None and origin_lng is not None:
        lat_d = origin_radius_km / 111.0
        lng_d = origin_radius_km / (111.0 * max(math.cos(math.radians(origin_lat)), 0.01))
        conditions.extend([
            Address.latitude.isnot(None), Address.longitude.isnot(None),
            Address.latitude.between(origin_lat - lat_d, origin_lat + lat_d),
            Address.longitude.between(origin_lng - lng_d, origin_lng + lng_d),
        ])
    if cargo_type:
        conditions.append(FreightListing.cargo_type == CargoType(cargo_type.lower()))
    if vehicle_type:
        conditions.append(FreightListing.vehicle_type == VehicleType(vehicle_type.lower()))
    if urgency:
        conditions.append(FreightListing.urgency == Urgency(urgency.lower()))
    if min_price is not None:
        conditions.append(FreightListing.shipper_price >= min_price)
    if max_price is not None:
        conditions.append(FreightListing.shipper_price <= max_price)
    if max_distance_km is not None:
        conditions.append(FreightListing.distance_km <= max_distance_km)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    sort_map = {"created_at": FreightListing.created_at, "price": FreightListing.shipper_price,
                "distance": FreightListing.distance_km, "weight": FreightListing.weight_kg}
    sort_col = sort_map.get(sort_by, FreightListing.created_at)
    stmt = stmt.order_by(sort_col.asc().nullslast() if sort_order == "asc" else sort_col.desc().nullslast())
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    listings = (await db.execute(stmt)).scalars().unique().all()
    summaries = []
    for l in listings:
        if origin_lat is not None and origin_lng is not None and l.pickup_address:
            if l.pickup_address.latitude and l.pickup_address.longitude:
                if haversine_km(origin_lat, origin_lng, l.pickup_address.latitude, l.pickup_address.longitude) > origin_radius_km:
                    continue
        summaries.append(build_listing_summary(l))

    return PaginatedListings(listings=summaries, total=total, page=page, per_page=per_page)


# ── GET /listings/available ──────────────────────────────────

@router.get("/available", response_model=PaginatedListings, summary="Browse available loads (couriers)")
async def available_listings(
    origin_city: Optional[str] = Query(None), destination_city: Optional[str] = Query(None),
    origin_lat: Optional[float] = Query(None, ge=-90, le=90),
    origin_lng: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: float = Query(50, ge=1, le=500),
    cargo_type: Optional[str] = Query(None), vehicle_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0), max_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("created_at"), sort_order: str = Query("desc"),
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(require_any_authenticated), db: AsyncSession = Depends(get_db),
) -> PaginatedListings:
    return await search_listings(
        q=None, origin_city=origin_city, origin_region=None, destination_city=destination_city,
        origin_lat=origin_lat, origin_lng=origin_lng, origin_radius_km=radius_km,
        cargo_type=cargo_type, vehicle_type=vehicle_type, urgency=None,
        min_price=min_price, max_price=max_price, max_distance_km=None,
        listing_status="active", sort_by=sort_by, sort_order=sort_order,
        page=page, per_page=per_page, user=user, db=db,
    )


# ── GET /listings/:id ───────────────────────────────────────

@router.get("/{listing_id}", response_model=ListingResponse, summary="Get listing detail")
async def get_listing(listing_id: uuid.UUID, user: User = Depends(require_any_authenticated),
                      db: AsyncSession = Depends(get_db)) -> ListingResponse:
    result = await db.execute(select(FreightListing).where(FreightListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return build_listing_response(listing)


# ── PATCH /listings/:id ─────────────────────────────────────

@router.patch("/{listing_id}", response_model=ListingResponse, summary="Update a freight listing")
async def update_listing(listing_id: uuid.UUID, body: UpdateListingRequest,
                         user: User = Depends(require_shipper), db: AsyncSession = Depends(get_db)) -> ListingResponse:
    result = await db.execute(select(FreightListing).where(FreightListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    is_admin = any(r in user.role_names for r in ("system_admin", "org_admin"))
    if listing.shipper_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorised")

    frozen = {ListingStatus.ASSIGNED, ListingStatus.IN_TRANSIT, ListingStatus.DELIVERED, ListingStatus.COMPLETED}
    if listing.status in frozen and body.status != "cancelled":
        raise HTTPException(status_code=400, detail="Cannot edit assigned/completed listing")

    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "cargo_type" and value:
            setattr(listing, field, CargoType(value))
        elif field == "vehicle_type" and value:
            setattr(listing, field, VehicleType(value))
        elif field == "urgency" and value:
            setattr(listing, field, Urgency(value))
        elif field == "status" and value:
            setattr(listing, field, ListingStatus(value))
        else:
            setattr(listing, field, value)

    listing.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(listing, attribute_names=["shipper", "pickup_address", "delivery_address"])
    return build_listing_response(listing)


# ── DELETE /listings/:id ─────────────────────────────────────

@router.delete("/{listing_id}", response_model=MessageResponse, summary="Cancel a freight listing")
async def delete_listing(listing_id: uuid.UUID, user: User = Depends(require_shipper),
                         db: AsyncSession = Depends(get_db)) -> MessageResponse:
    result = await db.execute(select(FreightListing).where(FreightListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    is_admin = any(r in user.role_names for r in ("system_admin", "org_admin"))
    if listing.shipper_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorised")
    if listing.status in (ListingStatus.IN_TRANSIT, ListingStatus.DELIVERED):
        raise HTTPException(status_code=400, detail="Cannot cancel active trip listing")

    listing.status = ListingStatus.CANCELLED
    listing.updated_at = datetime.now(timezone.utc)

    bids = (await db.execute(
        select(FreightBid).where(FreightBid.listing_id == listing_id, FreightBid.status == BidStatus.PENDING)
    )).scalars().all()
    for bid in bids:
        bid.status = BidStatus.REJECTED
        bid.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return MessageResponse(message=f"Listing {listing_id} cancelled. {len(bids)} bid(s) rejected.")


# ── GET /listings/:id/bids ───────────────────────────────────

@router.get("/{listing_id}/bids", response_model=BidListResponse, summary="View bids on a listing")
async def get_listing_bids(
    listing_id: uuid.UUID, bid_status: Optional[str] = Query(None),
    sort_by: str = Query("price"), sort_order: str = Query("asc"),
    user: User = Depends(require_any_authenticated), db: AsyncSession = Depends(get_db),
) -> BidListResponse:
    lr = await db.execute(select(FreightListing).where(FreightListing.id == listing_id))
    listing = lr.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    stmt = select(FreightBid).where(FreightBid.listing_id == listing_id)
    is_admin = any(r in user.role_names for r in ("system_admin", "org_admin"))
    if listing.shipper_id != user.id and not is_admin:
        stmt = stmt.where(FreightBid.courier_id == user.id)
    if bid_status:
        stmt = stmt.where(FreightBid.status == BidStatus(bid_status.lower()))

    sort_map = {"price": FreightBid.price, "created_at": FreightBid.created_at, "eta_hours": FreightBid.eta_hours}
    col = sort_map.get(sort_by, FreightBid.price)
    stmt = stmt.order_by(col.asc().nullslast() if sort_order == "asc" else col.desc().nullslast())

    bids = (await db.execute(stmt)).scalars().all()
    return BidListResponse(
        bids=[BidResponse(
            id=b.id, listing_id=b.listing_id, courier_id=b.courier_id,
            courier_name=b.courier.full_name if b.courier else None,
            price=float(b.price), currency=b.currency, eta_hours=b.eta_hours,
            eta_description=b.eta_description, message=b.message,
            status=b.status.value if isinstance(b.status, BidStatus) else b.status,
            created_at=b.created_at, updated_at=b.updated_at,
        ) for b in bids],
        total=len(bids),
    )


# ── POST /listings/:id/bids ─────────────────────────────────

@router.post("/{listing_id}/bids", response_model=BidResponse, status_code=status.HTTP_201_CREATED, summary="Place a bid")
async def create_bid(listing_id: uuid.UUID, body: CreateBidRequest,
                     user: User = Depends(require_any_authenticated), db: AsyncSession = Depends(get_db)) -> BidResponse:
    lr = await db.execute(select(FreightListing).where(FreightListing.id == listing_id))
    listing = lr.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status not in (ListingStatus.ACTIVE, ListingStatus.BIDDING):
        raise HTTPException(status_code=400, detail=f"Listing not open for bids ({listing.status.value})")
    if listing.shipper_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot bid on own listing")

    existing = (await db.execute(select(FreightBid).where(
        FreightBid.listing_id == listing_id, FreightBid.courier_id == user.id, FreightBid.status == BidStatus.PENDING
    ))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="You already have a pending bid")

    bid = FreightBid(listing_id=listing_id, courier_id=user.id, price=body.price, currency=body.currency,
                     eta_hours=body.eta_hours, eta_description=body.eta_description, message=body.message,
                     status=BidStatus.PENDING)
    db.add(bid)
    listing.bid_count += 1
    if listing.status == ListingStatus.ACTIVE:
        listing.status = ListingStatus.BIDDING
    await db.flush()
    await db.refresh(bid, attribute_names=["courier"])

    return BidResponse(
        id=bid.id, listing_id=bid.listing_id, courier_id=bid.courier_id,
        courier_name=bid.courier.full_name if bid.courier else None,
        price=float(bid.price), currency=bid.currency, eta_hours=bid.eta_hours,
        eta_description=bid.eta_description, message=bid.message,
        status=bid.status.value, created_at=bid.created_at, updated_at=bid.updated_at,
    )


# ── POST /listings/:id/accept-bid ───────────────────────────

@router.post("/{listing_id}/accept-bid", response_model=AcceptBidResponse, summary="Accept a bid and create a trip")
async def accept_bid(listing_id: uuid.UUID, body: AcceptBidRequest,
                     user: User = Depends(require_shipper), db: AsyncSession = Depends(get_db)) -> AcceptBidResponse:
    lr = await db.execute(select(FreightListing).where(FreightListing.id == listing_id))
    listing = lr.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    is_admin = any(r in user.role_names for r in ("system_admin", "org_admin"))
    if listing.shipper_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorised")
    if listing.status not in (ListingStatus.ACTIVE, ListingStatus.BIDDING):
        raise HTTPException(status_code=400, detail=f"Cannot accept bids ({listing.status.value})")

    br = await db.execute(select(FreightBid).where(FreightBid.id == body.bid_id, FreightBid.listing_id == listing_id))
    bid = br.scalar_one_or_none()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    if bid.status != BidStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Bid not pending ({bid.status.value})")

    now = datetime.now(timezone.utc)
    bid.status = BidStatus.ACCEPTED
    bid.updated_at = now

    for other in (await db.execute(select(FreightBid).where(
        FreightBid.listing_id == listing_id, FreightBid.id != bid.id, FreightBid.status == BidStatus.PENDING
    ))).scalars().all():
        other.status = BidStatus.REJECTED
        other.updated_at = now

    listing.status = ListingStatus.ASSIGNED
    listing.updated_at = now

    trip = FreightTrip(listing_id=listing_id, bid_id=bid.id, courier_id=bid.courier_id, status=TripStatus.PICKUP_PENDING)
    db.add(trip)
    await db.flush()

    return AcceptBidResponse(
        listing_id=listing_id, bid_id=bid.id, trip_id=trip.id,
        courier_name=bid.courier.full_name if bid.courier else None,
        accepted_price=float(bid.price),
    )
