from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from user.models import Users
from .schemas import LocationResponse, LocationCreate
from .models import Location
from database import get_db
from dependencies import  get_current_user

router = APIRouter()

@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Endpoint to create a new location. Only staff users are allowed to create locations.
    """
    # Ensure the user is a staff member
    if not current_user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff members can create locations.",
        )

    # Create the location
    new_location = Location(
        name=location_data.name,
        owner_id=current_user.id
    )

    db.add(new_location)
    await db.commit()
    await db.refresh(new_location)

    return new_location
