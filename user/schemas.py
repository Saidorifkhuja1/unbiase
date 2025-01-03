from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=64,
        description="Password should be between 8 and 64 characters.",
    )


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
