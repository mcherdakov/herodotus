import asyncio
from time import time

import asyncpg

from app.senders.email import send_emails
from app.senders.models import EmailStatus, Message, MessageStatus, TelegramStatus
from app.senders.queries import (
    get_email_conf,
    get_statuses_for_message,
    get_telegram_conf,
    get_unprocessed_messages,
    update_email_status,
    update_message,
    update_telegram_status,
)
from app.senders.telegram import send_telegram
from app.settings import settings

ITERATION_TIME_SECONDS = 10
INITIAL_TIMEOUT_SECONDS = 5


class Worker:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def process_status(
        self, status: EmailStatus | TelegramStatus, message: Message
    ) -> bool:
        if status.status == MessageStatus.sent:
            return True
        try:
            async with self.pool.acquire() as conn:
                if isinstance(status, EmailStatus):
                    email_conf = await get_email_conf(conn, status.email_conf_uuid)
                    if email_conf is None:
                        return True
                    await send_emails([email_conf.email], message)
                    status.status = MessageStatus.sent
                    await update_email_status(conn, status)
                elif isinstance(status, TelegramStatus):
                    telegram_conf = await get_telegram_conf(
                        conn, status.telegram_conf_uuid
                    )
                    if telegram_conf is None:
                        return True
                    await send_telegram([telegram_conf.chat_id], message)
                    status.status = MessageStatus.sent
                    await update_telegram_status(conn, status)
            return True
        except Exception:
            return False

    async def process_message(self, message: Message):
        async with self.pool.acquire() as conn:
            statuses = await get_statuses_for_message(conn, message.uuid)
            res = await asyncio.gather(
                *[self.process_status(status, message) for status in statuses]
            )
            if all(res):
                message.status = MessageStatus.sent
            else:
                message.scheduled_ts = int(time()) + INITIAL_TIMEOUT_SECONDS * (
                    2**message.attempts
                )
            message.attempts += 1

            await update_message(conn, message)

    async def process_messages(self, messages: list[Message]):
        await asyncio.gather(*[self.process_message(message) for message in messages])

    async def run_iteration(self):
        async with self.pool.acquire() as conn:
            messages = await get_unprocessed_messages(conn)

        await self.process_messages(messages)

    async def run(self):
        while True:
            await self.run_iteration()
            await asyncio.sleep(ITERATION_TIME_SECONDS)


async def create_pool() -> asyncpg.Pool:
    pool = await asyncpg.create_pool(dsn=settings.pg_dsn)
    if pool is None:
        raise Exception("Cannot create pool")
    return pool


async def main():
    pool = await create_pool()
    await Worker(pool).run()


if __name__ == "__main__":
    asyncio.run(main())
