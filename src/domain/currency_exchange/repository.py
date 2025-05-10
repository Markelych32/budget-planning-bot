from datetime import date

from sqlalchemy import Result, select
from sqlalchemy.orm import joinedload

from src.domain.currency_exchange.models import (
    CurrencyExchange,
    CurrencyExchangeInDB,
    CurrencyExchangeUncommited,
)
from src.domain.users import User
from src.infrastructure.database import BaseCRUD, CurrencyExchangeSchema
from src.infrastructure.errors import NotFound


class CurrencyExchangeCRUD(BaseCRUD):
    schema_class = CurrencyExchangeSchema

    async def get(self, id_: int) -> CurrencyExchange:
        query = (
            select(self.schema_class)
            .where(self.schema_class.id == id_)
            .options(
                joinedload(self.schema_class.source_currency),
                joinedload(self.schema_class.destination_currency),
            )
        )
        result: Result = await self._session.execute(query)

        if not (_schema := result.scalar_one_or_none()):
            raise NotFound

        return CurrencyExchange.from_orm(_schema)

    async def create(
        self, schema: CurrencyExchangeUncommited
    ) -> CurrencyExchangeInDB:
        _schema = await self._save(self.schema_class(**schema.dict()))
        return CurrencyExchangeInDB.from_orm(_schema)

    async def in_dates_range(
        self, start: date, end: date, user: User | None = None
    ) -> list[CurrencyExchange]:

        query = (
            select(self.schema_class)
            .filter(
                self.schema_class.date >= start, self.schema_class.date <= end
            )
            .options(
                joinedload(self.schema_class.source_currency),
                joinedload(self.schema_class.destination_currency),
            )
        )

        if user:
            query = query.filter(self.schema_class.user_id == user.id)

        result: Result = await self.execute(query)

        return [
            CurrencyExchange.from_orm(_schema)
            for _schema in result.scalars().all()
        ]
