from time import time
from uuid import UUID, uuid4

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.api import get_current_user
from app.db import get_db_connection
from app.projects.models import AccessType
from app.projects.queries import get_project_access
from app.senders.email import send_emails
from app.senders.models import (EmailConfIn, EmailConfInDb, EmailStatus,
                                Message, MessageIn, MessageStatus,
                                TelegramConfIn, TelegramConfInDb,
                                TelegramStatus)
from app.senders.queries import (get_message, get_project_confs,
                                 get_statuses_for_message, insert_email_conf,
                                 insert_email_statuses, insert_message,
                                 insert_telegram_conf,
                                 insert_telegram_statuses)
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
async def list_confs(
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


async def send_sync(
    conn: asyncpg.Connection,
    project_confs: list[EmailConfInDb | TelegramConfInDb],
    message: Message,
):
    emails = []
    chat_ids = []
    email_statuses = []
    telegram_statuses = []
    for project_conf in project_confs:
        if isinstance(project_conf, EmailConfInDb):
            emails.append(project_conf.email)
            email_statuses.append(
                EmailStatus(
                    uuid=uuid4(),
                    message_uuid=message.uuid,
                    status=MessageStatus.sent,
                    email_conf_uuid=project_conf.uuid,
                )
            )
        elif isinstance(project_conf, TelegramConfInDb):
            chat_ids.append(project_conf.chat_id)
            telegram_statuses.append(
                TelegramStatus(
                    uuid=uuid4(),
                    message_uuid=message.uuid,
                    status=MessageStatus.sent,
                    telegram_conf_uuid=project_conf.uuid,
                ),
            )

    await send_emails(emails, message)
    await send_telegram(chat_ids, message)

    message.status = MessageStatus.sent
    await insert_message(conn, message)
    await insert_email_statuses(conn, email_statuses)
    await insert_telegram_statuses(conn, telegram_statuses)


async def send_async(
    conn: asyncpg.Connection,
    project_confs: list[EmailConfInDb | TelegramConfInDb],
    message: Message,
):
    email_statuses = []
    telegram_statuses = []
    for project_conf in project_confs:
        if isinstance(project_conf, EmailConfInDb):
            email_statuses.append(
                EmailStatus(
                    uuid=uuid4(),
                    message_uuid=message.uuid,
                    status=MessageStatus.scheduled,
                    email_conf_uuid=project_conf.uuid,
                )
            )
        elif isinstance(project_conf, TelegramConfInDb):
            telegram_statuses.append(
                TelegramStatus(
                    uuid=uuid4(),
                    message_uuid=message.uuid,
                    status=MessageStatus.scheduled,
                    telegram_conf_uuid=project_conf.uuid,
                ),
            )

    await insert_message(conn, message)
    await insert_email_statuses(conn, email_statuses)
    await insert_telegram_statuses(conn, telegram_statuses)


@router.post("/send/", response_model=Message)
async def send(
    message: MessageIn,
    current_user: User = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    await check_project_permissions(conn, current_user, message.project_uuid)
    project_confs = await get_project_confs(conn, message.project_uuid)
    message_db = Message(
        **message.dict(),
        uuid=uuid4(),
        scheduled_ts=int(time()),
        status=MessageStatus.scheduled,
    )

    if message.sync:
        await send_sync(conn, project_confs, message_db)
    else:
        await send_async(conn, project_confs, message_db)

    return message_db


class MessageResponse(BaseModel):
    message: Message
    statuses: list[EmailStatus | TelegramStatus]


@router.get("/message/", response_model=MessageResponse)
async def message(
    message_uuid: UUID,
    current_user: User = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    message = await get_message(conn, message_uuid)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await check_project_permissions(conn, current_user, message.project_uuid)

    return MessageResponse(
        message=message,
        statuses=await get_statuses_for_message(conn, message_uuid),
    )
