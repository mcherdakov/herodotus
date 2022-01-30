import os
from urllib.request import Request

import asyncpg
from fastapi import Request

from app.settings import settings


class Database:
    pool: asyncpg.Pool | None

    def __init__(self):
        self.pool = None

    async def create_pool(self):
        if self.pool is None:
            self.pool = await asyncpg.create_pool(dsn=settings.pg_dsn)

    async def close(self):
        if self.pool is not None:
            await self.pool.close()


async def get_db_connection(request: Request):
    pool: asyncpg.Pool = request.state.pool
    async with pool.acquire() as connection:
        yield connection
