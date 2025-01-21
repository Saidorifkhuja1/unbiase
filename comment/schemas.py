from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class CommentResponse(BaseModel):
    id: UUID
    body: str
    user_id: UUID
    university_id: UUID

    class Config:
        from_attributes = True