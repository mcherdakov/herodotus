from datetime import timedelta
from uuid import uuid4

import asyncpg
import pytest
from fastapi import HTTPException, status
from httpx import AsyncClient
from jose import jwt

from app.auth.api import (
    TokenData,
    authenticate_user,
    create_access_token,
    get_current_user,
    pwd_context,
    verify_password,
)
from app.settings import settings
from app.users.models import UserInDB
from app.users.queries import get_user_by_username, insert_user


def test_verify_password_correct():
    pwd = "password"
    hashed_pwd = pwd_context.hash(pwd)

    assert verify_password(pwd, hashed_pwd)


def test_verify_password_incorrect():
    pwd = "password"
    changed_hashed_pwd = pwd_context.hash("hello")

    assert not verify_password(pwd, changed_hashed_pwd)


@pytest.mark.anyio
async def test_authenticate_user(db_conn: asyncpg.Connection):
    user = UserInDB(
        username="test", uuid=uuid4(), password_hash=pwd_context.hash("pwd")
    )
    await insert_user(db_conn, user)

    auth_user = await authenticate_user(db_conn, "test", "pwd")
    assert auth_user is not None
    assert auth_user.dict() == user.dict()


@pytest.mark.anyio
async def test_authenticate_user_not_exists(db_conn: asyncpg.Connection):
    user = await authenticate_user(db_conn, "test", "pwd")
    assert user is None


def test_create_access_token():
    token = create_access_token(TokenData(username="test"), timedelta(days=1))
    payload = jwt.decode(token, settings.auth_key, settings.jwt_alogrithm)
    assert payload.get("sub") == "test"


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(db_conn: asyncpg.Connection):
    user = UserInDB(
        username="test", uuid=uuid4(), password_hash=pwd_context.hash("pwd")
    )
    await insert_user(db_conn, user)

    auth_user = await authenticate_user(db_conn, "test", "wrong_pwd")
    assert auth_user is None


@pytest.mark.anyio
async def test_get_current_user(db_conn: asyncpg.Connection):
    user = UserInDB(
        username="test", uuid=uuid4(), password_hash=pwd_context.hash("pwd")
    )
    await insert_user(db_conn, user)
    token = create_access_token(TokenData(username=user.username), timedelta(days=1))

    current_user = await get_current_user(token, db_conn)
    assert current_user is not None

    assert current_user.uuid == user.uuid


@pytest.mark.anyio
async def test_get_current_user_invalid_token(db_conn: asyncpg.Connection):
    user = UserInDB(
        username="test", uuid=uuid4(), password_hash=pwd_context.hash("pwd")
    )
    await insert_user(db_conn, user)

    with pytest.raises(HTTPException) as einfo:
        await get_current_user("not_valid_jwt", db_conn)

    assert einfo.value.detail["reason"] == "invalid_credentials"


@pytest.mark.anyio
async def test_get_current_user_not_exists(db_conn: asyncpg.Connection):
    token = create_access_token(TokenData(username="test"), timedelta(days=1))

    with pytest.raises(HTTPException) as einfo:
        await get_current_user(token, db_conn)

    assert einfo.value.detail["reason"] == "invalid_credentials"


@pytest.mark.anyio
async def test_register(client: AsyncClient, db_conn: asyncpg.Connection):
    response = await client.post(
        "/auth/register/", json={"username": "test", "password": "test"}
    )
    assert response.status_code == status.HTTP_200_OK
    response_body = response.json()
    assert response_body["username"] == "test"

    user = await get_user_by_username(db_conn, "test")
    assert user is not None
    assert user.username == "test"
    assert verify_password("test", user.password_hash)
    assert response_body["uuid"] == str(user.uuid)


@pytest.mark.anyio
async def test_register_duplicate_username(
    client: AsyncClient, db_conn: asyncpg.Connection
):
    user = UserInDB(username="test", uuid=uuid4(), password_hash="test")
    await insert_user(db_conn, user)

    response = await client.post(
        "/auth/register/", json={"username": "test", "password": "test"}
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"]["reason"] == "duplicate_username"


@pytest.mark.anyio
async def test_get_access_token(client: AsyncClient, db_conn: asyncpg.Connection):
    user = UserInDB(
        username="test", uuid=uuid4(), password_hash=pwd_context.hash("pwd")
    )
    await insert_user(db_conn, user)

    response = await client.post(
        "/auth/token/",
        data={"username": "test", "password": "pwd"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data.get("token_type") == "bearer"

    token = data.get("access_token")
    payload = jwt.decode(token, settings.auth_key, settings.jwt_alogrithm)
    assert payload.get("sub") == "test"


@pytest.mark.anyio
async def test_get_access_token_incorrect_credentials(
    client: AsyncClient, db_conn: asyncpg.Connection
):
    response = await client.post(
        "/auth/token/",
        data={"username": "test", "password": "pwd"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"]["reason"] == "incorrect_credentials"
