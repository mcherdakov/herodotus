from uuid import UUID, uuid4
import asyncpg


from app.projects.models import Project, AccessType, ProjectAccess, ProjectAccessDB
from app.users.models import User


async def insert_project(
    conn: asyncpg.Connection, project: Project, user: User
) -> None:
    async with conn.transaction():
        await conn.execute(
            "INSERT INTO projects(uuid, name, description) VALUES ($1, $2, $3)",
            project.uuid,
            project.name,
            project.description,
        )

        await conn.execute(
            "INSERT INTO project_access(uuid, user_uuid, project_uuid, type) VALUES($1, $2, $3, $4)",
            uuid4(),
            user.uuid,
            project.uuid,
            AccessType.owner.value,
        )


async def get_project_by_uuid(conn: asyncpg.Connection, uuid: UUID) -> Project | None:
    raw_project: asyncpg.Record = await conn.fetchrow(
        "SELECT * FROM projects WHERE uuid = $1", uuid
    )
    if raw_project is None:
        return None

    return Project(**raw_project)


async def get_project_access(
    conn: asyncpg.Connection, project_uuid: UUID, user: User
) -> ProjectAccessDB | None:
    raw_access: asyncpg.Record = await conn.fetchrow(
        "SELECT * FROM project_access WHERE project_uuid = $1 AND user_uuid = $2",
        project_uuid,
        user.uuid,
    )
    if raw_access is None:
        return None

    return ProjectAccessDB(**raw_access)


async def get_projects_for_user(conn: asyncpg.Connection, user: User) -> list[Project]:
    raw: list[asyncpg.Record] = await conn.fetch(
        """
        SELECT projects.*
        FROM users 
            JOIN project_access ON project_access.user_uuid = users.uuid
            JOIN projects ON projects.uuid = project_access.project_uuid
        WHERE users.uuid = $1;
        """,
        user.uuid,
    )
    return [Project(**p_raw) for p_raw in raw]
