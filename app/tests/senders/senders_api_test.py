from uuid import uuid4

import asyncpg
import pytest
from fastapi import status
from pydantic import EmailStr

from app.projects.models import Project
from app.projects.queries import insert_project
from app.senders.models import EmailConfIn, EmailConfInDb
from app.senders.queries import get_email_conf, insert_email_conf
from app.tests.conftest import AuthClient
from app.users.models import User


@pytest.mark.anyio
async def test_create_email_conf(
    auth_client: AuthClient, user: User, db_conn: asyncpg.Connection
):
    project = Project(name="project", description="", uuid=uuid4())
    await insert_project(db_conn, project, user)
    response = await auth_client.post(
        "/senders/email/",
        user=user,
        json={"email": "test@test.ru", "project_uuid": str(project.uuid)},
    )
    assert response.status_code == status.HTTP_200_OK
    email_conf = EmailConfInDb(**response.json())

    email_conf_db = await get_email_conf(db_conn, email_conf.uuid)
    assert email_conf_db is not None

    assert email_conf.dict() == email_conf_db.dict()


@pytest.mark.anyio
async def test_create_email_conf_permission(
    auth_client: AuthClient, user: User, db_conn: asyncpg.Connection
):
    response = await auth_client.post(
        "/senders/email/",
        user=user,
        json={"email": "test@test.ru", "project_uuid": str(uuid4())},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_list_confs(
    auth_client: AuthClient, user: User, db_conn: asyncpg.Connection
):
    project = Project(name="project", description="", uuid=uuid4())
    await insert_project(db_conn, project, user)
    email_conf = EmailConfInDb(
        email=EmailStr("test@test.ru"), project_uuid=project.uuid, uuid=uuid4()
    )
    await insert_email_conf(db_conn, email_conf)

    response = await auth_client.get(
        f"/senders/?project_uuid={project.uuid}", user=user
    )
    assert response.status_code == status.HTTP_200_OK

    assert [EmailConfInDb(**s) for s in response.json()] == [email_conf]
