"""
LoadMoveGH — Authentication Endpoints
Register, login, refresh, phone OTP, password reset, email verify.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_verification_token,
    decode_refresh_token,
    generate_otp,
    hash_password,
    verify_password,
)
from app.models.user import Role, User, UserRole
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    PhoneLoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    VerifyOTPRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    if not body.email and not body.phone:
        raise HTTPException(status_code=400, detail="Either email or phone is required")

    # Check for existing user
    conditions = []
    if body.email:
        conditions.append(User.email == body.email)
    if body.phone:
        conditions.append(User.phone == body.phone)

    result = await db.execute(select(User).where(or_(*conditions)))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User with this email or phone already exists")

    user = User(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()

    # Assign role
    role_result = await db.execute(select(Role).where(Role.name == body.role))
    role = role_result.scalar_one_or_none()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))

    await db.flush()

    return RegisterResponse(user_id=user.id, email=body.email, phone=body.phone)


@router.post("/login", response_model=TokenResponse, summary="Login with email/phone + password")
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    if not body.email and not body.phone:
        raise HTTPException(status_code=400, detail="Email or phone required")

    conditions = []
    if body.email:
        conditions.append(User.email == body.email)
    if body.phone:
        conditions.append(User.phone == body.phone)

    result = await db.execute(select(User).where(or_(*conditions)))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    user.last_login_at = datetime.now(timezone.utc)
    access = create_access_token(user.id, {"roles": user.role_names})
    refresh = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    import jwt
    try:
        payload = decode_refresh_token(body.refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    access = create_access_token(user.id, {"roles": user.role_names})
    new_refresh = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/phone-login", response_model=MessageResponse, summary="Request OTP for phone login")
async def phone_login(
    body: PhoneLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="No account with this phone number")

    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    await db.flush()

    # In production: send via SMS gateway
    return MessageResponse(message=f"OTP sent to {body.phone}. [Dev: {otp}]")


@router.post("/verify-otp", response_model=TokenResponse, summary="Verify OTP and get tokens")
async def verify_otp(
    body: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)
    if not user.otp_code or user.otp_code != body.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if user.otp_expires_at and user.otp_expires_at < now:
        raise HTTPException(status_code=400, detail="OTP expired")

    user.otp_code = None
    user.otp_expires_at = None
    user.phone_verified = True
    user.last_login_at = now

    access = create_access_token(user.id, {"roles": user.role_names})
    refresh = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/forgot-password", response_model=MessageResponse, summary="Request password reset")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        return MessageResponse(message="If that email exists, a reset link has been sent.")

    token = create_verification_token(user.id)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.flush()

    # In production: send email with reset link
    return MessageResponse(message="If that email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse, summary="Reset password with token")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    import jwt as pyjwt
    try:
        payload = pyjwt.decode(body.token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)
    if user.password_reset_expires and user.password_reset_expires < now:
        raise HTTPException(status_code=400, detail="Reset token expired")

    user.password_hash = hash_password(body.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.flush()

    return MessageResponse(message="Password reset successfully")
