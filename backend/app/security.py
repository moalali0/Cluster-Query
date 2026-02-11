"""Security middleware configuration — CORS, rate limiting, API key validation.

All features default to permissive/disabled so the demo works unchanged.
"""

from fastapi import Header, HTTPException

from .config import settings


def get_cors_config() -> dict:
    """Build CORS middleware kwargs from settings."""
    if settings.cors_origins == "*":
        return dict(
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    return dict(
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "x-user-id", "x-api-key"],
    )


async def check_api_key(
    x_api_key: str = Header(default="", alias="x-api-key"),
) -> None:
    """Validate API key if API_KEY_REQUIRED is enabled.

    # TODO: Use hmac.compare_digest for constant-time comparison
    """
    if not settings.api_key_required:
        return
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")


async def rate_limit() -> None:
    """Enforce per-minute rate limiting if configured.

    # TODO: Implement with Redis or in-memory sliding window
    #       Track by IP or user ID
    #       Return 429 with Retry-After header when exceeded
    """
    if settings.rate_limit_per_minute <= 0:
        return
    # TODO: implement rate limiting logic
