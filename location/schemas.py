from pydantic import BaseModel, Field
from uuid import UUID

class LocationCreate(BaseModel):
    name: str


class LocationID(BaseModel):
    id: UUID  # Add the ID field
    name: str

    class Config:
        orm_mode = True

