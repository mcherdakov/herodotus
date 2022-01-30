from uuid import UUID

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(max_length=64)


class UserIn(UserBase):
    password: str


class User(UserBase):
    uuid: UUID


class UserInDB(User):
    password_hash: str
