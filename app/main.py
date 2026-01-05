import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from config import get_settings

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
    if settings.webhook_url:
        logger.info("Bot started in webhook mode")
    else:
        # Start polling in background for development
        logger.info("No webhook URL configured. Use 'python run_polling.py' for polling mode.")    
    yield    
    # Shutdown
    logger.info("Bot shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="YouTube Comment Analyzer Bot",
    description="Telegram bot for analyzing YouTube video comments",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "YouTube Comment Analyzer Bot is running"}


@app.get("/health")
async def health(
    bot = Depends()
):
    """Detailed health check."""
    bot = app.state.bot
    dp = app.state.dp
    
    return {
        "status": "healthy",
        "bot": "initialized" if bot else "not initialized",
        "dispatcher": "initialized" if dp else "not initialized"
    }


@app.post("/webhook")
async def webhook(request: Request):
    """Handle Telegram webhook updates."""
    # global bot, dp
    # Bot and dispatcher are stored on the FastAPI app state at runtime
    # Access them via request.app.state.bot and request.app.state.dp
    bot = app.state.bot
    dp = app.state.dp
    
    if bot is None or dp is None:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return JSONResponse(content={"ok": True})
    except Exception as e:
        logger.exception("Error processing webhook update")
        raise HTTPException(status_code=500, detail=str(e))


# For running with: uvicorn app.main:app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
