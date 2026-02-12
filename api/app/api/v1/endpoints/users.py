"""
LoadMoveGH — User Profile Endpoints
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user, require_system_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse, UpdateProfileRequest, UserProfile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfile, summary="Get my profile")
async def get_me(user: User = Depends(get_current_active_user)) -> UserProfile:
    return UserProfile(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        kyc_status=user.kyc_status.value if hasattr(user.kyc_status, "value") else user.kyc_status,
        is_active=user.is_active,
        roles=user.role_names,
        created_at=user.created_at,
    )


@router.patch("/me", response_model=UserProfile, summary="Update my profile")
async def update_me(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return UserProfile(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        kyc_status=user.kyc_status.value if hasattr(user.kyc_status, "value") else user.kyc_status,
        is_active=user.is_active,
        roles=user.role_names,
        created_at=user.created_at,
    )


@router.get(
    "",
    response_model=list[UserProfile],
    summary="List all users (admin only)",
    dependencies=[Depends(require_system_admin)],
)
async def list_users(db: AsyncSession = Depends(get_db)) -> list[UserProfile]:
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(100))
    users = result.scalars().all()
    return [
        UserProfile(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            phone=u.phone,
            email_verified=u.email_verified,
            phone_verified=u.phone_verified,
            kyc_status=u.kyc_status.value if hasattr(u.kyc_status, "value") else u.kyc_status,
            is_active=u.is_active,
            roles=u.role_names,
            created_at=u.created_at,
        )
        for u in users
    ]
