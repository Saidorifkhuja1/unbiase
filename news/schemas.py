from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class NewsCreate(BaseModel):
    title: str
    photo: Optional[str] = None
    body: str

    class Config:
        from_attributes = True

class NewsResponse(NewsCreate):
    id: UUID
    created_by_id: UUID

    class Config:
        from_attributes = True

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    photo: Optional[str] = None
    body: Optional[str] = None

    class Config:
        from_attributes = True
