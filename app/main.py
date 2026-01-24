import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from config import get_settings
from app.routers.analyze.youtube_video import youtube_router

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


# OpenAPI tags metadata
openapi_tags = [
    {
        "name": "YouTube Analysis",
        "description": "Endpoints to analyze YouTube videos and comments",
    }
]

# Create FastAPI app
app = FastAPI(
    title="YouTube Comment Analyzer Bot",
    description="Telegram bot for analyzing YouTube video comments",
    version="1.1.0",
    lifespan=lifespan,
    openapi_tags=openapi_tags,
    docs_url="/swagger",
    openapi_url="/openapi.json",
    contact={"name": "Roman Iutsis"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"}
)

app.include_router(youtube_router)


@app.get("/health")
async def root():
    """Health check endpoint."""
    return {"status": "ok"}

# For running with: uvicorn app.main:app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
