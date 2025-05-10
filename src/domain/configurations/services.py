from src.domain.configurations.models import (
    ConfigurationInDB,
    ConfigurationUncommited,
)
from src.domain.configurations.repository import ConfigurationsCRUD
from src.domain.money import CurrenciesCRUD, CurrencyInDB


async def create_default(user_id: int) -> ConfigurationInDB:

    currency: CurrencyInDB = await CurrenciesCRUD().first()

    schema = ConfigurationUncommited(
        number_of_dates=3,
        costs_sources="",
        incomes_sources="",
        ignore_categories="",
        default_currency_id=currency.id,
        user_id=user_id,
    )

    return await ConfigurationsCRUD().create(schema)


def clean_sources_input(data: str) -> str:

    return ",".join(el.strip() for el in data.split(",") if el)


async def clean_ignore_categories(data: str) -> str:

    return ",".join(el.strip() for el in data.split(",") if el)
