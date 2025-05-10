from enum import StrEnum
from uuid import uuid4

__all__ = (
    "AnalyticsRootOption",
    "LevelOption",
    "DetailedOption",
    "BasicOption",
    "DetailAnalyticsCallbackOperation",
    "DatesRangeRegex",
)


class DatesRangeRegex(StrEnum):
    YEAR = r"\d{4}"
    YEARS = r"\d{4}-\d{4}"
    MONTH = r"\d{4}-(?:0?[1-9]|1[0-2])"
    MONTHS = r"\d{4}-(?:0?[1-9]|1[0-2])\s*-\s*\d{4}-(?:0?[1-9]|1[0-2])"
    DAYS = r"\d{4}-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12][0-9]|3[01])\s*-\s*\d{4}-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12][0-9]|3[01])"  # noqa


class AnalyticsRootOption(StrEnum):
    """The analytics submenu options enum."""

    PREVIOUS_MONTH = str(uuid4())
    THIS_MONTH = str(uuid4())
    BY_PATTERN = str(uuid4())

class LevelOption(StrEnum):
    SELECT_BASIC_LEVEL = str(uuid4())
    SELECT_DETAILED_LEVEL = str(uuid4())


class BasicOption(StrEnum):
    ONLY_MY = str(uuid4())
    ALL = str(uuid4())


class DetailedOption(StrEnum):
    ONLY_MY = str(uuid4())
    ONLY_INCOMES = str(uuid4())
    ONLY_CURRENCY_EXCHANGES = str(uuid4())
    BY_CATEGORY = str(uuid4())
    ALL = str(uuid4())

class DetailAnalyticsCallbackOperation(StrEnum):
    SELECT_CATEGORY = str(uuid4())


class BasicAnalyticsCallbackOperation(StrEnum):
    SELECT_CATEGORY = str(uuid4())
