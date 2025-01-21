import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from database import get_db
from .models import *
from .schemas import *
from user.models import Users
from user.jwt_auth import JWTBearer, JWTAuth
from uuid import UUID



router = APIRouter()


logger = logging.getLogger(__name__)


jwt_auth = JWTAuth()






@router.post("/regions_create/", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def create_region(
    region: RegionCreate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):
    logger.info("Creating region with data: %s", region.dict())
    payload = jwt_auth.decode_token(token)
    current_user_id = payload.get("user_id")

    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )

    result = await db.execute(select(Users).where(Users.id == current_user_id))
    user = result.scalar()
    if not user or not user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff users can create regions"
        )

    existing_region = await db.execute(select(Region).where(Region.name == region.name))
    if existing_region.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A region with this name already exists"
        )

    new_region = Region(
        name=region.name,
        created_by_id=current_user_id
    )

    db.add(new_region)
    try:
        await db.commit()
        await db.refresh(new_region)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create region: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create region: {str(e)}"
        )

    return {"id": str(new_region.id), "name": new_region.name, "created_by_id": str(new_region.created_by_id)}


@router.put("/regions_update/{region_id}", response_model=RegionResponse, status_code=status.HTTP_200_OK)
async def update_region(
    region_id: UUID,
    region: RegionUpdate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):
    logger.info("Updating region with ID: %s", region_id)
    payload = jwt_auth.decode_token(token)
    current_user_id = payload.get("user_id")

    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )

    result = await db.execute(select(Users).where(Users.id == current_user_id))
    user = result.scalar()
    if not user or not user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff users can update regions"
        )

    region_to_update = await db.execute(select(Region).where(Region.id == region_id))
    region_to_update = region_to_update.scalar()
    if not region_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )

    region_to_update.name = region.name

    try:
        await db.commit()
        await db.refresh(region_to_update)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update region: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update region: {str(e)}"
        )

    return {"id": str(region_to_update.id), "name": region_to_update.name, "created_by_id": str(region_to_update.created_by_id)}


# @router.delete("/regions_delete/{region_id}", status_code=status.HTTP_200_OK)
# async def delete_region(
#     region_id: UUID,
#     db: AsyncSession = Depends(get_db),
#     token: str = Depends(JWTBearer(jwt_auth))
# ):
#     logger.info("Deleting region with ID: %s", region_id)
#     payload = jwt_auth.decode_token(token)
#     current_user_id = payload.get("user_id")
#
#     if not current_user_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not authenticated"
#         )
#
#     result = await db.execute(select(Users).where(Users.id == current_user_id))
#     user = result.scalar()
#     if not user or not user.status:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only staff users can delete regions"
#         )
#
#     region_to_delete = await db.execute(select(Region).where(Region.id == region_id))
#     region_to_delete = region_to_delete.scalar()
#     if not region_to_delete:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Region not found"
#         )
#
#     try:
#         await db.execute(delete(Region).where(Region.id == region_id))
#         await db.commit()
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Failed to delete region: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete region: {str(e)}"
#         )
#
#     return None


@router.get("/my_regions_list/", response_model=list[RegionResponse], status_code=status.HTTP_200_OK)
async def get_my_regions(
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

    regions = await db.execute(select(Region).where(Region.created_by_id == current_user_id))
    regions = regions.scalars().all()

    return [{"id": str(region.id), "name": region.name, "created_by_id": str(region.created_by_id)} for region in regions]


@router.get("/all_regions_list/", response_model=list[RegionResponse], status_code=status.HTTP_200_OK)
async def get_all_regions(db: AsyncSession = Depends(get_db)):
    regions = await db.execute(select(Region))
    regions = regions.scalars().all()

    return [{"id": str(region.id), "name": region.name, "created_by_id": str(region.created_by_id)} for region in regions]










####################################################################################################################################



@router.post("/locations_create/", response_model=LocationID, status_code=status.HTTP_201_CREATED)
async def create_location(
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

    user_result = await db.execute(select(Users).where(Users.id == current_user_id))
    user = user_result.scalar()

    if not user or not user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff users can create locations"
        )


    region_result = await db.execute(select(Region).where(Region.id == location.region_id))
    region = region_result.scalar()

    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )


    existing_location = await db.execute(select(Location).where(Location.name == location.name))
    if existing_location.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A location with this name already exists"
        )

    new_location = Location(
        name=location.name,
        region_id=location.region_id,
        created_by_id=current_user_id
    )

    db.add(new_location)
    try:
        await db.commit()
        await db.refresh(new_location)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create location: {str(e)}"
        )

    return LocationID(id=new_location.id, name=new_location.name, region_id=new_location.region_id)




@router.put("/locations_update/{location_id}/", response_model=LocationID, status_code=status.HTTP_200_OK)
async def update_location(
    location_id: UUID,
    location: LocationUpdate,
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

    
    region_result = await db.execute(select(Region).where(Region.id == location.region_id))
    region = region_result.scalar()

    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )

    duplicate_location = await db.execute(
        select(Location).where(Location.name == location.name, Location.id != location_id)
    )
    if duplicate_location.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A location with this name already exists"
        )

    try:
        query = (
            update(Location)
            .where(Location.id == location_id)
            .values(name=location.name, region_id=location.region_id)
        )
        await db.execute(query)
        await db.commit()

        updated_location = await db.execute(select(Location).where(Location.id == location_id))
        updated_location = updated_location.scalar()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update location: {str(e)}"
        )

    return LocationID(id=updated_location.id, name=updated_location.name, region_id=updated_location.region_id)


# @router.delete("/locations_delete/{location_id}/", status_code=status.HTTP_200_OK)
# async def delete_location(
#     location_id: UUID,
#     db: AsyncSession = Depends(get_db),
#     token: str = Depends(JWTBearer(jwt_auth))
# ):
#     payload = jwt_auth.decode_token(token)
#     current_user_id = payload.get("user_id")
#
#     if not current_user_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not authenticated"
#         )
#
#     # Retrieve the location
#     result = await db.execute(select(Location).where(Location.id == location_id))
#     existing_location = result.scalar()
#
#     if not existing_location:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Location not found"
#         )
#
#     # Check if the user is authorized to delete the location
#     if existing_location.created_by_id != UUID(current_user_id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You do not have permission to delete this location"
#         )
#
#
#     try:
#         await db.execute(delete(Location).where(Location.id == location_id))
#         await db.commit()
#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete location: {str(e)}"
#         )
#
#     return {"message": f"Location with ID {location_id} successfully deleted."}



@router.get("/my_locations_list/", response_model=list[LocationID], status_code=status.HTTP_200_OK)
async def list_my_locations(
    region_id: UUID,
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

    result = await db.execute(
        select(Location).where(Location.created_by_id == current_user_id, Location.region_id == region_id)
    )
    locations = result.scalars().all()

    return [{"id": location.id, "name": location.name, "region_id": location.region_id} for location in locations]


@router.get("/all_locations_list/", response_model=list[LocationID], status_code=status.HTTP_200_OK)
async def list_all_locations(
    region_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Location).where(Location.region_id == region_id))
    locations = result.scalars().all()

    return [{"id": location.id, "name": location.name, "region_id": location.region_id} for location in locations]








