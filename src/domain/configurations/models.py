from src.domain.configurations.constants import (
    COST_SOURCES_FALLBACK,
    INCOME_SOURCES_FALLBACK,
)
from src.domain.money import CurrencyInDB
from src.infrastructure.models import InternalModel

__all__ = ("ConfigurationUncommited", "ConfigurationInDB", "Configuration")


class ConfigurationUncommited(InternalModel):
    number_of_dates: int
    costs_sources: str
    incomes_sources: str
    ignore_categories: str
    default_currency_id: int
    user_id: int


class ConfigurationInDB(ConfigurationUncommited):
    id: int


class Configuration(InternalModel):
    id: int
    number_of_dates: int
    costs_sources: str
    incomes_sources: str
    ignore_categories: str
    default_currency: CurrencyInDB

    @property
    def costs_sources_items(self) -> list[str]:
        return [
            el for el in self.costs_sources.split(",") if el
        ] or COST_SOURCES_FALLBACK

    @property
    def incomes_sources_items(self) -> list[str]:
        return [
            el for el in self.incomes_sources.split(",") if el
        ] or INCOME_SOURCES_FALLBACK

    @property
    def ignore_categories_items(self) -> list[int]:
        return [int(el) for el in self.ignore_categories.split(",") if el]

    def represent(self) -> str:
        costs_sources_message = ", ".join(
            (s for s in self.costs_sources_items)
        )
        incomes_sources_message = ", ".join(
            (i for i in self.incomes_sources_items)
        )

        ignore_categories_message = ", ".join(
            (str(i) for i in self.ignore_categories_items)
        )
        return "\n\n".join(
            (
                "<b>🔧 Текущая конфигурация</b>\n",
                f"Кол-во дней для выбора на клавиатуре 👉 {self.number_of_dates}",
                f"Основные источники расходов 👉 {costs_sources_message}",
                f"Основные источники доходов 👉 {incomes_sources_message}",
                f"Игнорировать категории 👉 {ignore_categories_message}",
                f"Валюта по умолчанию  👉 {self.default_currency.name}",
            )
        )
