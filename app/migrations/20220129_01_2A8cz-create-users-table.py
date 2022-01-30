"""
create users table
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        """
        CREATE TABLE users (
            uuid UUID PRIMARY KEY,
            username VARCHAR(64) UNIQUE,
            password_hash VARCHAR(128)
        )
    """,
        rollback="""
        DROP TABLE users;
    """,
    )
]
