from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_path: Path) -> AsyncEngine:
    # Download workers write progress concurrently; wait for SQLite's lock instead of failing.
    return create_async_engine(f"sqlite+aiosqlite:///{database_path}", connect_args={"timeout": 30})


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
