import asyncio
from typing import AsyncGenerator

from src.domain.dates import DateFormat
from src.domain.dates import services as dates_services
from src.domain.incomes.models import Income, IncomeInDB, IncomeUncommited
from src.domain.incomes.repository import IncomesCRUD
from src.domain.money import CurrenciesCRUD
from src.infrastructure.cache import Cache
from src.infrastructure.errors import NotFound


async def add(schema: IncomeUncommited) -> Income:

    income_in_db: IncomeInDB = await IncomesCRUD().create(schema)

    await CurrenciesCRUD().increase_equity(
        id_=income_in_db.currency_id, value=income_in_db.value
    )
    income: Income = await IncomesCRUD().get(id_=income_in_db.id)

    return income


async def delete(cost: Income):

    await CurrenciesCRUD().decrease_equity(
        id_=cost.currency.id, value=cost.value
    )
    await IncomesCRUD().delete(id_=cost.id)


async def get_last_months(
    limit: int | None = None,
) -> AsyncGenerator[str, None]:

    try:
        first = Cache.get(namespace="incomes", key="first_date")
        last = Cache.get(namespace="incomes", key="last_date")
    except NotFound:
        crud = IncomesCRUD()
        first, last = await asyncio.gather(crud.first(), crud.last())
        Cache.set(
            namespace="incomes",
            key="first_date",
            instance=first,
        )
        Cache.set(
            namespace="incomes",
            key="last_date",
            instance=last,
        )

    for index, item in enumerate(
        dates_services.represent_dates_range(
            first.date, last.date, DateFormat.MONTHLY
        )
    ):
        if limit and index > limit:
            break

        yield item
