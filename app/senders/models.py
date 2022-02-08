from uuid import UUID
from pydantic import BaseModel, EmailStr

from app.projects.models import Project


class EmailConfBase(BaseModel):
    email: EmailStr


class EmailConfIn(EmailConfBase):
    project_uuid: UUID


class EmailConfInDb(EmailConfIn):
    uuid: UUID
