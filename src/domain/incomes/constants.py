from enum import StrEnum
from uuid import uuid4

from src.infrastructure.database import IncomeSource

__all__ = (
    "IncomeRootOption",
    "AddIncomeCallbackOperation",
    "DeleteIncomeCallbackOperation",
    "NOT_REAL_REVENUE_SOURCES",
)


NOT_REAL_REVENUE_SOURCES = {
    IncomeSource.GIFT,
    IncomeSource.DEBT,
}


class IncomeRootOption(StrEnum):

    ADD_INCOME = str(uuid4())
    DELETE_INCOME = str(uuid4())


class AddIncomeCallbackOperation(StrEnum):
    SELECT_CURRENCY = str(uuid4())
    SELECT_DATE = str(uuid4())
    SELECT_SOURCE = str(uuid4())
    SELECT_CONFIRMATION = str(uuid4())
    SELECT_YES = str(uuid4())
    SELECT_NO = str(uuid4())


class DeleteIncomeCallbackOperation(StrEnum):
    SELECT_MONTH = str(uuid4())
    SELECT_INCOME = str(uuid4())
    SELECT_CONFIRMATION = str(uuid4())
    SELECT_YES = str(uuid4())
    SELECT_NO = str(uuid4())
