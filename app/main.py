import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from config import get_settings
from app.routers.analyze.youtube_video import youtube_router
from app.routers.auth.auth import auth_router, bot_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.""" 
    settings = get_settings()  
    yield    
    # Shutdown
    logger.info("Bot shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="YouTube Comment Analyzer Bot",
    description="Telegram bot for analyzing YouTube video comments",
    version="1.1.0",
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(bot_router)
app.include_router(youtube_router)


@app.get("/health")
async def root():
    """Health check endpoint."""
    return {"status": "ok"}

# For running with: uvicorn app.main:app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
