from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr


class EmailConfBase(BaseModel):
    email: EmailStr


class EmailConfIn(EmailConfBase):
    project_uuid: UUID


class EmailConfInDb(EmailConfIn):
    uuid: UUID


class TelegramConfBase(BaseModel):
    chat_id: int


class TelegramConfIn(TelegramConfBase):
    project_uuid: UUID


class TelegramConfInDb(TelegramConfIn):
    uuid: UUID


class MessageIn(BaseModel):
    project_uuid: UUID
    title: str
    text: str
    sync: bool


class MessageStatus(str, Enum):
    scheduled = "scheduled"
    sent = "sent"


class Message(MessageIn):
    uuid: UUID
    scheduled_ts: int
    status: MessageStatus
    attempts: int = 0


class StatusBase(BaseModel):
    uuid: UUID
    message_uuid: UUID
    status: MessageStatus


class EmailStatus(StatusBase):
    email_conf_uuid: UUID


class TelegramStatus(StatusBase):
    telegram_conf_uuid: UUID
