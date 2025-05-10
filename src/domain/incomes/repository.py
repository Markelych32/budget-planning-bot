import calendar
from datetime import date, datetime
from typing import AsyncGenerator

from sqlalchemy import Result, asc, select
from sqlalchemy.orm import joinedload

from src.domain.dates import DateFormat
from src.domain.incomes.models import Income, IncomeInDB, IncomeUncommited
from src.domain.users import User
from src.infrastructure.database import BaseCRUD, IncomeSchema
from src.infrastructure.errors import DatabaseError, NotFound

__all__ = ("IncomesCRUD",)


class IncomesCRUD(BaseCRUD[IncomeSchema]):
    schema_class = IncomeSchema

    async def get(self, id_: int) -> Income:
        query = (
            select(self.schema_class)
            .where(self.schema_class.id == id_)
            .options(joinedload(self.schema_class.currency))
        )
        result: Result = await self._session.execute(query)

        if not (_schema := result.scalar_one_or_none()):
            raise NotFound

        return Income.from_orm(_schema)

    async def create(self, schema: IncomeUncommited) -> IncomeInDB:
        _schema: IncomeSchema = await self._save(IncomeSchema(**schema.dict()))
        return IncomeInDB.from_orm(_schema)

    async def by_user(self, user: User) -> AsyncGenerator[Income, None]:
        query = (
            select(self.schema_class)
            .where(self.schema_class.user_id == user.id)
            .options(joinedload(self.schema_class.currency))
        )

        result: Result = await self._session.execute(query)

        for _schema in result.scalars().all():
            yield Income.from_orm(_schema)

    async def first(self) -> IncomeInDB:
        _schema: IncomeSchema = await self._first(by="date")
        return IncomeInDB.from_orm(_schema)

    async def last(self) -> IncomeInDB:
        _schema: IncomeSchema = await self._last(by="date")
        return IncomeInDB.from_orm(_schema)

    async def filter_for_delete(
        self, month: str
    ) -> AsyncGenerator[Income, None]:

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
            )
            .order_by(asc("date"))
            .options(joinedload(self.schema_class.currency))
        )

        try:
            result: Result = await self._session.execute(query)
        except self._ERRORS:
            raise DatabaseError

        for element in result.scalars().all():
            yield Income.from_orm(element)

    async def in_dates_range(
        self, start: date, end: date, user: User | None = None
    ) -> list[Income]:

        query = (
            select(self.schema_class)
            .filter(
                self.schema_class.date >= start, self.schema_class.date <= end
            )
            .options(joinedload(self.schema_class.currency))
        )

        if user:
            query = query.filter(self.schema_class.user_id == user.id)

        result: Result = await self.execute(query)

        return [Income.from_orm(_schema) for _schema in result.scalars().all()]
