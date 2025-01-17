from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import University
from user.models import Users
from sqlalchemy import update, delete
from .schemas import UniversityCreate, UniversityResponse, UniversityResponse1
from database import get_db
from user.jwt_auth import JWTBearer, JWTAuth
from uuid import UUID
router = APIRouter()
jwt_auth = JWTAuth()




@router.post("/university_create/", response_model=UniversityResponse1, status_code=status.HTTP_201_CREATED)
async def create_university(
    university: UniversityCreate,
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

    result = await db.execute(select(Users).where(Users.id == current_user_id))
    user = result.scalar()
    if not user or not user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff users can create a university"
        )

    # Check if a university with the same email already exists
    existing_university = await db.execute(
        select(University).where(University.email == university.email)
    )
    existing_university = existing_university.scalar()

    if existing_university:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A university with this email already exists."
        )

    # Create the new university
    new_university = University(
        name=university.name,
        photo=str(university.photo) if university.photo else None,
        location_id=university.location_id,
        category_id=university.category_id,
        description=university.description,
        video=str(university.video) if university.video else None,
        amount_of_students=university.amount_of_students,
        phone_number=university.phone_number,
        email=university.email,
        webpage=str(university.webpage),
        created_by_id=current_user_id
    )

    db.add(new_university)
    try:
        await db.commit()  # Commit transaction
        await db.refresh(new_university)  # Refresh the object after commit
    except Exception as e:
        await db.rollback()  # Rollback in case of an error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create university: {str(e)}"
        )

    # Return success message with the created university details
    return UniversityResponse1(
        id=new_university.id,
        name=new_university.name,
        photo=new_university.photo,
        location_id=new_university.location_id,
        category_id=new_university.category_id,
        description=new_university.description,
        video=new_university.video,
        amount_of_students=new_university.amount_of_students,
        phone_number=new_university.phone_number,
        email=new_university.email,
        webpage=new_university.webpage,
        created_by_id=new_university.created_by_id
    )




@router.put("/university_update/{university_id}/")
async def update_university(
    university_id: UUID,
    university: UniversityCreate,
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

    result = await db.execute(select(University).where(University.id == university_id))
    existing_university = result.scalar()
    if not existing_university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )

    if existing_university.created_by_id != UUID(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this university"
        )

    try:
        query = (
            update(University)
            .where(University.id == university_id)
            .values(
                name=university.name,
                photo=str(university.photo) if university.photo else None,
                location_id=university.location_id,
                category_id=university.category_id,
                description=university.description,
                video=str(university.video) if university.video else None,
                amount_of_students=university.amount_of_students,
                phone_number=university.phone_number,
                email=university.email,
                webpage=str(university.webpage),
            )
        )
        await db.execute(query)
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update university: {str(e)}"
        )

    # Return a custom success response
    return {
        "message": "University successfully updated."
    }





@router.delete("/university_delete/{university_id}/", status_code=status.HTTP_200_OK)
async def delete_university(
    university_id: UUID,
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

    # Check if the university exists
    result = await db.execute(select(University).where(University.id == university_id))
    existing_university = result.scalar()
    if not existing_university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )


    if existing_university.created_by_id != UUID(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this university"
        )

    try:
        await db.execute(delete(University).where(University.id == university_id))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete university: {str(e)}"
        )

    return {"message": "University successfully deleted."}


@router.get("/my_university_list/", response_model=list[UniversityResponse])
async def list_universities(
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


    result = await db.execute(select(University).where(University.created_by_id == UUID(current_user_id)))
    universities = result.scalars().all()

    return [
        {
            "id": str(university.id),
            "name": university.name,
            "photo": university.photo,
            "location_id": str(university.location_id),
            "category_id": str(university.category_id),
            "description": university.description,
            "video": university.video,
            "amount_of_students": university.amount_of_students,
            "phone_number": university.phone_number,
            "email": university.email,
            "webpage": university.webpage,
            "created_by_id": str(university.created_by_id),
        }
        for university in universities
    ]



# @router.get("/universities_list/", response_model=list[UniversityResponse1])
# async def list_universities(
#     db: AsyncSession = Depends(get_db)
# ):
#     # Fetch universities from the database
#     result = await db.execute(select(University))
#     universities = result.scalars().all()
#
#     # Return a list of universities, including their id, name, and other details if needed
#     return [
#         {
#             "id": str(university.id),
#             "name": university.name,
#             "photo": university.photo,
#             "location_id": str(university.location_id),
#             "category_id": str(university.category_id),
#             "description": university.description,
#             "amount_of_students": university.amount_of_students,
#             "phone_number": university.phone_number,
#             "email": university.email,
#             "webpage": university.webpage,
#         }
#         for university in universities
#     ]
