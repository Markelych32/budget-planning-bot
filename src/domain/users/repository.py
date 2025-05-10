from typing import Any

from sqlalchemy import Result, select
from sqlalchemy.orm import joinedload

from src.domain.users.models import User, UserInDB, UserUncommited
from src.infrastructure.database import (
    BaseCRUD,
    ConfigurationSchema,
    UserSchema,
)
from src.infrastructure.errors import NotFound

__all__ = ("UsersCRUD",)


class UsersCRUD(BaseCRUD[UserSchema]):
    schema_class = UserSchema

    async def create(self, schema: UserUncommited) -> UserInDB:
        _schema: UserSchema = await self._save(UserSchema(**schema.dict()))
        return UserInDB.from_orm(_schema)

    async def _get(self, key: str, value: Any) -> User:
        query = (
            select(self.schema_class)
            .where(getattr(self.schema_class, key) == value)
            .options(
                joinedload(self.schema_class.configuration).joinedload(
                    ConfigurationSchema.default_currency
                ),
            )
        )
        result: Result = await self._session.execute(query)
        if not (_schema := result.scalars().one_or_none()):
            raise NotFound

        return User.from_orm(_schema)

    async def get(self, id_: int) -> User:

        return await self._get(key="id", value=id_)

    async def by_account_id(self, id_: int) -> User:

        return await self._get(key="account_id", value=id_)
