from uuid import UUID
import asyncpg

from app.projects.models import Project
from app.senders.models import EmailConfInDb


async def insert_email_conf(conn: asyncpg.Connection, conf: EmailConfInDb):
    await conn.execute(
        "INSERT INTO email_conf(uuid, project_uuid, email) VALUES ($1, $2, $3)",
        conf.uuid,
        conf.project_uuid,
        conf.email,
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


async def get_project_confs(
    conn: asyncpg.Connection, project_uuid: UUID
) -> list[EmailConfInDb]:
    raw_email_confs: list[asyncpg.Record] = await conn.fetch(
        "SELECT * FROM email_conf WHERE project_uuid = $1", project_uuid
    )
    return [EmailConfInDb(**c) for c in raw_email_confs]
