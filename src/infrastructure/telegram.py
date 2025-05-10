import os
from contextlib import suppress
from importlib import import_module

from loguru import logger
from telebot.async_telebot import AsyncTeleBot

from src.settings import SRC_FOLDER, TELEGRAM_BOT_API_KEY


def create_bot():
    if not TELEGRAM_BOT_API_KEY:
        raise Exception("Telegram API key is not specified in the .env")

    return AsyncTeleBot(token=TELEGRAM_BOT_API_KEY)


def import_handlers():
    handlers_dir = SRC_FOLDER / "handlers"

    logger.debug("Loading handlers...")
    for app_name in os.listdir(handlers_dir):
        with suppress(ModuleNotFoundError, AttributeError):
            logger.success(f"{app_name} handler is loaded")
            import_module(f"src.handlers.{app_name}")


bot: AsyncTeleBot = create_bot()
