from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str
    status: Optional[bool] = False


class UserAuth(BaseModel):
    email: EmailStr
    password: str


class UserPassword(BaseModel):
    old_password: str
    new_password: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
