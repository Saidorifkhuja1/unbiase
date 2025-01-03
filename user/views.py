from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from database import get_db
from .models import Users
from .schemas import UserCreate, UserRead

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to register a new user.

    Args:
        user (UserCreate): Data for creating a new user.
        db (AsyncSession): Database session dependency.

    Returns:
        UserRead: Created user data excluding the password.
    """
    # Check if email already exists
    result = await db.execute(select(Users).where(Users.email == user.email))
    existing_user = result.scalar()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    # Hash the password
    hashed_password = Users.get_password_hash(user.password)

    # Create the user object
    new_user = Users(
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        password=hashed_password,
    )

    # Add and commit the user to the database
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user. Please try again later.",
        ) from e
