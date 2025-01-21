from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import *
from sqlalchemy.orm import selectinload
from user.models import Users
from sqlalchemy import update, delete
from .schemas import *
from database import get_db
from user.jwt_auth import JWTBearer, JWTAuth
from typing import List
from uuid import UUID
import logging

logger = logging.getLogger(__name__)



router = APIRouter()
jwt_auth = JWTAuth()


@router.post("/university_create/", response_model=UniversityResponse, status_code=status.HTTP_201_CREATED)
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


    existing_university_by_name = await db.execute(
        select(University).where(University.name == university.name)
    )
    existing_university_by_name = existing_university_by_name.scalar()

    if existing_university_by_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A university with this name already exists."
        )


    existing_university_by_phone = await db.execute(
        select(University).where(University.phone_number == university.phone_number)
    )
    existing_university_by_phone = existing_university_by_phone.scalar()

    if existing_university_by_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A university with this phone number already exists."
        )


    existing_university_by_email = await db.execute(
        select(University).where(University.email == university.email)
    )
    existing_university_by_email = existing_university_by_email.scalar()

    if existing_university_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A university with this email already exists."
        )

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
        await db.commit()
        await db.refresh(new_university)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create university: {str(e)}"
        )

    return UniversityResponse(
        id=str(new_university.id),
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


    existing_university_by_name = await db.execute(
        select(University).where(University.name == university.name, University.id != university_id)
    )
    existing_university_by_name = existing_university_by_name.scalar()

    if existing_university_by_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A university with this name already exists."
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

    return {
        "message": "University successfully updated."
    }





@router.get("/search_universities_by_name/{name}/", response_model=list[UniversityResponse1])
async def search_universities_by_name(
    name: str,
    db: AsyncSession = Depends(get_db)
):
    try:

        result = await db.execute(select(University).where(University.name.ilike(f"%{name}%")))
        universities = result.scalars().all()

        return [
            {
                "id": str(university.id),
                "name": university.name,
                "photo": university.photo,
                # Add other fields if needed
            }
            for university in universities
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search universities by name: {str(e)}"
        )







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




@router.get("/universities_list/", response_model=list[UniversityResponse1])
async def list_universities(
    db: AsyncSession = Depends(get_db)
):
    try:

        result = await db.execute(select(University))
        universities = result.scalars().all()


        return [
            {
                "id": str(university.id),
                "name": university.name,
                "photo": university.photo,
                # "location_id": str(university.location_id),
                # "category_id": str(university.category_id),
                # "description": university.description,
                # "amount_of_students": university.amount_of_students,
                # "phone_number": university.phone_number,
                # "email": university.email,
                # "webpage": university.webpage,
                # "created_by_id": str(university.created_by_id),
            }
            for university in universities
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch universities: {str(e)}"
        )


@router.get("/universities_by_category/{category_id}/", response_model=list[UniversityResponse1])
async def universities_by_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(University).where(University.category_id == category_id))
        universities = result.scalars().all()

        return [
            {
                "id": str(university.id),
                "name": university.name,
                "photo": university.photo,

            }
            for university in universities
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch universities by category: {str(e)}"
        )



@router.get("/universities_by_location/{location_id}/", response_model=list[UniversityResponse1])
async def universities_by_location(
    location_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(University).where(University.location_id == location_id))
        universities = result.scalars().all()

        return [
            {
                "id": str(university.id),
                "name": university.name,
                "photo": university.photo,

            }
            for university in universities
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch universities by location: {str(e)}"
        )



@router.get("/university_detail/{university_id}/", response_model=UniversityResponse)
async def get_university_detail(
    university_id: UUID,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(select(University).where(University.id == university_id))
    university = result.scalar()

    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )


    return {
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

##########################################################################################################################


@router.post("/department_create/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
        department: DepartmentCreate,
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
            detail="Only staff users can create a department"
        )


    try:
        uuid.UUID(department.university_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid university ID format"
        )


    existing_university = await db.execute(select(University).where(University.id == department.university_id))
    existing_university = existing_university.scalar()
    if not existing_university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )


    existing_department = await db.execute(select(Department).where(Department.name == department.name))
    existing_department = existing_department.scalar()
    if existing_department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A department with this name already exists"
        )


    new_department = Department(
        name=department.name,
        photo=str(department.photo) if department.photo else None,
        description=department.description,
        university_id=department.university_id
    )

    db.add(new_department)
    try:
        await db.commit()
        await db.refresh(new_department)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )

    return DepartmentResponse(
        id=str(new_department.id),
        name=new_department.name,
        photo=new_department.photo,
        description=new_department.description,
        university_id=str(new_department.university_id)
    )


@router.get("/department_detail/{department_id}/", response_model=DepartmentResponse, status_code=status.HTTP_200_OK)
async def department_detail(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Fetching details for department with ID: {department_id}")


    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar()

    if not department:
        logger.warning(f"No department found with ID: {department_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found with the provided ID"
        )


    return {
        "id": str(department.id),
        "name": department.name,
        "description": department.description,
        "university_id": str(department.university_id) if department.university_id else None,
    }


@router.put("/department_update/{department_id}", response_model=DepartmentResponse, status_code=status.HTTP_200_OK)
async def update_department(
    department_id: str,
    department: DepartmentCreate,
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
            detail="Only staff users can update a department"
        )


    department_to_update = await db.execute(select(Department).where(Department.id == department_id))
    department_to_update = department_to_update.scalar()
    if not department_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )


    existing_department = await db.execute(
        select(Department).where(Department.name == department.name, Department.id != department_id)
    )
    existing_department = existing_department.scalar()
    if existing_department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A department with this name already exists"
        )


    department_to_update.name = department.name
    department_to_update.photo = str(department.photo) if department.photo else None
    department_to_update.description = department.description
    department_to_update.university_id = department.university_id

    db.add(department_to_update)
    try:
        await db.commit()
        await db.refresh(department_to_update)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update department: {str(e)}"
        )

    return DepartmentResponse(
        id=str(department_to_update.id),
        name=department_to_update.name,
        photo=department_to_update.photo,
        description=department_to_update.description,
        university_id=str(department_to_update.university_id)
    )




@router.delete("/department_delete/{department_id}", status_code=status.HTTP_200_OK)
async def delete_department(
    department_id: str,
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
            detail="Only staff users can delete a department"
        )


    department_to_delete = await db.execute(select(Department).where(Department.id == department_id))
    department_to_delete = department_to_delete.scalar()
    if not department_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )


    try:
        await db.delete(department_to_delete)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete department: {str(e)}"
        )

    return {"detail": "Department deleted successfully"}





@router.get("/departments_list/{university_id}", response_model=List[DepartmentResponse], status_code=status.HTTP_200_OK)
async def list_departments(
    university_id: str,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(select(Department).where(Department.university_id == university_id))
    departments = result.scalars().all()


    if not departments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No departments found for the specified university."
        )


    return [
        DepartmentResponse(
            id=str(department.id),
            name=department.name,
            photo=department.photo,
            description=department.description,
            university_id=str(department.university_id)
        )
        for department in departments
    ]
#################################################################################################################

@router.post("/deterioration_create/", response_model=DeteriorationResponse, status_code=status.HTTP_201_CREATED)
async def create_deterioration(
    deterioration: DeteriorationCreate,
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


    department = await db.execute(select(Department).where(Department.id == deterioration.department_id))
    department = department.scalar()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )


    existing_deterioration = await db.execute(
        select(Deterioration).where(Deterioration.name == deterioration.name)
    )
    existing_deterioration = existing_deterioration.scalar()

    if existing_deterioration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deterioration with this name already exists"
        )


    new_deterioration = Deterioration(
        name=deterioration.name,
        department_id=deterioration.department_id,
        photo=deterioration.photo,
        description=deterioration.description,
        number_of_students=deterioration.number_of_students,
    )

    db.add(new_deterioration)

    try:
        await db.commit()
        await db.refresh(new_deterioration)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deterioration: {str(e)}"
        )

    return DeteriorationResponse(
        id=str(new_deterioration.id),
        name=new_deterioration.name,
        department_id=str(new_deterioration.department_id),
        photo=new_deterioration.photo,
        description=new_deterioration.description,
        number_of_students=new_deterioration.number_of_students,
    )



@router.get("/deterioration_detail/{deterioration_id}/", response_model=DeteriorationResponse, status_code=status.HTTP_200_OK)
async def deterioration_detail(
    deterioration_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Fetching details for deterioration with ID: {deterioration_id}")


    result = await db.execute(
        select(Deterioration).where(Deterioration.id == deterioration_id)
    )
    deterioration = result.scalar()

    if not deterioration:
        logger.warning(f"No deterioration found with ID: {deterioration_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deterioration not found with the provided ID"
        )


    return {
        "id": str(deterioration.id),
        "name": deterioration.name,
        "description": deterioration.description,
        "department_id": str(deterioration.department_id) if deterioration.department_id else None,
        "photo": deterioration.photo,
        "number_of_students": deterioration.number_of_students,
    }



@router.put("/deterioration_update/{deterioration_id}", response_model=DeteriorationResponse, status_code=status.HTTP_200_OK)
async def update_deterioration(
    deterioration_id: str,
    deterioration: DeteriorationUpdate,
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


    deterioration_to_update = await db.execute(select(Deterioration).where(Deterioration.id == deterioration_id))
    deterioration_to_update = deterioration_to_update.scalar()

    if not deterioration_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deterioration not found"
        )


    department = await db.execute(select(Department).where(Department.id == deterioration.department_id))
    department = department.scalar()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )


    if deterioration_to_update.name != deterioration.name:
        existing_deterioration = await db.execute(
            select(Deterioration).where(Deterioration.name == deterioration.name)
        )
        existing_deterioration = existing_deterioration.scalar()

        if existing_deterioration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deterioration with this name already exists"
            )


    deterioration_to_update.name = deterioration.name
    deterioration_to_update.department_id = deterioration.department_id
    deterioration_to_update.photo = deterioration.photo
    deterioration_to_update.description = deterioration.description
    deterioration_to_update.number_of_students = deterioration.number_of_students

    try:
        await db.commit()
        await db.refresh(deterioration_to_update)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update deterioration: {str(e)}"
        )

    return DeteriorationResponse(
        id=str(deterioration_to_update.id),
        name=deterioration_to_update.name,
        department_id=str(deterioration_to_update.department_id),
        photo=deterioration_to_update.photo,
        description=deterioration_to_update.description,
        number_of_students=deterioration_to_update.number_of_students,
    )





@router.delete("/deterioration_delete/{deterioration_id}", status_code=status.HTTP_200_OK)
async def delete_deterioration(
    deterioration_id: str,
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


    deterioration_to_delete = await db.execute(select(Deterioration).where(Deterioration.id == deterioration_id))
    deterioration_to_delete = deterioration_to_delete.scalar()

    if not deterioration_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deterioration not found"
        )

    try:
        await db.delete(deterioration_to_delete)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete deterioration: {str(e)}"
        )

    return {"detail": "Deterioration deleted successfully"}


@router.get("/deteriorations_list/{department_id}", response_model=List[DeteriorationResponse], status_code=status.HTTP_200_OK)
async def list_deteriorations(
    department_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Deterioration).where(Deterioration.department_id == department_id))
    deteriorations = result.scalars().all()

    if not deteriorations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No deteriorations found for the specified department."
        )

    return [
        DeteriorationResponse(
            id=str(deterioration.id),
            name=deterioration.name,
            department_id=str(deterioration.department_id),
            photo=deterioration.photo,
            description=deterioration.description,
            number_of_students=deterioration.number_of_students,
        )
        for deterioration in deteriorations
    ]
