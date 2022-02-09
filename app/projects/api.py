from uuid import uuid4

import asyncpg
from fastapi import APIRouter, Depends

from app.auth.api import get_current_user
from app.db import get_db_connection
from app.projects.models import Project, ProjectIn
from app.projects.queries import get_projects_for_user, insert_project
from app.users.models import User

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


@router.post("/", response_model=Project)
async def create(
    project: ProjectIn,
    current_user: User = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    project_db = Project(
        uuid=uuid4(), name=project.name, description=project.description
    )
    await insert_project(conn, project_db, current_user)

    return project_db


@router.get("/", response_model=list[Project])
async def list(
    current_user: User = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    return await get_projects_for_user(conn, current_user)
