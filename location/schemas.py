
from pydantic import BaseModel


class LocationCreate(BaseModel):
    name: str
