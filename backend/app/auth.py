"""JumpCloud OIDC authentication framework.

When AUTH_ENABLED=false (default), all endpoints use a demo user.
When AUTH_ENABLED=true, tokens are validated against JumpCloud OIDC.
"""

from dataclasses import dataclass, field
from enum import Enum

from fastapi import Header, HTTPException

from .config import settings


class UserRole(str, Enum):
    ANALYST = "analyst"
    ADMIN = "admin"
    READONLY = "readonly"


@dataclass
class CurrentUser:
    id: str                          # JumpCloud user ID
    email: str
    name: str
    role: UserRole
    allowed_clients: list[str] = field(default_factory=list)  # empty = all


DEMO_USER = CurrentUser(
    id="demo-analyst",
    email="demo@example.com",
    name="Demo Analyst",
    role=UserRole.ANALYST,
    allowed_clients=[],
)


async def _validate_jumpcloud_token(token: str) -> CurrentUser:
    """Validate a JumpCloud OIDC JWT and return a CurrentUser.

    # TODO: Fetch JWKS from settings.jumpcloud_jwks_url (cache keys)
    # TODO: Decode + verify JWT with python-jose
    #       - Verify issuer == settings.jumpcloud_issuer
    #       - Verify audience == settings.jumpcloud_audience
    #       - Check expiration
    # TODO: Extract claims (sub, email, name, groups)
    # TODO: Map JumpCloud groups -> UserRole
    # TODO: Map groups -> allowed_clients list
    """
    raise NotImplementedError("JumpCloud token validation not yet configured")


async def get_current_user(
    authorization: str = Header(default=""),
    x_user_id: str = Header(default="demo-analyst", alias="x-user-id"),
) -> CurrentUser:
    """FastAPI dependency that resolves the current user.

    With AUTH_ENABLED=false: returns a demo user (backward compatible).
    With AUTH_ENABLED=true: validates the Bearer token against JumpCloud.
    """
    if not settings.auth_enabled:
        return CurrentUser(
            id=x_user_id,
            email=f"{x_user_id}@example.com",
            name=x_user_id,
            role=UserRole.ANALYST,
            allowed_clients=[],
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    return await _validate_jumpcloud_token(token)
