from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from user.models import Users
from user.jwt_auth import JWTBearer, JWTAuth
from database import get_db
import uuid

router = APIRouter()
jwt_auth = JWTAuth()


async def get_current_staff_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth)),
):
    print("Decoding token")
    payload = jwt_auth.decode_token(token)
    print(f"Token payload: {payload}")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    print(f"Fetching user: {user_id}")
    result = await db.execute(select(Users).filter(Users.id == uuid.UUID(user_id)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff users are allowed to perform this action",
        )

    print(f"User fetched: {user}")
    return user

