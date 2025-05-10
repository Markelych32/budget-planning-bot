from enum import StrEnum, auto

__all__ = ("IncomeSource",)


class IncomeSource(StrEnum):

    REVENUE = auto()
    OTHER = auto()
    GIFT = auto()
    DEBT = auto()
