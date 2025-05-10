from telebot import types

from src.application.states import State
from src.domain.users import User
from src.infrastructure.models import InternalModel

__all__ = (
    "CommandContract",
    "MessageContract",
    "CallbackQueryContract",
    "BaseContract",
)


class CommandContract(InternalModel):
    m: types.Message


class BaseContract(InternalModel):
    state: State
    user: User


class MessageContract(BaseContract):
    m: types.Message


class CallbackQueryContract(BaseContract):
    q: types.CallbackQuery
