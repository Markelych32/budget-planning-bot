from datetime import date

from src.domain.money import CurrencyInDB
from src.domain.money import services as money_services
from src.infrastructure.database.constants import IncomeSource
from src.infrastructure.models import InternalModel

__all__ = (
    "IncomeUncommited",
    "IncomeInDB",
    "Income",
)


class IncomeUncommited(InternalModel):
    name: str
    value: int
    source: IncomeSource
    date: date

    user_id: int
    currency_id: int


class IncomeInDB(IncomeUncommited):
    id: int


class Income(InternalModel):
    id: int
    name: str
    value: int
    source: IncomeSource
    date: date

    currency: CurrencyInDB

    def repr(self) -> str:
        return "\n".join(
            (
                f"Название 👉 {self.name}",
                f"Значение 👉 {money_services.repr_value(self.value)}"
                f"{self.currency.sign}",
                f"Источник 👉 {self.source}",
                f"Дата 👉 {self.date}",
            )
        )
