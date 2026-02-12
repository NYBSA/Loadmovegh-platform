"""
LoadMoveGH — API v1 Router
Aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.assistant import router as assistant_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.escrow import router as escrow_router
from app.api.v1.endpoints.fraud import router as fraud_router
from app.api.v1.endpoints.listings import router as listings_router
from app.api.v1.endpoints.matching import router as matching_router
from app.api.v1.endpoints.pricing import router as pricing_router
from app.api.v1.endpoints.trips import router as trips_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.wallets import router as wallets_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(listings_router)
api_router.include_router(trips_router)
api_router.include_router(wallets_router)
api_router.include_router(escrow_router)
api_router.include_router(pricing_router)
api_router.include_router(matching_router)
api_router.include_router(fraud_router)
api_router.include_router(assistant_router)
