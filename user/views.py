from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from database import get_db
from .models import Users, pwd_context
from .schemas import UserCreate, UserAuth, UserBase, UserPassword
from fastapi.encoders import jsonable_encoder
from .jwt_auth import JWTAuth, JWTBearer
from fastapi.responses import JSONResponse


router = APIRouter()
jwt_auth = JWTAuth()

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to register a new user.

    Args:
        user (UserCreate): Data for creating a new user.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: A dictionary containing a success message, user data, and JWT tokens.
    """
    # Check if email already exists
    result = await db.execute(select(Users).where(Users.email == user.email))
    existing_user = result.scalar()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )


    hashed_password = Users.get_password_hash(user.password)


    is_staff = user.status if user.status is not None else False

    # Create the user object
    new_user = Users(
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        password=hashed_password,
        status=is_staff,  # Set staff status based on the input or default to False
    )

    # Add and commit the user to the database
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Generate JWT tokens
        tokens = JWTAuth().login_jwt(user_id=str(new_user.id))

        # Serialize the user object
        user_data = jsonable_encoder(new_user)

        return {
            "message": "User registered successfully.",
            "user": user_data,
            "tokens": tokens,  # Include access and refresh tokens in the response
        }
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user. Please try again later.",
        ) from e



@router.post('/user_login')
async def user_login(user_data: UserAuth, db: AsyncSession = Depends(get_db)):
    # Retrieve the user from the database by email
    result = await db.execute(select(Users).where(Users.email == user_data.email))
    user = result.scalar()

    if user and pwd_context.verify(user_data.password, user.password):
        # Generate JWT token
        jwt_token = JWTAuth().login_jwt(str(user.id))
        return jwt_token
    else:
        # Return error if the user is not found or password is incorrect
        return JSONResponse(
            content={"error": "Email or password incorrect"},
            status_code=status.HTTP_400_BAD_REQUEST
        )


@router.get('/user_detail', dependencies=[Depends(JWTBearer(JWTAuth()))])
async def user_detail(db: AsyncSession = Depends(get_db), jwt_token: str = Depends(JWTBearer(JWTAuth()))):
    """
    Endpoint to retrieve user details of the currently authenticated user.

    Args:
        db (AsyncSession): Database session dependency.
        jwt_token (str): JWT token extracted from the authorization header.

    Returns:
        dict: User details excluding password if user found, error message otherwise.
    """
    # Decode the JWT token to extract the user_uuid
    decoded_token = JWTAuth().decode_token(jwt_token)
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_uuid = decoded_token.get("user_id")

    # Retrieve the user from the database by UUID
    result = await db.execute(select(Users).where(Users.id == user_uuid))
    user = result.scalar()

    if not user:
        return JSONResponse(
            content={"error": "User not found"},
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Convert the user object to a dictionary
    user_data = user.__dict__

    # Remove the password from the user data
    user_data.pop("password", None)

    return user_data



@router.patch("/update_user", dependencies=[Depends(JWTBearer(JWTAuth()))])
async def update_user(user_data: UserBase, db: AsyncSession = Depends(get_db),
                      jwt_token: str = Depends(JWTBearer(JWTAuth()))):
    """
    Endpoint to update user details for the currently authenticated user.

    Args:
        user_data (schemas.UserAuth): User data to update.
        db (AsyncSession): Database session dependency.
        jwt_token (str): JWT token extracted from the authorization header.

    Returns:
        dict: Updated user details.
    """
    # Decode the JWT token to extract the user_uuid
    decoded_token = JWTAuth().decode_token(jwt_token)
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_uuid = decoded_token.get("user_id")

    # Retrieve the user from the database by UUID
    result = await db.execute(select(Users).where(Users.id == user_uuid))
    user = result.scalar()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if the email in the update request already exists
    existing_user_result = await db.execute(select(Users).where(Users.email == user_data.email))
    existing_user = existing_user_result.scalar()

    if existing_user and existing_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Update the user details (DO NOT update the password field)
    user.full_name = user_data.full_name
    user.phone_number = user_data.phone_number
    user.email = user_data.email

    # Commit the changes to the database
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Convert the updated user to a dictionary and REMOVE password
        user_data = user.__dict__
        if "password" in user_data:
            user_data.pop("password")  # Explicitly remove password

        return user_data

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user. Please try again later."
        ) from e


@router.patch("/update_password", dependencies=[Depends(JWTBearer(JWTAuth()))])
async def update_password(user_data: UserPassword, db: AsyncSession = Depends(get_db),
                          jwt_token: str = Depends(JWTBearer(JWTAuth()))):
    """
    Endpoint to update password for the currently authenticated user.
    Requires the old password to be provided, and the new password will be validated and updated.

    Args:
        user_data (schemas.UserPasswordUpdate): User data, including old and new password.
        db (AsyncSession): Database session dependency.
        jwt_token (str): JWT token extracted from the authorization header.

    Returns:
        dict: Success message after updating the password.
    """
    # Decode the JWT token to extract the user_uuid
    decoded_token = JWTAuth().decode_token(jwt_token)
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_uuid = decoded_token.get("user_id")

    # Retrieve the user from the database by UUID
    result = await db.execute(select(Users).where(Users.id == user_uuid))
    user = result.scalar()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if the old password provided matches the current password in the database
    if not pwd_context.verify(user_data.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect"
        )

    # Hash the new password and update it
    new_hashed_password = pwd_context.hash(user_data.new_password)

    user.password = new_hashed_password

    # Commit the changes to the database
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "Password updated successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password. Please try again later."
        ) from e



@router.delete("/delete_user", dependencies=[Depends(JWTBearer(JWTAuth()))])
async def delete_user(db: AsyncSession = Depends(get_db), jwt_token: str = Depends(JWTBearer(JWTAuth()))):
    """
    Endpoint to delete the currently authenticated user.

    Args:
        db (AsyncSession): Database session dependency.
        jwt_token (str): JWT token extracted from the authorization header.

    Returns:
        dict: Success message if user is deleted.
    """
    # Decode the JWT token to extract the user_uuid
    decoded_token = JWTAuth().decode_token(jwt_token)
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_uuid = decoded_token.get("user_id")

    # Retrieve the user from the database by UUID
    result = await db.execute(select(Users).where(Users.id == user_uuid))
    user = result.scalar()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete the user from the database
    try:
        await db.delete(user)
        await db.commit()

        return {"message": "User deleted successfully."}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user. Please try again later."
        ) from e

