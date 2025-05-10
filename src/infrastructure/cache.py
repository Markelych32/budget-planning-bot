from datetime import datetime, timedelta
from typing import Any

from pydantic import Field

from src.infrastructure.errors import NotFound
from src.infrastructure.models import InternalModel
from src.settings import CACHE_TTL


class _CacheEntry(InternalModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    ttl: timedelta
    instance: Any


class Cache:

    _DATA: dict[str, _CacheEntry] = {}

    @staticmethod
    def _build_key(namespace: str, key: Any) -> str:
        return f"{namespace}:{str(key)}"

    @classmethod
    def set(cls, namespace: str, key: str, instance: Any):
        _key = cls._build_key(namespace, key)
        entry = _CacheEntry(instance=instance, ttl=CACHE_TTL)

        cls._DATA[_key] = entry

    @classmethod
    def get(cls, namespace: str, key: Any) -> Any:
        _key = cls._build_key(namespace, key)

        try:
            entry: _CacheEntry = cls._DATA[_key]
        except KeyError:
            raise NotFound

        if (datetime.now() - entry.timestamp) > CACHE_TTL:
            raise NotFound

        return entry.instance


def cached(namespace: str, key: str):

    def wrapper(coro):
        async def inner(*args, **kwargs):
            try:
                result = Cache.get(namespace, key)
            except NotFound:
                result = await coro(*args, **kwargs)
                Cache.set(namespace=namespace, key=key, instance=result)

            return result

        return inner

    return wrapper
