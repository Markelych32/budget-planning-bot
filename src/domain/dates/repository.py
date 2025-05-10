from contextlib import suppress
from datetime import date

from sqlalchemy import asc, desc, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.cache import Cache
from src.infrastructure.database import (
    CostSchema,
    CurrencyExchangeSchema,
    IncomeSchema,
)
from src.infrastructure.database.services.session import CTX_SESSION
from src.infrastructure.errors import NotFound

class DatesCRUD:

    CACHE_NAMESPACE = "dates"

    def __init__(self) -> None:
        self._session: AsyncSession = CTX_SESSION.get()

    async def first(self) -> date:
        with suppress(NotFound):
            return Cache.get(self.CACHE_NAMESPACE, "first")

        query = (
            select(CostSchema.date)
            .union(
                select(IncomeSchema.date), select(CurrencyExchangeSchema.date)
            )
            .order_by(asc("date"))
            .limit(1)
        )
        results: Result = await self._session.execute(query)

        if not (result := results.scalar_one_or_none()):
            raise NotFound

        return result

    async def last(self) -> date:
        with suppress(NotFound):
            return Cache.get(self.CACHE_NAMESPACE, "last")

        query = (
            select(CostSchema.date)
            .union(
                select(IncomeSchema.date), select(CurrencyExchangeSchema.date)
            )
            .order_by(desc("date"))
            .limit(1)
        )

        results: Result = await self._session.execute(query)

        if not (result := results.scalar_one_or_none()):
            raise NotFound

        return result
