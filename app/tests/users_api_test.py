import asyncpg
import pytest
from fastapi import status
from httpx import AsyncClient

from app.users.models import UserIn
from app.users.queries import get_user_by_username


async def create_user(client: AsyncClient, user: UserIn):
    await client.post(
        "/auth/register/",
        json=user.dict(),
    )


async def get_auth_headers(client: AsyncClient, user: UserIn):
    response = await client.post(
        "/auth/token/",
        data={"username": user.username, "password": user.password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return {
        "Authorization": "Bearer " + response.json()["access_token"],
    }


@pytest.mark.anyio
async def test_me(client: AsyncClient, db_conn: asyncpg.Connection):
    user = UserIn(username="test", password="pwd")
    await create_user(client, user)

    user_db = await get_user_by_username(db_conn, username=user.username)
    assert user_db is not None

    response = await client.get(
        "/users/me/", headers=await get_auth_headers(client, user)
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["username"] == user_db.username
    assert data["uuid"] == str(user_db.uuid)
