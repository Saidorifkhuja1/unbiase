from pydantic import BaseModel, Field
from uuid import UUID

class LocationCreate(BaseModel):
    name: str


class LocationID(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True

