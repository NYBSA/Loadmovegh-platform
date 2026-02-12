"""
LoadMoveGH — SQLAlchemy Models: Users, Organizations, Roles, Permissions
Matches the ARCHITECTURE.md schema for Organization & Users.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ── Enums ────────────────────────────────────────────────────

class OrgType(str, enum.Enum):
    SHIPPER = "shipper"
    COURIER = "courier"
    BOTH = "both"


class OrgStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class KYCStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class RoleName(str, enum.Enum):
    SYSTEM_ADMIN = "system_admin"
    ORG_ADMIN = "org_admin"
    SHIPPER = "shipper"
    COURIER = "courier"
    SHIPPER_VIEWER = "shipper_viewer"
    COURIER_DRIVER = "courier_driver"
    SUPPORT_AGENT = "support_agent"


# ── Helpers ──────────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ═══════════════════════════════════════════════════════════════
#  ORGANIZATION
# ═══════════════════════════════════════════════════════════════

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[OrgType] = mapped_column(
        SAEnum(OrgType, name="org_type", create_constraint=True),
        nullable=False,
        default=OrgType.SHIPPER,
    )
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[OrgStatus] = mapped_column(
        SAEnum(OrgStatus, name="org_status", create_constraint=True),
        nullable=False,
        default=OrgStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # relationships
    users: Mapped[List["User"]] = relationship(back_populates="organization", lazy="selectin")


# ═══════════════════════════════════════════════════════════════
#  USER
# ═══════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_phone", "phone", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )

    # Identity
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    # Verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    kyc_status: Mapped[KYCStatus] = mapped_column(
        SAEnum(KYCStatus, name="kyc_status", create_constraint=True),
        nullable=False,
        default=KYCStatus.NOT_STARTED,
    )

    # State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # OTP for phone login / verification
    otp_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    otp_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Password reset
    password_reset_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        back_populates="users", lazy="selectin"
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def role_names(self) -> list[str]:
        return [ur.role.name for ur in self.user_roles if ur.role]


# ═══════════════════════════════════════════════════════════════
#  ROLE & PERMISSIONS (RBAC)
# ═══════════════════════════════════════════════════════════════

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    permissions: Mapped[List["RolePermission"]] = relationship(
        back_populates="role", lazy="selectin", cascade="all, delete-orphan"
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        back_populates="role", lazy="selectin"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "resource", "action", name="uq_role_resource_action"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship
    role: Mapped["Role"] = relationship(back_populates="permissions")


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="user_roles")
    role: Mapped["Role"] = relationship(back_populates="user_roles")


# ═══════════════════════════════════════════════════════════════
#  AUDIT LOG
# ═══════════════════════════════════════════════════════════════

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    changes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
