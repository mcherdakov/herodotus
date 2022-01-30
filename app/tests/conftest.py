import asyncio

import asyncpg
import pytest
from httpx import AsyncClient

from app.db import Database, get_db_connection
from app.main import create_app


async def clean_db(conn: asyncpg.Connection):
    """
    Cleans up db before and after tests
    """
    await conn.execute(
        """
        TRUNCATE TABLE users;
    """
    )


async def setup_db():
    db = Database()
    await db.create_pool()
    assert db.pool is not None

    async with db.pool.acquire() as conn:
        await clean_db(conn)

    return db


@pytest.fixture(scope="module", autouse=True)
def setup_db_runner():
    db = asyncio.run(setup_db())
    yield db


@pytest.fixture()
async def db():
    db = Database()
    await db.create_pool()
    return db


@pytest.fixture()
async def db_conn(db: Database):
    """
    Safe to use with other db-using fixtures,
    it will always be the same connection
    """
    assert db.pool is not None
    async with db.pool.acquire() as conn:
        # asyncpg handles nested transactions automatically
        transaction = conn.transaction()
        await transaction.start()
        yield conn
        await transaction.rollback()


@pytest.fixture()
async def app(db_conn: asyncpg.Connection, db: Database):
    # Get same db as used in db_conn so app won't create it's own pool.
    app = create_app(use_db=db)
    # We can't let app create it's own connections, because we need to
    # have control to rollback all changes
    app.dependency_overrides[get_db_connection] = lambda: db_conn
    return app


@pytest.fixture()
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def anyio_backend():
    return "asyncio"
