"""
message conf table
"""

from yoyo import step

__depends__ = {"20220209_02_LjSBw-message-table"}

steps = [
    step(
        """
        CREATE TABLE email_status (
            uuid UUID PRIMARY KEY,
            message_uuid UUID REFERENCES messages ON DELETE CASCADE,
            email_conf_uuid UUID REFERENCES email_conf ON DELETE CASCADE,
            status VARCHAR(64)
        );
        CREATE TABLE telegram_status (
            uuid UUID PRIMARY KEY,
            message_uuid UUID REFERENCES messages ON DELETE CASCADE,
            telegram_conf_uuid UUID REFERENCES telegram_conf ON DELETE CASCADE,
            status VARCHAR(64)
        );
    """,
        rollback="""
        DROP TABLE email_status, telegram_status;
        """,
    )
]
