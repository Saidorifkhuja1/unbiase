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


class UniversityResponse1(BaseModel):
    id: str
    name: str
    photo: str
    # location_id: str
    # category_id: str
    # description: str
    # amount_of_students: int
    # phone_number: str
    # email: str
    # webpage: str
    # created_by_id: str
    # video: Optional[str] = None


    # id: UUID
    # created_by_id: UUID
    #
    # class Config:
    #     from_attributes = True


class UniversityResponse(BaseModel):
    id: Optional[UUID]
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





class DepartmentCreate(BaseModel):
    name: str
    photo: Optional[str] = None
    description: str
    university_id: str


class DepartmentResponse(BaseModel):
    id: str
    name: str
    photo: Optional[str] = None
    description: str
    university_id: str

    class Config:
        from_attributes = True


class DeteriorationBase(BaseModel):
    name: str
    department_id: str
    photo: Optional[str]
    description: str
    number_of_students: int


class DeteriorationCreate(DeteriorationBase):
    pass


class DeteriorationUpdate(DeteriorationBase):
    pass


class DeteriorationResponse(DeteriorationBase):
    id: str

    class Config:
        from_attributes = True