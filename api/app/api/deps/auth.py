"""
LoadMoveGH — FastAPI Dependencies: Authentication & RBAC
Provides reusable dependencies for JWT validation and role-based access control.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


# ═══════════════════════════════════════════════════════════════
#  GET CURRENT USER (from JWT)
# ═══════════════════════════════════════════════════════════════

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT access token from the Authorization header,
    then return the corresponding User from the database.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


# ═══════════════════════════════════════════════════════════════
#  GET CURRENT ACTIVE USER (convenience)
# ═══════════════════════════════════════════════════════════════

async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Ensure the user account is active."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


# ═══════════════════════════════════════════════════════════════
#  ROLE-BASED ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════

class RoleChecker:
    """
    Dependency class that checks if the current user has at least one
    of the required roles.
    """

    def __init__(self, required_roles: List[str]) -> None:
        self.required_roles = required_roles

    async def __call__(
        self,
        user: User = Depends(get_current_active_user),
    ) -> User:
        user_roles = user.role_names
        if not any(role in user_roles for role in self.required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(self.required_roles)}",
            )
        return user


class PermissionChecker:
    """
    Dependency class that checks if the current user has a specific
    permission (resource + action) via their roles.
    """

    def __init__(self, resource: str, action: str) -> None:
        self.resource = resource
        self.action = action

    async def __call__(
        self,
        user: User = Depends(get_current_active_user),
    ) -> User:
        for ur in user.user_roles:
            if ur.role:
                for perm in ur.role.permissions:
                    if perm.resource == self.resource and perm.action == self.action:
                        return user
                    if perm.resource == self.resource and perm.action == "*":
                        return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {self.resource}:{self.action}",
        )


# ═══════════════════════════════════════════════════════════════
#  CONVENIENCE ROLE DEPENDENCIES
# ═══════════════════════════════════════════════════════════════

require_system_admin = RoleChecker(["system_admin"])
require_org_admin = RoleChecker(["system_admin", "org_admin"])
require_shipper = RoleChecker(["system_admin", "org_admin", "shipper"])
require_courier = RoleChecker(["system_admin", "org_admin", "courier"])
require_any_authenticated = RoleChecker([
    "system_admin", "org_admin", "shipper", "courier",
    "shipper_viewer", "courier_driver", "support_agent",
])
