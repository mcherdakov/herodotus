import asyncio

import asyncpg
import pytest
from httpx import AsyncClient

from app.auth.api import pwd_context
from app.db import Database, get_db_connection
from app.main import create_app
from app.users.models import User, UserIn


async def clean_db(conn: asyncpg.Connection):
    """
    Cleans up db before and after tests
    """
    await conn.execute(
        """
        TRUNCATE TABLE users CASCADE;
        TRUNCATE TABLE projects CASCADE;
    """
    )


async def setup_db():
    db = Database()
    await db.create_pool()
    assert db.pool is not None

    async with db.pool.acquire() as conn:
        await clean_db(conn)

    return db


@pytest.fixture(scope="session", autouse=True)
def setup_db_runner():
    db = asyncio.run(setup_db())
    yield db


@pytest.fixture()
async def db():
    db = Database()
    await db.create_pool()
    yield db
    await db.close()


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


@pytest.fixture()
async def user(client: AsyncClient):
    user = UserIn(username="test", password="pwd")
    rsp = await client.post(
        "/auth/register/",
        json=user.dict(),
    )
    return User(**rsp.json())


async def get_auth_headers(client: AsyncClient, user: UserIn):
    response = await client.post(
        "/auth/token/",
        data={"username": user.username, "password": user.password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return {
        "Authorization": "Bearer " + response.json()["access_token"],
    }


class AuthClient(AsyncClient):
    def __init__(self, *args, **kwargs):
        self.users: dict[str, str] = dict()  # username: token
        super().__init__(*args, **kwargs)

    async def _get_auth_token(self, user: User, password: str | None) -> str:
        response = await self.post(
            "/auth/token/",
            data={"username": user.username, "password": password or "pwd"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return "Bearer " + response.json()["access_token"]

    async def _update_request(
        self, user: User | None, password: str | None, request_kwargs
    ) -> None:
        if user is None:
            return

        if "headers" not in request_kwargs:
            request_kwargs["headers"] = dict()

        headers = request_kwargs["headers"]
        token = self.users.get(user.username)
        if token is None:
            token = await self._get_auth_token(user, password)
            self.users[user.username] = token

        headers["Authorization"] = token

    async def get(
        self, *args, user: User | None = None, password: str | None = None, **kwargs
    ):
        await self._update_request(user, password, kwargs)
        return await super().get(*args, **kwargs)

    async def post(
        self, *args, user: User | None = None, password: str | None = None, **kwargs
    ):
        await self._update_request(user, password, kwargs)
        return await super().post(*args, **kwargs)


@pytest.fixture()
async def auth_client(app):
    async with AuthClient(app=app, base_url="http://test") as ac:
        yield ac
