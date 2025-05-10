from functools import wraps
from typing import Callable, Coroutine

from telebot import types

from src.infrastructure.errors import AccessForbiden
from src.settings import USERS_WHITE_LIST


def acl(coro: Callable):
    @wraps(coro)
    async def inner(m: types.Message | types.CallbackQuery) -> Coroutine:
        if isinstance(m, types.Message) and not m.text:
            raise Exception("You can not send empty messages")

        if m.from_user.id not in USERS_WHITE_LIST:
            raise AccessForbiden

        return await coro(m)

    return inner
