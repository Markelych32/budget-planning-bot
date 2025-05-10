from src.domain.configurations.models import (
    ConfigurationInDB,
    ConfigurationUncommited,
)
from src.infrastructure.database import BaseCRUD, ConfigurationSchema

__all__ = ("ConfigurationsCRUD",)


class ConfigurationsCRUD(BaseCRUD[ConfigurationSchema]):
    schema_class = ConfigurationSchema

    async def create(
        self, schema: ConfigurationUncommited
    ) -> ConfigurationInDB:
        _schema: ConfigurationSchema = await self._save(
            ConfigurationSchema(**schema.dict())
        )

        return ConfigurationInDB.from_orm(_schema)

    async def update_default_currency(
        self, configuration_id: int, currency_id: int
    ) -> ConfigurationInDB:
        _schema = await self._update(
            "id", configuration_id, {"default_currency_id": currency_id}
        )
        return ConfigurationInDB.from_orm(_schema)

    async def update_costs_sources(
        self, configuration_id: int, payload: str
    ) -> ConfigurationInDB:
        _schema = await self._update(
            "id", configuration_id, {"costs_sources": payload}
        )
        return ConfigurationInDB.from_orm(_schema)

    async def update_incomes_sources(
        self, configuration_id: int, payload: str
    ) -> ConfigurationInDB:
        _schema = await self._update(
            "id", configuration_id, {"incomes_sources": payload}
        )
        return ConfigurationInDB.from_orm(_schema)

    async def update_ignore_categories(
        self, configuration_id: int, payload: str
    ) -> ConfigurationInDB:
        _schema = await self._update(
            "id", configuration_id, {"ignore_categories": payload}
        )
        return ConfigurationInDB.from_orm(_schema)

    async def update_number_of_dates(
        self, configuration_id: int, payload: int
    ) -> ConfigurationInDB:
        _schema = await self._update(
            "id", configuration_id, {"number_of_dates": payload}
        )
        return ConfigurationInDB.from_orm(_schema)
