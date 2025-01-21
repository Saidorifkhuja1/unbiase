import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from database import get_db
from .models import Category
from .schemas import CategoryCreate, CategoryID
from user.models import Users
from user.jwt_auth import JWTBearer, JWTAuth
from uuid import UUID



router = APIRouter()


logger = logging.getLogger(__name__)


jwt_auth = JWTAuth()

@router.post("/category_create/", response_model=CategoryCreate, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):
    logger.info("Creating category with data: %s", category.dict())

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
            detail="Only staff users can create categories"
        )


    existing_category = await db.execute(select(Category).where(Category.name == category.name))
    if existing_category.scalar():
        logger.error(f"Category with name '{category.name}' already exists.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists."
        )


    new_category = Category(
        name=category.name,
        created_by_id=current_user_id
    )

    db.add(new_category)
    try:
        await db.commit()
        await db.refresh(new_category)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create category: {str(e)}"
        )

    return {"name": new_category.name, "created_by_id": new_category.created_by_id}


@router.put("/category_update/{category_id}/", response_model=dict)
async def update_category(
    category_id: UUID,
    category: CategoryCreate,
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


    result = await db.execute(select(Category).where(Category.id == category_id))
    existing_category = result.scalar()
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )


    if existing_category.created_by_id != UUID(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this category"
        )


    name_conflict = await db.execute(
        select(Category).where(Category.name == category.name, Category.id != category_id)
    )
    if name_conflict.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists."
        )


    try:
        query = (
            update(Category)
            .where(Category.id == category_id)
            .values(name=category.name)
        )
        await db.execute(query)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update category: {str(e)}"
        )

    return {
        "message": "Category successfully updated.",
        "updated_category": {
            "id": str(category_id),
            "name": category.name,
            "created_by_id": current_user_id,
        },
    }







# @router.delete("/category_delete/{category_id}/", status_code=status.HTTP_200_OK)
# async def delete_category(
#         category_id: UUID,
#         db: AsyncSession = Depends(get_db),
#         token: str = Depends(JWTBearer(jwt_auth))
# ):
#
#     payload = jwt_auth.decode_token(token)
#     current_user_id = payload.get("user_id")
#     if not current_user_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not authenticated"
#         )
#
#
#     result = await db.execute(select(Category).where(Category.id == category_id))
#     existing_category = result.scalar()
#
#
#     if not existing_category:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Category not found"
#         )
#
#
#     if existing_category.created_by_id != UUID(current_user_id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You do not have permission to delete this category"
#         )
#
#
#     try:
#         await db.execute(delete(Category).where(Category.id == category_id))
#         await db.commit()
#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete category: {str(e)}"
#         )
#
#
#     return {"message": "Category successfully deleted."}




@router.get("/my_category_list/", response_model=list[CategoryID])
async def list_categories(
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

    result = await db.execute(select(Category).where(Category.created_by_id == current_user_id))
    categories = result.scalars().all()


    return [{"id": category.id, "name": category.name} for category in categories]




@router.get("/all_categories_list/", response_model=list[CategoryID])
async def list_categories(
    db: AsyncSession = Depends(get_db),
):


    result = await db.execute(select(Category))
    categories = result.scalars().all()


    return [{"id": category.id, "name": category.name} for category in categories]



