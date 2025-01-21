from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class CartBase(BaseModel):
    university_id: UUID

class CartResponse(CartBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True

class AddToCartRequest(CartBase):
    pass
