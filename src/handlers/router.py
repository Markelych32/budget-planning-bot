from typing import Callable

from telebot import types

from src.application.authentication import acl
from src.application.errors import base_error_handler
from src.application.messages import (
    CallbackMessages,
    CallbackQueryContract,
    CommandContract,
    MessageContract,
    Messages,
)
from src.application.states import State
from src.domain.users import User, UsersCRUD
from src.handlers.add_cost import add_cost_callback
from src.handlers.analytics import analytics_general_menu_callback
from src.handlers.commands import restart as restart_command_callback
from src.handlers.commands import start as start_command_callback
from src.handlers.configurations import configurations_general_callback
from src.handlers.currency_exchange import currency_exchange_callback
from src.handlers.delete_cost import delete_cost_callback
from src.handlers.equity import equity_callback
from src.handlers.incomes import incomes_general_menu_callback
from src.infrastructure.errors import AccessForbiden, NotFound
from src.infrastructure.telegram import bot
from src.keyboards.constants import Commands, Menu
from src.keyboards.default import default_keyboard

__all__ = ("any_message", "any_callback_qeury")


ROOT_COMMANDS_MAPPER: dict[str, Callable] = {
    Commands.START: start_command_callback,
}
ROOT_MESSAGES_MAPPER: dict[str, Callable] = {
    Menu.ADD_COST: add_cost_callback,
    Menu.DELETE_COST: delete_cost_callback,
    Menu.INCOMES: incomes_general_menu_callback,
    Menu.EQUITY: equity_callback,
    Menu.EXCHANGE: currency_exchange_callback,
    Menu.ANALYTICS: analytics_general_menu_callback,
    Menu.CONFIGURATIONS: configurations_general_callback,
}


async def _get_user(account_id: int) -> User:
    try:
        return await UsersCRUD().by_account_id(account_id)
    except NotFound:
        raise AccessForbiden


@bot.message_handler(func=lambda _: True)
@base_error_handler
@acl
async def any_message(m: types.Message):

    assert m.text

    if _callback := ROOT_COMMANDS_MAPPER.get(m.text):
        return await _callback(CommandContract(m=m))

    user: User = await _get_user(m.from_user.id)
    state = State(user.id)

    if m.text == Commands.RESTART:
        return await restart_command_callback(
            MessageContract(m=m, state=state, user=user)
        )

    if _callback := ROOT_MESSAGES_MAPPER.get(m.text):
        return await _callback(MessageContract(m=m, state=state, user=user))

    if not (_callback := state.next_callback):
        return await Messages.send(
            chat_id=user.chat_id,
            text="Пожалуйста, воспользуйтесь клавиатурой",
            keyboard=default_keyboard(),
        )

    state.next_callback = None

    return await _callback(MessageContract(m=m, state=state, user=user))


@bot.callback_query_handler(func=lambda c: c.data)
@base_error_handler
@acl
async def any_callback_qeury(q: types.CallbackQuery):
    user: User = await _get_user(q.from_user.id)
    state = State(user.id)

    if not (_callback := state.next_callback):
        return await CallbackMessages.edit(
            q=q, text="Это сообщение устарело"
        )

    state.next_callback = None

    return await _callback(CallbackQueryContract(q=q, state=state, user=user))
