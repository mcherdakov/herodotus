"""
email conf table
"""

from yoyo import step

__depends__ = {"20220208_02_q0Jgz-create-project-access-table"}

steps = [
    step(
        """
        CREATE TABLE email_conf (
            uuid UUID PRIMARY KEY,
            project_uuid UUID REFERENCES projects ON DELETE CASCADE,
            email TEXT
        );
    """,
        rollback="""
        DROP TABLE email_conf;
        """,
    )
]
