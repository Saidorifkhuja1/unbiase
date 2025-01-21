from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from .models import Cart
from .schemas import CartResponse, AddToCartRequest
from user.jwt_auth import JWTBearer, JWTAuth
from database import get_db

router = APIRouter()

jwt_auth = JWTAuth()
jwt_bearer = JWTBearer(jwt_auth=jwt_auth)



@router.post("/add_cart", response_model=CartResponse)
async def add_cart(
        request: AddToCartRequest,
        db: AsyncSession = Depends(get_db),
        token: HTTPAuthorizationCredentials = Depends(jwt_bearer),
):
    try:

        decoded_token = jwt_auth.decode_token(token)
        if not decoded_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_id = decoded_token.get("user_id")


        existing_cart_item = await db.execute(
            select(Cart).filter_by(user_id=user_id, university_id=request.university_id)
        )
        existing_cart_item = existing_cart_item.scalar_one_or_none()

        if existing_cart_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item already exists in cart"
            )


        cart_item = Cart(user_id=user_id, university_id=request.university_id)
        db.add(cart_item)
        await db.commit()
        await db.refresh(cart_item)

        return CartResponse.from_orm(cart_item)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add item to cart: {str(e)}"
        )



@router.get("/get_my_cart", response_model=list[CartResponse])
async def get_my_cart(
        db: AsyncSession = Depends(get_db),
        token: HTTPAuthorizationCredentials = Depends(jwt_bearer),
):
    try:

        decoded_token = jwt_auth.decode_token(token)
        if not decoded_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_id = decoded_token.get("user_id")


        result = await db.execute(select(Cart).filter_by(user_id=user_id))
        cart_items = result.scalars().all()

        if not cart_items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No items found in your cart")

        return [CartResponse.from_orm(cart_item) for cart_item in cart_items]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch user's cart: {str(e)}"
        )



@router.delete("/remove_from_cart", response_model=CartResponse)
async def remove_from_cart(
        university_id: UUID,
        db: AsyncSession = Depends(get_db),
        token: HTTPAuthorizationCredentials = Depends(jwt_bearer),
):
    try:

        decoded_token = jwt_auth.decode_token(token)
        if not decoded_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_id = decoded_token.get("user_id")


        cart_item = await db.execute(
            select(Cart).filter_by(user_id=user_id, university_id=university_id)
        )
        cart_item = cart_item.scalar_one_or_none()

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )


        await db.delete(cart_item)
        await db.commit()


        return CartResponse.from_orm(cart_item)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete item from cart: {str(e)}"
        )



@router.get("/check_in_cart", response_model=bool)
async def check_in_cart(
        university_id: UUID,
        db: AsyncSession = Depends(get_db),
        token: HTTPAuthorizationCredentials = Depends(jwt_bearer),
):
    try:

        decoded_token = jwt_auth.decode_token(token)
        if not decoded_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_id = decoded_token.get("user_id")


        cart_item = await db.execute(
            select(Cart).filter_by(user_id=user_id, university_id=university_id)
        )
        cart_item = cart_item.scalar_one_or_none()
        return cart_item is not None

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to check if item is in cart: {str(e)}"
        )
