import asyncio
import os
import sqlite3
import sys
import types
import uuid
from collections import deque
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy import text


# Register UUID adapter for sqlite3 so UUIDs are stored as strings, avoiding scientific notation float issues
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))

# Register dialect compilers for PostgreSQL-specific types on SQLite
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(PG_UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "TEXT"

# If aiosqlite is not installed, register a lightweight in-process async adapter for SQLite
try:
    import aiosqlite
except ImportError:
    class FakeCursor:
        def __init__(self, cur):
            self._cur = cur

        @property
        def description(self):
            return self._cur.description

        @property
        def rowcount(self):
            return self._cur.rowcount

        @property
        def lastrowid(self):
            return self._cur.lastrowid

        async def execute(self, *args, **kwargs):
            self._cur.execute(*args, **kwargs)
            return self

        async def executemany(self, *args, **kwargs):
            self._cur.executemany(*args, **kwargs)
            return self

        async def fetchall(self):
            return self._cur.fetchall()

        async def fetchone(self):
            return self._cur.fetchone()

        async def fetchmany(self, size=None):
            return self._cur.fetchmany(size)

        async def close(self):
            return self._cur.close()

    class FakeAioConn:
        def __init__(self, *args, **kwargs):
            self._conn = sqlite3.connect(*args, **kwargs)
            self.isolation_level = self._conn.isolation_level
            self._tx = asyncio.Queue()
            self.daemon = True

        def __await__(self):
            async def _ret():
                return self
            return _ret().__await__()

        def __getattr__(self, name):
            return getattr(self._conn, name)

        async def cursor(self):
            return FakeCursor(self._conn.cursor())

        async def execute(self, *args, **kwargs):
            cur = self._conn.cursor()
            cur.execute(*args, **kwargs)
            return FakeCursor(cur)

        async def commit(self):
            return self._conn.commit()

        async def rollback(self):
            return self._conn.rollback()

        async def close(self):
            return self._conn.close()

        async def create_function(self, *args, **kwargs):
            return self._conn.create_function(*args, **kwargs)

    def _connect(*args, **kwargs):
        return FakeAioConn(*args, **kwargs)

    aiosqlite_mod = types.ModuleType("aiosqlite")
    for k in [
        "DatabaseError", "Error", "IntegrityError", "NotSupportedError",
        "OperationalError", "ProgrammingError", "sqlite_version",
        "sqlite_version_info", "PARSE_COLNAMES", "PARSE_DECLTYPES", "Binary"
    ]:
        setattr(aiosqlite_mod, k, getattr(sqlite3, k, None))
    aiosqlite_mod.paramstyle = "qmark"
    aiosqlite_mod.connect = _connect
    sys.modules["aiosqlite"] = aiosqlite_mod

from app.core.database import Base
# Import all models so Base.metadata is fully populated
from app.models.models import (
    Category,
    Brand,
    Product,
    ProductImage,
    ProductVariant,
    Offer,
    EmiPlanRule,
    Quote,
    CheckoutIntent,
)

# Load .env from the service root so TEST_DATABASE_URL (and other vars) are available
# to os.getenv() calls in conftest, not just to pydantic-settings app code.
try:
    from dotenv import load_dotenv as _load_dotenv
    import pathlib as _pathlib
    _env_file = _pathlib.Path(__file__).parent.parent / ".env"
    if _env_file.exists():
        _load_dotenv(_env_file, override=False)  # Don't override vars already set in shell
except Exception:
    pass  # python-dotenv not installed — rely on shell environment

# Use SQLite in-memory with StaticPool for fast, isolated, reliable test runs across any environment,
# or Postgres if TEST_DATABASE_URL is explicitly set.
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

# Guard: refuse to run drop_all teardown on any real (non-SQLite) database.
# This prevents the test suite from destroying a seeded dev or staging database.
_IS_SQLITE = "sqlite" in TEST_DB_URL



@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False} if _IS_SQLITE else {},
        poolclass=StaticPool if _IS_SQLITE else None,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # Only drop tables when using SQLite in-memory.
    # On Postgres, we rely on per-test isolation (each test uses its own fresh rows).
    # drop_all on Postgres would destroy all application tables in whatever DB is pointed at.
    if _IS_SQLITE:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session_factory(test_engine):
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(test_session_factory):
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def reset_redis_client():
    """Reset the Redis client singleton between tests (handles per-test event-loop churn)."""
    from app.core.redis import close_redis
    await close_redis()
    yield
    await close_redis()


@pytest_asyncio.fixture(autouse=True)
async def flush_redis_keys():
    """Flush all Redis keys before each test so hardcoded idempotency keys don't collide
    across test runs. Skips gracefully when Redis is not available (local SQLite-only runs)."""
    try:
        from app.core.redis import get_redis
        r = await get_redis()
        await r.flushdb()
    except Exception:
        pass  # Redis unavailable — tests that need it will handle that themselves
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_db_between_tests(test_engine):
    """On Postgres: truncate all data before each test for clean isolation.
    On SQLite: drop_all/create_all per test_engine already handles isolation, so skip.
    TRUNCATE ... CASCADE handles FK ordering automatically."""
    if _IS_SQLITE:
        yield
        return
    async with test_engine.begin() as conn:
        await conn.execute(text(
            "TRUNCATE TABLE checkout_intents, quotes, product_images, "
            "product_variants, offers, emi_plan_rules, products, brands, categories "
            "RESTART IDENTITY CASCADE"
        ))
    yield
