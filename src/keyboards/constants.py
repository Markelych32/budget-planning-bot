from enum import StrEnum
from typing import Iterable

from src.domain.analytics import BasicOption, DetailedOption
from src.infrastructure.database import IncomeSource
from src.keyboards.models import CallbackItem


class Commands(StrEnum):
    START = "/start"
    RESTART = "/restart"


class Menu(StrEnum):
    ADD_COST = "💵 Добавить расходы"
    EXCHANGE = "💱 Обмен"
    ANALYTICS = "📊 Аналитика"
    EQUITY = "🏦 Капитализация"
    INCOMES = "💰 Доходы"
    DELETE_COST = "🔥 Удалить расходы"
    CONFIGURATIONS = "🔧 Конфигурация"


class ConfirmationOption(StrEnum):
    YES = "✅ Да"
    NO = "❌ Нет"


INCOME_SOURCES_KEYBOARD_ELEMENTS: Iterable[CallbackItem] = (
    CallbackItem(name="💁 Другое", callback_data=IncomeSource.OTHER),
    CallbackItem(name="💰 Доход", callback_data=IncomeSource.REVENUE),
    CallbackItem(name="🪙 Долг", callback_data=IncomeSource.DEBT),
    CallbackItem(name="🎁 Подарок", callback_data=IncomeSource.GIFT),
)

ANALYTICS_BASIC_OPTIONS_KEYBOARD_ELEMENTS: list[CallbackItem] = [
    CallbackItem(name="🙋 Только я", callback_data=BasicOption.ONLY_MY),
    CallbackItem(name="🛒 Все", callback_data=BasicOption.ALL),
]

ANALYTICS_DETAILED_OPTIONS_KEYBOARD_ELEMENTS: list[CallbackItem] = [
    CallbackItem(name="♾️ Все", callback_data=DetailedOption.ALL),
    CallbackItem(name="🙋 Только я", callback_data=DetailedOption.ONLY_MY),
    CallbackItem(
        name="💱 Only exchanges",
        callback_data=DetailedOption.ONLY_CURRENCY_EXCHANGES,
    ),
    CallbackItem(
        name="💹 Только обмены", callback_data=DetailedOption.ONLY_INCOMES
    ),
    CallbackItem(
        name="🛍️ Траты по категориям", callback_data=DetailedOption.BY_CATEGORY
    ),
]
