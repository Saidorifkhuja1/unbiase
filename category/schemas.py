from pydantic import BaseModel, Field
from uuid import UUID

class CategoryCreate(BaseModel):
    name: str


class CategoryID(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True
