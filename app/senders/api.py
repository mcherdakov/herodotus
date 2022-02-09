from uuid import UUID, uuid4

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.api import get_current_user
from app.db import get_db_connection
from app.projects.models import AccessType
from app.projects.queries import get_project_access
from app.senders.email import send_emails
from app.senders.models import (EmailConfIn, EmailConfInDb, Message,
                                TelegramConfIn, TelegramConfInDb)
from app.senders.queries import (get_project_confs, insert_email_conf,
                                 insert_telegram_conf)
from app.senders.telegram import send_telegram
from app.users.models import User

router = APIRouter(
    prefix="/senders",
    tags=["senders"],
)


async def check_project_permissions(
    conn: asyncpg.Connection, user: User, project_uuid: UUID
):
    access = await get_project_access(conn, project_uuid, user)
    if access is None or access.type != AccessType.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "reason": "not_enough_project_permissions",
                "message": "Project doesn't exist or you don't have enough permissions",
            },
        )


@router.get("/", response_model=list[EmailConfInDb | TelegramConfInDb])
async def list(
    project_uuid: UUID,
    current_user: User = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    await check_project_permissions(conn, current_user, project_uuid)
    return await get_project_confs(conn, project_uuid)


@router.post("/email/", response_model=EmailConfInDb)
async def create_email_conf(
    conf: EmailConfIn,
    current_user: User = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    await check_project_permissions(conn, current_user, conf.project_uuid)
    email_conf_db = EmailConfInDb(
        uuid=uuid4(), project_uuid=conf.project_uuid, email=conf.email
    )
    await insert_email_conf(conn, email_conf_db)

    return email_conf_db


@router.post("/telegram/", response_model=TelegramConfInDb)
async def create_telegram_conf(
    conf: TelegramConfIn,
    current_user: User = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    await check_project_permissions(conn, current_user, conf.project_uuid)
    telegram_conf_db = TelegramConfInDb(
        uuid=uuid4(), project_uuid=conf.project_uuid, chat_id=conf.chat_id
    )
    await insert_telegram_conf(conn, telegram_conf_db)

    return telegram_conf_db


@router.post("/send/")
async def send(
    message: Message,
    current_user: User = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    await check_project_permissions(conn, current_user, message.project_uuid)

    project_confs = await get_project_confs(conn, message.project_uuid)
    emails = []
    chat_ids = []
    for project_conf in project_confs:
        if isinstance(project_conf, EmailConfInDb):
            emails.append(project_conf.email)
        elif isinstance(project_conf, TelegramConfInDb):
            chat_ids.append(project_conf.chat_id)

    await send_emails(emails, message)
    await send_telegram(chat_ids, message)

    return {"message": "success"}
