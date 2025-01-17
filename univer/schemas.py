from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
from uuid import UUID


class UniversityCreate(BaseModel):
    name: str
    photo: Optional[HttpUrl]
    location_id: UUID
    category_id: UUID
    description: str
    video: Optional[HttpUrl]
    amount_of_students: int
    phone_number: str
    email: EmailStr
    webpage: HttpUrl


class UniversityResponse1(UniversityCreate):
    id: UUID
    created_by_id: UUID

    class Config:
        from_attributes = True


class UniversityResponse(BaseModel):
    id: Optional[str]
    name: Optional[str]
    photo: Optional[HttpUrl]
    location_id: Optional[str]
    category_id: Optional[str]
    description: Optional[str]
    video: Optional[HttpUrl]
    amount_of_students: Optional[int]
    phone_number: Optional[str]
    email: Optional[EmailStr]
    webpage: Optional[HttpUrl]
    created_by_id: Optional[str]

    class Config:
        from_attributes = True