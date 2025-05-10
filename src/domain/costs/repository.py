import calendar
from datetime import date, datetime
from typing import AsyncGenerator

from sqlalchemy import Result, asc, select
from sqlalchemy.orm import joinedload

from src.domain.costs.models import Cost, CostInDB, CostUncommited
from src.domain.dates import DateFormat
from src.domain.users import User
from src.infrastructure.database import BaseCRUD, CostSchema
from src.infrastructure.errors import DatabaseError, NotFound

__all__ = ("CostsCRUD",)


class CostsCRUD(BaseCRUD[CostSchema]):
    schema_class = CostSchema

    async def get(self, id_: int) -> Cost:
        query = (
            select(self.schema_class)
            .where(self.schema_class.id == id_)
            .options(
                joinedload(self.schema_class.category),
                joinedload(self.schema_class.currency),
            )
        )
        result: Result = await self._session.execute(query)

        if not (_schema := result.scalar_one_or_none()):
            raise NotFound

        return Cost.from_orm(_schema)

    async def create(self, schema: CostUncommited) -> CostInDB:
        _schema: CostSchema = await self._save(CostSchema(**schema.dict()))
        return CostInDB.from_orm(_schema)

    async def by_user(self, user: User) -> AsyncGenerator[Cost, None]:
        query = (
            select(self.schema_class)
            .where(self.schema_class.user_id == user.id)
            .options(
                joinedload(self.schema_class.category),
                joinedload(self.schema_class.currency),
            )
        )

        result: Result = await self._session.execute(query)

        for _schema in result.scalars().all():
            yield Cost.from_orm(_schema)

    async def first(self) -> CostInDB:
        _schema: CostSchema = await self._first(by="date")
        return CostInDB.from_orm(_schema)

    async def last(self) -> CostInDB:
        _schema: CostSchema = await self._last(by="date")
        return CostInDB.from_orm(_schema)

    async def filter_for_delete(
        self, month: str, category_id: int
    ) -> AsyncGenerator[Cost, None]:

        first_date: date = datetime.strptime(month, DateFormat.MONTHLY).date()
        _, last_day = calendar.monthrange(first_date.year, first_date.month)
        last_date: date = date(
            year=first_date.year, month=first_date.month, day=last_day
        )

        query = (
            select(self.schema_class)
            .filter(
                self.schema_class.date >= first_date,
                self.schema_class.date <= last_date,
                self.schema_class.category_id == category_id,
            )
            .order_by(asc("date"))
            .options(
                joinedload(self.schema_class.category),
                joinedload(self.schema_class.currency),
            )
        )

        try:
            result: Result = await self._session.execute(query)
        except self._ERRORS:
            raise DatabaseError

        for element in result.scalars().all():
            yield Cost.from_orm(element)

    async def in_dates_range(
        self,
        start: date,
        end: date,
        user: User | None = None,
        category_id: int | None = None,
    ) -> list[Cost]:

        query = (
            select(self.schema_class)
            .filter(
                self.schema_class.date >= start, self.schema_class.date <= end
            )
            .options(
                joinedload(self.schema_class.category),
                joinedload(self.schema_class.currency),
            )
        )
        if user:
            query = query.filter(self.schema_class.user_id == user.id)
        if category_id:
            query = query.filter(self.schema_class.category_id == category_id)

        result: Result = await self.execute(query)

        return [Cost.from_orm(_schema) for _schema in result.scalars().all()]
