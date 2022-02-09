"""
telegram conf table
"""

from yoyo import step

__depends__ = {"20220208_03_kuh3P-email-conf-table"}

steps = [
    step(
        """
        CREATE TABLE telegram_conf (
            uuid UUID PRIMARY KEY,
            project_uuid UUID REFERENCES projects ON DELETE CASCADE,
            chat_id INTEGER
        )
    """
    )
]
