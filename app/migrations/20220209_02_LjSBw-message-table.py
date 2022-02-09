"""
message table
"""

from yoyo import step

__depends__ = {"20220209_01_mw9UO-telegram-conf-table"}

steps = [
    step(
        """
        CREATE TABLE messages (
            uuid UUID PRIMARY KEY,
            project_uuid UUID REFERENCES projects ON DELETE CASCADE,
            title TEXT,
            text TEXT,
            status VARCHAR(64),
            sync BOOLEAN,
            scheduled_ts INTEGER,
            attempts INTEGER
        )
        """,
        rollback="""
        DROP TABLE messages;
        """,
    )
]
