from enum import StrEnum
from uuid import uuid4

__all__ = ("ConfigurationRootOption", "ConfigurationUpdateOption")

INCOME_SOURCES_FALLBACK = ["Моя любимая работа"]
COST_SOURCES_FALLBACK = ["Еда", "Такси", "Вода", "Метро"]


class ConfigurationRootOption(StrEnum):

    GET_ALL = str(uuid4())
    UPDATE = str(uuid4())


class ConfigurationUpdateOption(StrEnum):
    NUMBER_OF_DATES = str(uuid4())
    COSTS_SOURCES = str(uuid4())
    INCOMES_SOURCES = str(uuid4())
    IGNORE_CATEGORIES = str(uuid4())
    DEFAULT_CURRENCY = str(uuid4())
    SELECT_CURRENCY = str(uuid4())
