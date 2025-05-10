from datetime import date
from enum import StrEnum
from uuid import uuid4

from src.domain.categories import CategoryInDB
from src.domain.money import CurrencyInDB
from src.domain.money import services as money_services
from src.infrastructure.models import InternalModel

__all__ = (
    "CostUncommited",
    "CostInDB",
    "Cost",
    "AddCostCallbackOperation",
    "DeleteCostCallbackOperation",
)


class CostUncommited(InternalModel):
    name: str
    value: int
    date: date

    user_id: int
    category_id: int
    currency_id: int


class CostInDB(CostUncommited):
    id: int


class Cost(InternalModel):
    id: int
    name: str
    value: int
    date: date

    category: CategoryInDB
    currency: CurrencyInDB

    def repr(self) -> str:
        return "\n".join(
            (
                f"Название 👉 {self.name}",
                f"Значение 👉 {money_services.repr_value(self.value)}"
                f"{self.currency.sign}",
                f"Категория 👉 {self.category.name}",
                f"Дата 👉 {self.date}",
            )
        )

class AddCostCallbackOperation(StrEnum):
    SELECT_CATEGORY = str(uuid4())
    SELECT_DATE = str(uuid4())
    SELECT_CONFIRMATION = str(uuid4())
    SELECT_YES = str(uuid4())
    SELECT_NO = str(uuid4())


class DeleteCostCallbackOperation(StrEnum):
    SELECT_MONTH = str(uuid4())
    SELECT_CATEGORY = str(uuid4())
    SELECT_COST = str(uuid4())
    SELECT_CONFIRMATION = str(uuid4())
    SELECT_YES = str(uuid4())
    SELECT_NO = str(uuid4())
