from enum import StrEnum

__all__ = ("DateFormat",)


class DateFormat(StrEnum):
    FULL = "%Y-%m-%d"
    MONTHLY = "%Y-%m"
    ANNUALLY = "%Y"
    DAILY = "%d"
