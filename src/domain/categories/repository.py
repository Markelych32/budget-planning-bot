from sqlalchemy import Result, select

from src.domain.categories.models import CategoryInDB, CategoryUncommited
from src.infrastructure.database import BaseCRUD, CategorySchema

__all__ = ("CategoriesCRUD",)


class CategoriesCRUD(BaseCRUD[CategorySchema]):
    schema_class = CategorySchema

    async def create(self, schema: CategoryUncommited) -> CategoryInDB:
        _schema: CategorySchema = await self._save(
            CategorySchema(**schema.dict())
        )

        return CategoryInDB.from_orm(_schema)

    async def all(self) -> list[CategoryInDB]:
        return [
            CategoryInDB.from_orm(_schema) async for _schema in self._all()
        ]

    async def exclude(self, ids: list[int]) -> list[CategoryInDB]:
        result: Result = await self._session.execute(
            select(self.schema_class).filter(
                self.schema_class.id.not_in(tuple(ids))
            )
        )

        return [
            CategoryInDB.from_orm(_schema)
            for _schema in result.scalars().all()
        ]

    async def get(self, id_: int) -> CategoryInDB:
        _schema = await self._get(key="id", value=id_)
        return CategoryInDB.from_orm(_schema)

    async def get_by_name(self, name: str) -> CategoryInDB:
        _schema = await self._get(key="name", value=name)
        return CategoryInDB.from_orm(_schema)
