from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.users.models import User


class ProjectBase(BaseModel):
    name: str = Field(max_length=64)
    description: str


class ProjectIn(ProjectBase):
    pass


class Project(ProjectBase):
    uuid: UUID


class AccessType(str, Enum):
    owner = "owner"


class ProjectAccessBase(BaseModel):
    type: AccessType


class ProjectAccessIn(ProjectAccessBase):
    user_uuid: UUID
    project_uuid: UUID


class ProjectAccess(ProjectAccessBase):
    uuid: UUID
    user: User
    project: Project


class ProjectAccessDB(ProjectAccessIn):
    uuid: UUID
    user_uuid: UUID
    project_uuid: UUID
