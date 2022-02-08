"""
create project_access table
"""

from yoyo import step

__depends__ = {"20220208_01_ORjZ1-create-projects-table"}

steps = [
    step(
        """
        CREATE TABLE project_access (
            uuid UUID PRIMARY KEY,
            user_uuid UUID REFERENCES users ON DELETE CASCADE,
            project_uuid UUID REFERENCES projects ON DELETE CASCADE,
            type VARCHAR(64),
            UNIQUE (user_uuid, project_uuid)
        );
    """,
        rollback="""
        DROP TABLE project_access;
        """,
    )
]
