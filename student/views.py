import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from database import get_db
from .models import Student
from .schemas import StudentCreate, StudentResponse
from user.models import Users
from user.jwt_auth import JWTBearer, JWTAuth
from uuid import UUID

router = APIRouter()
logger = logging.getLogger(__name__)
jwt_auth = JWTAuth()

@router.post("/students_create/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student: StudentCreate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):
    logger.info("Creating student with data: %s", student.dict())

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
    if not user or not user.status:
        logger.error("User is not authorized (ID: %s)", current_user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff users can perform this action"
        )

    new_student = Student(**student.dict())
    db.add(new_student)
    try:
        await db.commit()
        await db.refresh(new_student)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create student: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create student: {str(e)}"
        )

    return new_student


@router.put("/students_update/{student_id}/", response_model=StudentResponse, status_code=status.HTTP_200_OK)
async def update_student(
    student_id: UUID,
    student: StudentCreate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):
    logger.info(f"Updating student with ID: {student_id}")

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
    if not user or not user.status:
        logger.error("User is not authorized (ID: %s)", current_user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff users can perform this action"
        )


    result = await db.execute(select(Student).where(Student.id == student_id))
    existing_student = result.scalar()
    if not existing_student:
        logger.error("Student not found with ID: %s", student_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    try:
        query = (
            update(Student)
            .where(Student.id == student_id)
            .values(**student.dict())
        )
        await db.execute(query)
        await db.commit()

        # Fetch the updated student
        result = await db.execute(select(Student).where(Student.id == student_id))
        updated_student = result.scalar()
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update student: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update student: {str(e)}"
        )

    return updated_student


@router.delete("/students_delete/{student_id}/", status_code=status.HTTP_200_OK)
async def delete_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):
    logger.info(f"Deleting student with ID: {student_id}")

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
    if not user or not user.status:
        logger.error("User is not authorized (ID: %s)", current_user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff users can perform this action"
        )

    result = await db.execute(select(Student).where(Student.id == student_id))
    existing_student = result.scalar()
    if not existing_student:
        logger.error("Student not found with ID: %s", student_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    try:
        await db.execute(delete(Student).where(Student.id == student_id))
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete student: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete student: {str(e)}"
        )

    return {"message": "Student successfully deleted"}


@router.get("/students_detail/{student_id}/", response_model=StudentResponse, status_code=status.HTTP_200_OK)
async def student_detail(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Fetching details for student with ID: {student_id}")

    # Query the student by their ID
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar()

    if not student:
        logger.warning(f"No student found with ID: {student_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found with the provided ID"
        )

    # Return the student's details
    return {
        "id": student.id,
        "name": student.name,
        "lastname": student.lastname,
        "photo": student.photo,
        "deterioration_id": student.deterioration_id,
        "description": student.description,
        "working_place": student.working_place,
        "achievements": student.achievements,
    }


@router.get("/students_list/{deterioration_id}/", response_model=list[dict], status_code=status.HTTP_200_OK)
async def students_list(
    deterioration_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Fetching students list with deterioration_id: {deterioration_id}")

    # Query students filtered by deterioration_id
    result = await db.execute(
        select(Student).where(Student.deterioration_id == deterioration_id)
    )
    students = result.scalars().all()

    if not students:
        logger.warning(f"No students found for deterioration_id: {deterioration_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No students found for the provided deterioration ID"
        )

    # Return name and photo of students
    return [
        {
            "name": student.name,
            "photo": student.photo,
            "id": student.id,
        }
        for student in students
    ]
