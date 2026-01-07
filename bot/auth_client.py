import time
import logging
from typing import Optional

import httpx
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_token: Optional[str] = None
_expires_at: int = 0


async def get_bot_token() -> str:
    """Obtain and cache a token from the API. Raises on failure."""
    global _token, _expires_at
    now = int(time.time())
    if _token and now < _expires_at - 30:
        return _token

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{settings.api_base_url}/auth/token",
            json={"client_id": settings.bot_client_id, "client_secret": settings.bot_client_secret},
            timeout=10.0,
        )
        r.raise_for_status()
        data = r.json()
        _token = data["access_token"]
        _expires_at = now + data.get("expires_in", settings.jwt_ttl_seconds)
        return _token


async def ensure_authorized() -> bool:
    """Return True if we have a valid token (or managed to fetch one)."""
    try:
        await get_bot_token()
        return True
    except Exception as e:  # pragma: no cover - network errors in tests
        logger.warning("Failed to obtain bot token: %s", e)
        return False


async def post_ingest(payload: dict) -> dict:
    """POST to /bot/ingest using the bot JWT.

    Raises exception on failure.
    """
    token = await get_bot_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{settings.api_base_url}/bot/ingest", json=payload, headers=headers, timeout=10.0)
        r.raise_for_status()
        return r.json()
