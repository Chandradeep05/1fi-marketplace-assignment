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

# Use SQLite in-memory with StaticPool for fast, isolated, reliable test runs across any environment,
# or Postgres if TEST_DATABASE_URL is explicitly set.
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DB_URL else {},
        poolclass=StaticPool if "sqlite" in TEST_DB_URL else None,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
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
