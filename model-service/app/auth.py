"""
API key authentication.

A model that decides whether a piece of hospital equipment gets flagged
for emergency maintenance should not be callable by anyone on the internet.
This is deliberately simple (static key set, checked in constant time) —
enough for a service sitting behind a hospital's own network or API
gateway. For a multi-tenant SaaS deployment, swap this for OAuth2/JWT with
per-customer keys issued via a proper identity provider.
"""
import hmac
import logging

from fastapi import Header, HTTPException, status

from app.config import settings

logger = logging.getLogger("mediguard.auth")


def _matches_any(candidate: str, valid_keys: set[str]) -> bool:
    """Compare against each valid key using a constant-time comparison,
    to avoid leaking key length/prefix via response timing."""
    return any(hmac.compare_digest(candidate, key) for key in valid_keys)


async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header.",
        )
    if not _matches_any(x_api_key, settings.api_key_set):
        logger.warning("Rejected request with invalid API key (prefix=%s...)", x_api_key[:6])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    return x_api_key
