from uuid import uuid4

import asyncpg
import pytest
from fastapi import status

from app.projects.models import Project, ProjectIn
from app.projects.queries import (get_project_access, get_project_by_uuid,
                                  insert_project)
from app.tests.conftest import AuthClient
from app.users.models import User


@pytest.mark.anyio
async def test_insert_project(
    auth_client: AuthClient, user: User, db_conn: asyncpg.Connection
):
    project_in = ProjectIn(name="name", description="description")
    response = await auth_client.post("/projects/", user=user, json=project_in.dict())
    assert response.status_code == status.HTTP_200_OK

    project = Project(**response.json())
    assert project.name == project_in.name
    assert project.description == project_in.description

    project_db = await get_project_by_uuid(db_conn, project.uuid)
    assert project_db is not None
    assert project_db.dict() == project.dict()

    project_access = await get_project_access(db_conn, project.uuid, user)
    assert project_access is not None
    assert project_access.user_uuid == user.uuid
    assert project_access.project_uuid == project.uuid


@pytest.mark.anyio
async def test_projects_list(
    auth_client: AuthClient, user: User, db_conn: asyncpg.Connection
):
    project1 = Project(name="project1", description="", uuid=uuid4())
    project2 = Project(name="project2", description="", uuid=uuid4())
    await insert_project(db_conn, project1, user)
    await insert_project(db_conn, project2, user)

    response = await auth_client.get("/projects/", user=user)
    assert response.status_code == status.HTTP_200_OK
    projects = {p["name"]: Project(**p) for p in response.json()}
    assert len(projects) == 2

    assert project1.dict() == projects["project1"].dict()
    assert project2.dict() == projects["project2"].dict()
