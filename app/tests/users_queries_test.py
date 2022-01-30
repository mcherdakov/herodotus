from multiprocessing.connection import Connection
from uuid import uuid4

import asyncpg
import pytest

from app.users.models import UserInDB
from app.users.queries import get_user_by_username, insert_user


@pytest.mark.anyio
async def test_insert_user(db_conn: asyncpg.Connection):
    user = UserInDB(username="test", password_hash="test", uuid=uuid4())
    await insert_user(db_conn, user)

    user_db = await get_user_by_username(db_conn, user.username)
    assert user_db is not None
    assert user.dict() == user_db.dict()


@pytest.mark.anyio
async def test_insert_user_duplicate_username(db_conn: asyncpg.Connection):
    user = UserInDB(username="test", password_hash="test", uuid=uuid4())
    await insert_user(db_conn, user)

    with pytest.raises(asyncpg.UniqueViolationError):
        await insert_user(db_conn, user)


@pytest.mark.anyio
async def test_get_user_by_username_not_exists(db_conn: asyncpg.Connection):
    user = await get_user_by_username(db_conn, "test")
    assert user is None
