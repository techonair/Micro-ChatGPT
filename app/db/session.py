from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()


def _create_engine() -> AsyncEngine:
    if settings.database_url.startswith("sqlite"):
        return create_async_engine(
            settings.database_url,
            echo=False,
            poolclass=NullPool,
        )

    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=settings.sql_pool_size,
        max_overflow=settings.sql_max_overflow,
        pool_timeout=settings.sql_pool_timeout,
        pool_recycle=settings.sql_pool_recycle,
    )


engine = _create_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
