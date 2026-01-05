
import time
import secrets
from typing import Optional, Dict, Any

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.modals.auth import TokenRequest, TokenResponse
from config import get_settings

settings = get_settings()


# ===== JWT helpers =====
async def create_access_token(subject: str, scopes: Optional[list[str]] = None) -> str:
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
    # constant-time comparisons
    if not secrets.compare_digest(client_id, settings.bot_client_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")
    if not secrets.compare_digest(client_secret, settings.bot_client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")


# ===== Auth dependency for protected routes =====
bearer = HTTPBearer(auto_error=False)


async def require_bot_jwt(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> Dict[str, Any]:
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
bot_router = APIRouter(
    prefix="/bot",
    tags=["bot"],
    dependencies=[Depends(require_bot_jwt)],  # protect everything under /bot
)


@auth_router.post("/token", response_model=TokenResponse)
async def issue_token(req: TokenRequest):
    await verify_client_credentials(req.client_id, req.client_secret)
    access_token = await create_access_token(subject="telegram-bot", scopes=["bot"])
    return TokenResponse(access_token=access_token, expires_in=settings.jwt_ttl_seconds)


@bot_router.post("/ingest")
async def ingest(payload: dict):
    # Your bot-only endpoint
    return {"ok": True, "received": payload}


app = FastAPI()
app.include_router(auth_router)
app.include_router(bot_router)
