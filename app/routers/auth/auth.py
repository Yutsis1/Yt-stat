
import time
import secrets
from typing import Optional, Dict, Any

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.modals.auth import TokenRequest, TokenResponse
from config import get_settings


# ===== JWT helpers =====
# The app issues short-lived JWTs for the bot using client credentials.
async def create_access_token(subject: str, scopes: Optional[list[str]] = None) -> str:
    """Create a signed JWT used by the bot to call protected endpoints."""
    settings = get_settings()
    now = int(time.time())
    payload: Dict[str, Any] = {
        "iss": "your-fastapi-service",
        "sub": subject,          # e.g. "telegram-bot"
        "iat": now,
        "exp": now + settings.jwt_ttl_seconds,
        "scopes": scopes or ["bot"],
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def verify_client_credentials(client_id: str, client_secret: str) -> None:
    """Validate bot client_id/client_secret using constant-time comparisons."""
    settings = get_settings()
    # constant-time comparisons
    if not secrets.compare_digest(client_id, settings.bot_client_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")
    if not secrets.compare_digest(client_secret, settings.bot_client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")


# ===== Auth dependency for protected routes =====
# All routes under /bot require a valid Bearer JWT with the "bot" scope.
bearer = HTTPBearer(auto_error=False)


async def require_bot_jwt(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> Dict[str, Any]:
    """FastAPI dependency that enforces bot authentication on protected routes."""
    settings = get_settings()
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret,
                             algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    # Optional checks
    scopes = payload.get("scopes", [])
    if "bot" not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")

    return payload


# ===== Routers =====
auth_router = APIRouter(prefix="/auth", tags=["auth"])
# /bot routes are protected by require_bot_jwt so only the bot can call them.
bot_router = APIRouter(
    prefix="/bot",
    tags=["bot"],
    dependencies=[Depends(require_bot_jwt)],  # protect everything under /bot
)


@auth_router.post("/token", response_model=TokenResponse)
async def issue_token(req: TokenRequest):
    """Exchange bot client credentials for a JWT."""
    settings = get_settings()
    await verify_client_credentials(req.client_id, req.client_secret)
    access_token = await create_access_token(subject="telegram-bot", scopes=["bot"])
    return TokenResponse(access_token=access_token, expires_in=settings.jwt_ttl_seconds)


@bot_router.post("/ingest")
async def ingest(payload: dict):
    # Example bot-only endpoint (requires valid Bearer JWT).
    return {"ok": True, "received": payload}


app = FastAPI()
app.include_router(auth_router)
app.include_router(bot_router)
