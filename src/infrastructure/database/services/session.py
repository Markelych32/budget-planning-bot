from contextvars import ContextVar

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.settings import DATABASE_URL

__all__ = ("get_session", "engine", "CTX_SESSION")


engine: AsyncEngine = create_async_engine(
    DATABASE_URL, future=True, pool_pre_ping=True, echo=False
)


def get_session(engine: AsyncEngine | None = engine) -> AsyncSession:
    Session: async_sessionmaker[AsyncSession] = async_sessionmaker[
        AsyncSession
    ](engine, expire_on_commit=True, autoflush=False)

    return Session()


CTX_SESSION: ContextVar[AsyncSession] = ContextVar(
    "session", default=get_session()
)
