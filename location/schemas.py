from pydantic import BaseModel, Field
from uuid import UUID





class RegionCreate(BaseModel):
    name: str

    class Config:
        from_attributes = True


class RegionUpdate(BaseModel):
    name: str

    class Config:
        from_attributes = True


class RegionResponse(BaseModel):
    id: UUID
    name: str
    created_by_id: UUID

    class Config:
        from_attributes = True




class LocationCreate(BaseModel):
    name: str
    region_id: UUID


class LocationUpdate(BaseModel):
    name: str
    region_id: UUID


class LocationID(BaseModel):
    id: UUID
    name: str
    region_id: UUID

    class Config:
        from_attributes = True