from enum import StrEnum
from uuid import uuid4

__all__ = ("CurrencyExchangeCallbackOperation",)


class CurrencyExchangeCallbackOperation(StrEnum):
    SELECT_SRC_CURRENCY = str(uuid4())
    SELECT_DST_CURRENCY = str(uuid4())
    SELECT_DATE = str(uuid4())
    SELECT_CONFIRMATION = str(uuid4())
    SELECT_YES = str(uuid4())
    SELECT_NO = str(uuid4())
