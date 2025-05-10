import asyncio

from loguru import logger

from src.handlers import *  # noqa: F401, F403
from src.infrastructure.database.services import create_categories_if_not_exist
from src.infrastructure.telegram import bot

logger.add("fbb.log", rotation="50 MB")

async def start_bot_loop():
    logger.info("Bot started 🚀")

    while True:
        try:
            await bot.polling(none_stop=True, interval=0)
        except Exception as err:
            logger.error(err)
            logger.error("🔴 Bot is down.\nRestarting...")

asyncio.run(start_bot_loop())

asyncio.run(create_categories_if_not_exist())
