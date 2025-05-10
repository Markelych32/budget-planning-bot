from sqlalchemy import Result, select

from src.domain.money.models import CurrencyInDB, CurrencyUncommited
from src.infrastructure.database import BaseCRUD, CurrencySchema
from src.infrastructure.errors import DatabaseError

__all__ = ("CurrenciesCRUD",)


class CurrenciesCRUD(BaseCRUD[CurrencySchema]):
    schema_class = CurrencySchema

    async def get(self, id_: int) -> CurrencyInDB:
        _schema = await self._get(key="id", value=id_)
        return CurrencyInDB.from_orm(_schema)

    async def exclude(self, id_: int) -> list[CurrencyInDB]:

        query = select(self.schema_class).where(self.schema_class.id != id_)

        try:
            result: Result = await self._session.execute(query)
            return [
                CurrencyInDB.from_orm(element)
                for element in result.scalars().all()
            ]
        except self._ERRORS:
            raise DatabaseError

    async def create(self, schema: CurrencyUncommited) -> CurrencyInDB:
        _schema: CurrencySchema = await self._save(
            CurrencySchema(**schema.dict())
        )

        return CurrencyInDB.from_orm(_schema)

    async def all(self) -> list[CurrencyInDB]:
        return [
            CurrencyInDB.from_orm(element) async for element in self._all()
        ]

    async def first(self) -> CurrencyInDB:
        _schema: CurrencySchema = await self._first()
        return CurrencyInDB.from_orm(_schema)

    async def last(self) -> CurrencyInDB:
        _schema: CurrencySchema = await self._last()
        return CurrencyInDB.from_orm(_schema)

    async def increase_equity(self, id_: int, value: int) -> CurrencyInDB:
        schema: CurrencySchema = await self._get(key="id", value=id_)
        updated_schema: CurrencySchema = await self._update(
            key="id",
            value=schema.id,
            payload={"equity": schema.equity + value},
        )

        return CurrencyInDB.from_orm(updated_schema)

    async def decrease_equity(self, id_: int, value: int) -> CurrencyInDB:
        schema: CurrencySchema = await self._get(key="id", value=id_)
        updated_schema: CurrencySchema = await self._update(
            key="id",
            value=schema.id,
            payload={"equity": schema.equity - value},
        )

        return CurrencyInDB.from_orm(updated_schema)
