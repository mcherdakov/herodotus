from uuid import UUID, uuid4
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from app.projects.models import AccessType

from app.senders.models import EmailConfIn, EmailConfInDb
from app.db import get_db_connection
from app.auth.api import get_current_user
from app.senders.queries import insert_email_conf, get_project_confs
from app.users.models import User
from app.projects.queries import get_project_access


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


@router.get("/", response_model=list[EmailConfInDb])
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
