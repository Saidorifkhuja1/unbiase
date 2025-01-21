from pydantic import BaseModel
from uuid import UUID

class StudentCreate(BaseModel):
    name: str
    lastname: str
    photo: str | None = None
    deterioration_id: UUID
    description: str | None = None
    working_place: str | None = None
    achievements: str | None = None

class StudentResponse(BaseModel):
    id: UUID
    name: str
    lastname: str
    photo: str | None
    deterioration_id: UUID
    description: str | None
    working_place: str | None
    achievements: str | None

    class Config:
        from_attributes = True
