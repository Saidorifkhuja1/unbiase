from fastapi import APIRouter, Depends,  status
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import LocationCreate
from database import get_db
from .models import Location
from user.models import Users
from dependency import get_current_staff_user




router = APIRouter()

@router.post("/locations_create", status_code=status.HTTP_201_CREATED)
async def create_location(
    location: LocationCreate,
    current_user: Users = Depends(get_current_staff_user),
    db: AsyncSession = Depends(get_db),
):
    new_location = Location(
        name=location.name,
        created_by_id=current_user.id,
    )

    db.add(new_location)
    await db.commit()
    await db.refresh(new_location)
    return {
        "id": str(new_location.id),
        "name": new_location.name,
        "created_by_id": str(new_location.created_by_id),
    }

