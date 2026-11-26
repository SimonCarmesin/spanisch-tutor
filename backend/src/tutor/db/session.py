"""Engine und Session-Fabrik."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False: Objekte bleiben nach dem Commit lesbar (wichtig in async-Code)
    return async_sessionmaker(engine, expire_on_commit=False)
