import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from database import get_db
from .models import Location
from .schemas import LocationCreate, LocationID
from user.models import Users
from user.jwt_auth import JWTBearer, JWTAuth
from uuid import UUID



router = APIRouter()


logger = logging.getLogger(__name__)


jwt_auth = JWTAuth()

@router.post("/locations_create/", response_model=LocationCreate, status_code=status.HTTP_201_CREATED)
async def create_location(
    location: LocationCreate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):
    """
    Create a new location.
    """

    logger.info("Creating location with data: %s", location.dict())


    payload = jwt_auth.decode_token(token)
    current_user_id = payload.get("user_id")
    if not current_user_id:
        logger.error("User ID not found in the token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )


    result = await db.execute(select(Users).where(Users.id == current_user_id))
    user = result.scalar()
    if not user:
        logger.error("User not found with ID: %s", current_user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with the provided ID does not exist"
        )


    if not user.status:
        logger.error("User is not a staff member with ID: %s", current_user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff users can create locations"
        )


    new_location = Location(
        name=location.name,
        created_by_id=current_user_id
    )


    db.add(new_location)
    try:
        await db.commit()
        await db.refresh(new_location)
    except Exception as e:

        await db.rollback()
        logger.error(f"Failed to create location: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create location: {str(e)}"
        )


    return {"name": new_location.name, "created_by_id": new_location.created_by_id}



@router.put("/locations_update/{location_id}/", response_model=dict)
async def update_location(
    location_id: UUID,
    location: LocationCreate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):

    payload = jwt_auth.decode_token(token)
    current_user_id = payload.get("user_id")
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )


    result = await db.execute(select(Location).where(Location.id == location_id))
    existing_location = result.scalar()


    if not existing_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )


    if existing_location.created_by_id != UUID(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this location"
        )


    try:
        query = (
            update(Location)
            .where(Location.id == location_id)
            .values(name=location.name)
        )
        await db.execute(query)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update location: {str(e)}"
        )


    return {
        "message": "Location successfully updated.",
        "updated_location": {
            "id": str(location_id),
            "name": location.name,
            "created_by_id": current_user_id,
        },
    }





@router.delete("/locations_delete/{location_id}/", status_code=status.HTTP_200_OK)
async def delete_location(
        location_id: UUID,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(JWTBearer(jwt_auth))
):

    payload = jwt_auth.decode_token(token)
    current_user_id = payload.get("user_id")
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )


    result = await db.execute(select(Location).where(Location.id == location_id))
    existing_location = result.scalar()


    if not existing_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )


    if existing_location.created_by_id != UUID(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this location"
        )


    try:
        await db.execute(delete(Location).where(Location.id == location_id))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete location: {str(e)}"
        )


    return {"message": "Location successfully deleted."}




@router.get("/my_locations_list/", response_model=list[LocationID])
async def list_locations(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):
    payload = jwt_auth.decode_token(token)
    current_user_id = payload.get("user_id")
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )

    result = await db.execute(select(Location).where(Location.created_by_id == current_user_id))
    locations = result.scalars().all()


    return [{"id": location.id, "name": location.name} for location in locations]






@router.get("/locations_list/", response_model=list[LocationID])
async def list_locations(
    db: AsyncSession = Depends(get_db),
):


    result = await db.execute(select(Location))
    locations = result.scalars().all()


    return [{"id": location.id, "name": location.name} for location in locations]











