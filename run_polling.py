"""
Run the bot in polling mode (for local development).
Use this instead of webhook mode when developing locally.
"""
import asyncio
import logging
from app.main import start_polling

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("Starting YouTube Comment Analyzer Bot in polling mode...")
    print("Press Ctrl+C to stop")
    asyncio.run(start_polling())
