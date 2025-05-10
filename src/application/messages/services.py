import asyncio
from contextlib import suppress

from telebot import types

from src.application.messages.constants import DEFAULT_SEND_SETTINGS
from src.infrastructure.telegram import bot

__all__ = ("CallbackMessages", "Messages")


class CallbackMessages:

    @staticmethod
    async def edit(
        q: types.CallbackQuery,
        text: str,
        keyboard: types.InlineKeyboardMarkup | None = None,
    ):
        await bot.edit_message_text(
            chat_id=q.message.chat.id,
            message_id=q.message.id,
            text=text,
            reply_markup=keyboard,
            **DEFAULT_SEND_SETTINGS,
        )

    @staticmethod
    async def delete(q: types.CallbackQuery):
        await bot.delete_message(
            chat_id=q.message.chat.id, message_id=q.message.id
        )


class Messages:

    @staticmethod
    async def send(
        chat_id: int,
        text: str,
        keyboard: types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup,
        **kwargs,
    ) -> types.Message:

        telebot_payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": keyboard,
        }
        kwargs = DEFAULT_SEND_SETTINGS | kwargs | telebot_payload

        return await bot.send_message(**kwargs)

    @staticmethod
    async def _delete(chat_id: int, message_id: int) -> None:

        with suppress(Exception):
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

    @classmethod
    async def delete(cls, chat_id: int, *message_ids: int) -> None:
        tasks = [cls._delete(chat_id, id_) for id_ in message_ids]
        await asyncio.gather(*tasks)
