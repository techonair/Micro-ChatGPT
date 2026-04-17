import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-32-bytes-minimum")
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("API_V1_PREFIX", "/api/v1")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def reset_database():
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM conversation_summaries"))
        await session.execute(text("DELETE FROM conversation_turns"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
