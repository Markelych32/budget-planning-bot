import traceback
from functools import partial, wraps

from loguru import logger
from telebot import types

from src.application.messages import (
    DEFAULT_SEND_SETTINGS,
    CallbackMessages,
    Messages,
)
from src.infrastructure.errors import AccessForbiden, UserError
from src.keyboards.default import default_keyboard


def base_error_handler(coro):
    @wraps(coro)
    async def inner(m: types.Message | types.CallbackQuery, *args, **kwargs):
        regular_message = isinstance(m, types.Message)
        chat_id = m.chat.id if regular_message else m.message.chat.id

        error_message_coro = partial(
            Messages.send,
            chat_id=chat_id,
            keyboard=default_keyboard(),
            **DEFAULT_SEND_SETTINGS,
        )

        try:
            return await coro(m, *args, **kwargs)
        except AccessForbiden as error:
            return await error_message_coro(text=str(error))
        except UserError as error:
            if not regular_message:
                try:
                    return await CallbackMessages.edit(q=m, text=str(error))
                except Exception:
                    return await error_message_coro(text=str(error))
            else:
                return await error_message_coro(text=str(error))
        except Exception as error:
            traceback.print_exception(error)
            logger.error(error)
            text = r"Something went wrong ¯\_(ツ)_/¯"

            if not regular_message:
                try:
                    return await CallbackMessages.edit(q=m, text=text)
                except Exception:
                    return await error_message_coro(text=text)
            else:
                return await error_message_coro(text=text)

    return inner
