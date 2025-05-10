import asyncio
from typing import AsyncGenerator

from src.domain.costs.models import Cost, CostInDB, CostUncommited
from src.domain.costs.repository import CostsCRUD
from src.domain.dates import DateFormat
from src.domain.dates import services as dates_services
from src.domain.money import CurrenciesCRUD
from src.infrastructure.cache import Cache
from src.infrastructure.errors import NotFound


async def add(schema: CostUncommited) -> Cost:

    cost_in_db: CostInDB = await CostsCRUD().create(schema)

    await CurrenciesCRUD().decrease_equity(
        id_=cost_in_db.currency_id, value=cost_in_db.value
    )
    cost: Cost = await CostsCRUD().get(id_=cost_in_db.id)

    return cost


async def delete(cost: Cost):

    await CurrenciesCRUD().increase_equity(
        id_=cost.currency.id, value=cost.value
    )
    await CostsCRUD().delete(id_=cost.id)


async def get_last_months(
    limit: int | None = None,
) -> AsyncGenerator[str, None]:

    try:
        first = Cache.get(namespace="costs", key="first_date")
        last = Cache.get(namespace="costs", key="last_date")
    except NotFound:
        crud = CostsCRUD()
        first, last = await asyncio.gather(crud.first(), crud.last())
        Cache.set(
            namespace="costs",
            key="first_date",
            instance=first,
        )
        Cache.set(
            namespace="costs",
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
