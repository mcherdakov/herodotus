from uuid import uuid4

import asyncpg

from app.users.models import UserInDB


async def insert_user(conn: asyncpg.Connection, user: UserInDB):
    await conn.execute(
        "INSERT INTO users(uuid, username, password_hash) VALUES ($1, $2, $3)",
        user.uuid,
        user.username,
        user.password_hash,
    )


async def get_user_by_username(
    conn: asyncpg.Connection, username: str
) -> UserInDB | None:
    raw_user: asyncpg.Record = await conn.fetchrow(
        "SELECT * FROM users WHERE username = $1", username
    )
    if raw_user is None:
        return None

    return UserInDB(**raw_user)
