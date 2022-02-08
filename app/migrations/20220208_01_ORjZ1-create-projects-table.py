"""
create projects table
"""

from yoyo import step

__depends__ = {"20220129_01_2A8cz-create-users-table"}

steps = [
    step(
        """
        CREATE TABLE projects (
            uuid UUID PRIMARY KEY,
            name VARCHAR(64),
            description TEXT
        )
    """,
        rollback="""
        DROP TABLE projects;
        """,
    )
]
