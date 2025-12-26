import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from app.config import get_settings
from app.bot.handlers import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot and dispatcher instances
bot: Bot | None = None
dp: Dispatcher | None = None


async def setup_bot(
        bot_instance: Bot | None,
          dispatcher_instance: Dispatcher | None) -> tuple[Bot, Dispatcher]:
    """Initialize bot and dispatcher."""
    bot = bot_instance
    dp = dispatcher_instance
    
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    
    return bot, dp


async def start_polling(
        bot_instance: Bot | None,
        dispatcher_instance: Dispatcher | None
):
    """Start bot in polling mode (for development)."""
    bot = bot_instance
    dp = dispatcher_instance
    
    if bot is None or dp is None:
        bot, dp = await setup_bot( bot, dp)
    
    logger.info("Starting bot in polling mode...")
    await dp.start_polling(bot)


async def setup_webhook(
        bot_instance: Bot | None
):
    """Set up webhook for production."""
    bot = bot_instance
    
    settings = get_settings()
    if settings.webhook_url:
        webhook_url = f"{settings.webhook_url}/webhook"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")


async def shutdown_bot(bot_instance: Bot | None):
    """Clean up bot resources."""
    bot = bot_instance
    
    if bot:
        await bot.session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await setup_bot()
    
    settings = get_settings()
    if settings.webhook_url:
        await setup_webhook()
        logger.info("Bot started in webhook mode")
    else:
        # Start polling in background for development
        logger.info("No webhook URL configured. Use 'python run_polling.py' for polling mode.")
    
    yield
    
    # Shutdown
    await shutdown_bot()
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
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "bot": "initialized" if bot else "not initialized",
        "dispatcher": "initialized" if dp else "not initialized"
    }


@app.post("/webhook")
async def webhook(request: Request):
    """Handle Telegram webhook updates."""
    global bot, dp
    
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
