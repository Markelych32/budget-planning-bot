from typing import Callable

from telebot import types

from src.domain.configurations import ConfigurationsCRUD
from src.domain.users import UsersCRUD
from src.handlers.router import any_message


async def test_trigger_start(bot_send_message_patch, create_message):

    message: types.Message = create_message(text="/start")
    await any_message(message)

    users_count: int = await UsersCRUD().count()
    configurations_count: int = await ConfigurationsCRUD().count()
    currencies_count: int = await ConfigurationsCRUD().count()

    assert users_count == 1
    assert configurations_count == 1
    assert currencies_count == 1
    assert bot_send_message_patch.call_count == 1


async def test_trigger_start_twice(
    bot_send_message_patch,
    create_message: Callable,
    default_users_raw,
):

    create_message(
        account_id=default_users_raw["marry"].account_id,
    )

    message: types.Message = create_message(text="/start")
    await any_message(message)
    await any_message(message)

    users_count: int = await UsersCRUD().count()
    configurations_count: int = await ConfigurationsCRUD().count()
    currencies_count: int = await ConfigurationsCRUD().count()

    assert users_count == 1
    assert configurations_count == 1
    assert currencies_count == 1
    assert bot_send_message_patch.call_count == 2


async def test_trigger_start_acl_error(
    bot_send_message_patch, create_message: Callable
):

    message: types.Message = create_message(text="/start", account_id=33)
    await any_message(message)

    users_count: int = await UsersCRUD().count()
    configurations_count: int = await ConfigurationsCRUD().count()
    currencies_count: int = await ConfigurationsCRUD().count()

    assert users_count == 0
    assert configurations_count == 0
    assert currencies_count == 0
    assert bot_send_message_patch.call_count == 1
