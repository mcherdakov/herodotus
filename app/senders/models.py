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


class Message(BaseModel):
    project_uuid: UUID
    title: str
    text: str
