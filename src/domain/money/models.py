from pydantic import Field

from src.infrastructure.models import InternalModel

__all__ = ("CurrencyUncommited", "CurrencyInDB")


class CurrencyUncommited(InternalModel):
    name: str = Field(max_length=3)
    sign: str = Field(max_length=1)


class CurrencyInDB(CurrencyUncommited):
    id: int
    equity: int
