# Telegram bot handlers
from aiogram import Bot, Dispatcher
from config import get_settings
from bot.handlers import router
import logging

logger = logging.getLogger(__name__)

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