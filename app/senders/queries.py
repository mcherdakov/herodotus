from time import time
from uuid import UUID

import asyncpg

from app.senders.models import (EmailConfInDb, EmailStatus, Message,
                                MessageStatus, TelegramConfInDb,
                                TelegramStatus)


async def insert_email_conf(conn: asyncpg.Connection, conf: EmailConfInDb):
    await conn.execute(
        "INSERT INTO email_conf(uuid, project_uuid, email) VALUES ($1, $2, $3)",
        conf.uuid,
        conf.project_uuid,
        conf.email,
    )


async def insert_telegram_conf(conn: asyncpg.Connection, conf: TelegramConfInDb):
    await conn.execute(
        "INSERT INTO telegram_conf(uuid, project_uuid, chat_id) VALUES ($1, $2, $3)",
        conf.uuid,
        conf.project_uuid,
        conf.chat_id,
    )


async def get_email_conf(
    conn: asyncpg.Connection, conf_uuid: UUID
) -> EmailConfInDb | None:
    raw: asyncpg.Record = await conn.fetchrow(
        "SELECT * FROM email_conf WHERE uuid = $1",
        conf_uuid,
    )
    if raw is None:
        return None

    return EmailConfInDb(**raw)


async def get_telegram_conf(
    conn: asyncpg.Connection, conf_uuid: UUID
) -> TelegramConfInDb | None:
    raw: asyncpg.Record = await conn.fetchrow(
        "SELECT * FROM telegram_conf WHERE uuid = $1",
        conf_uuid,
    )
    if raw is None:
        return None

    return TelegramConfInDb(**raw)


async def get_project_confs(
    conn: asyncpg.Connection, project_uuid: UUID
) -> list[EmailConfInDb | TelegramConfInDb]:
    raw_email_confs: list[asyncpg.Record] = await conn.fetch(
        "SELECT * FROM email_conf WHERE project_uuid = $1", project_uuid
    )
    email_confs = [EmailConfInDb(**c) for c in raw_email_confs]

    raw_telegram_confs: list[asyncpg.Record] = await conn.fetch(
        "SELECT * FROM telegram_conf WHERE project_uuid = $1", project_uuid
    )
    telegram_confs = [TelegramConfInDb(**c) for c in raw_telegram_confs]

    return [*email_confs, *telegram_confs]


async def insert_message(conn: asyncpg.Connection, message: Message):
    await conn.execute(
        """
        INSERT INTO messages(uuid, project_uuid, title, text, sync, scheduled_ts, status, attempts)
            VALUES($1, $2, $3, $4, $5, $6, $7, $8);
        """,
        message.uuid,
        message.project_uuid,
        message.title,
        message.text,
        message.sync,
        message.scheduled_ts,
        message.status,
        message.attempts,
    )


async def get_message(conn: asyncpg.Connection, message_uuid: UUID) -> Message | None:
    raw: asyncpg.Record = await conn.fetchrow(
        "SELECT * FROM messages WHERE uuid = $1", message_uuid
    )
    if raw is None:
        return None

    return Message(**raw)


async def insert_email_statuses(
    conn: asyncpg.Connection, email_statuses: list[EmailStatus]
):
    await conn.executemany(
        """
        INSERT INTO email_status(uuid, message_uuid, email_conf_uuid, status)
            VALUES ($1, $2, $3, $4);
        """,
        [
            (
                email_status.uuid,
                email_status.message_uuid,
                email_status.email_conf_uuid,
                email_status.status,
            )
            for email_status in email_statuses
        ],
    )


async def update_email_status(conn: asyncpg.Connection, email_status: EmailStatus):
    await conn.execute(
        """
        UPDATE email_status SET (message_uuid, email_conf_uuid, status) = 
            ($1, $2, $3)
        WHERE uuid = $4;
        """,
        email_status.message_uuid,
        email_status.email_conf_uuid,
        email_status.status,
        email_status.uuid,
    )


async def insert_telegram_statuses(
    conn: asyncpg.Connection, telegram_statuses: list[TelegramStatus]
):
    await conn.executemany(
        """
        INSERT INTO telegram_status(uuid, message_uuid, telegram_conf_uuid, status)
            VALUES ($1, $2, $3, $4);
        """,
        [
            (
                telegram_status.uuid,
                telegram_status.message_uuid,
                telegram_status.telegram_conf_uuid,
                telegram_status.status,
            )
            for telegram_status in telegram_statuses
        ],
    )


async def update_telegram_status(
    conn: asyncpg.Connection, telegram_status: TelegramStatus
):
    await conn.execute(
        """
        UPDATE telegram_status SET (message_uuid, telegram_conf_uuid, status) = 
            ($1, $2, $3)
        WHERE uuid = $4;
        """,
        telegram_status.message_uuid,
        telegram_status.telegram_conf_uuid,
        telegram_status.status,
        telegram_status.uuid,
    )


async def get_statuses_for_message(
    conn: asyncpg.Connection, message_uuid: UUID
) -> list[EmailStatus | TelegramStatus]:
    email_raw = await conn.fetch(
        "SELECT * FROM email_status WHERE message_uuid = $1", message_uuid
    )
    email_statuses = [EmailStatus(**s) for s in email_raw]

    telegram_raw = await conn.fetch(
        "SELECT * FROM telegram_status WHERE message_uuid = $1", message_uuid
    )
    telegram_statuses = [TelegramStatus(**s) for s in telegram_raw]

    return [*email_statuses, *telegram_statuses]


async def get_unprocessed_messages(
    conn: asyncpg.Connection, limit: int = 100
) -> list[Message]:
    raw = await conn.fetch(
        """
        SELECT * FROM messages
            WHERE sync = false AND status = $1 AND scheduled_ts <= $2
        ORDER BY scheduled_ts
        LIMIT $3
        """,
        MessageStatus.scheduled,
        time(),
        limit,
    )

    return [Message(**m) for m in raw]


async def update_message(conn: asyncpg.Connection, message: Message):
    await conn.execute(
        """
        UPDATE messages SET (project_uuid, title, text, sync, scheduled_ts, status) = 
            ($1, $2, $3, $4, $5, $6)
        WHERE uuid = $7;
        """,
        message.project_uuid,
        message.title,
        message.text,
        message.sync,
        message.scheduled_ts,
        message.status,
        message.uuid,
    )
