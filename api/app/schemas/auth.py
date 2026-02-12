"""
LoadMoveGH — Pydantic Schemas for Authentication & User Management
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Ghana phone number regex ────────────────────────────────
GHANA_PHONE_RE = re.compile(r"^(\+233|0)(2[034-9]|5[045-9]|24|54|55|27|57|26|56)\d{7}$")


# ═══════════════════════════════════════════════════════════════
#  REGISTER
# ═══════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field("shipper", description="Initial role: shipper or courier")

    @field_validator("phone")
    @classmethod
    def validate_ghana_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not GHANA_PHONE_RE.match(v):
            raise ValueError(
                "Invalid Ghana phone number. Use format: +233XXXXXXXXX or 0XXXXXXXXX"
            )
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v.lower() not in ("shipper", "courier"):
            raise ValueError("Role must be 'shipper' or 'courier'")
        return v.lower()


class RegisterResponse(BaseModel):
    message: str = "Registration successful. Please verify your email."
    user_id: uuid.UUID
    email: Optional[str] = None
    phone: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ═══════════════════════════════════════════════════════════════
#  PHONE OTP
# ═══════════════════════════════════════════════════════════════

class PhoneLoginRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not GHANA_PHONE_RE.match(v):
            raise ValueError("Invalid Ghana phone number")
        return v


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str = Field(..., min_length=4, max_length=10)


# ═══════════════════════════════════════════════════════════════
#  PASSWORD RESET
# ═══════════════════════════════════════════════════════════════

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ═══════════════════════════════════════════════════════════════
#  USER PROFILE
# ═══════════════════════════════════════════════════════════════

class UserProfile(BaseModel):
    id: uuid.UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    email_verified: bool = False
    phone_verified: bool = False
    kyc_status: str
    is_active: bool
    roles: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not GHANA_PHONE_RE.match(v):
            raise ValueError("Invalid Ghana phone number")
        return v


class MessageResponse(BaseModel):
    message: str
