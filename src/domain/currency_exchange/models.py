from datetime import date

from src.domain.money import CurrencyInDB
from src.domain.money import services as money_services
from src.infrastructure.models import InternalModel

__all__ = (
    "CurrencyExchangeUncommited",
    "CurrencyExchangeInDB",
    "CurrencyExchange",
)


class CurrencyExchangeUncommited(InternalModel):
    source_value: int
    destination_value: int
    date: date
    source_currency_id: int
    destination_currency_id: int
    user_id: int


class CurrencyExchangeInDB(CurrencyExchangeUncommited):
    id: int


class CurrencyExchange(InternalModel):
    source_value: int
    destination_value: int
    date: date
    user_id: int

    source_currency: CurrencyInDB
    destination_currency: CurrencyInDB

    def repr(self) -> str:
        source_value = "".join(
            (
                money_services.repr_value(self.source_value),
                self.source_currency.sign,
            )
        )
        destination_value = "".join(
            (
                money_services.repr_value(self.destination_value),
                self.destination_currency.sign,
            )
        )
        return "\n".join(
            (
                f"Исходный счёт 👉 {source_value}",
                f"Целевой счёт 👉 {destination_value}",
                f"Дата 👉 {self.date}",
            )
        )
