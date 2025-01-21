from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models import Comment
from .schemas import *
from user.jwt_auth import JWTBearer, JWTAuth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from database import get_db
import logging

router = APIRouter()

jwt_auth = JWTAuth()
jwt_bearer = JWTBearer(jwt_auth=jwt_auth)

# 1. **Create a Comment**: Requires authentication
@router.post("/create_comments/", response_model=CommentResponse)
async def create_comment(
    body: str,
    university_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(jwt_bearer),
):
    try:

        decoded_token = jwt_auth.decode_token(token)
        if not decoded_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_id = decoded_token.get("user_id")

        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")


        new_comment = Comment(body=body, university_id=university_id, user_id=user_id)
        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)

        return CommentResponse.from_orm(new_comment)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.put("/update_comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    body: str,
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(jwt_bearer),
):
    try:
        decoded_token = jwt_auth.decode_token(token)
        if not decoded_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_id = decoded_token.get("user_id")

        comment = await db.execute(select(Comment).filter_by(id=comment_id, user_id=user_id))
        comment = comment.scalar_one_or_none()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found "
            )

        comment.body = body
        await db.commit()
        await db.refresh(comment)

        return CommentResponse.from_orm(comment)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update comment: {str(e)}"
        )



@router.delete("/delete_comments/{comment_id}")
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(jwt_bearer),
):
    try:
        decoded_token = jwt_auth.decode_token(token)
        if not decoded_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_id = decoded_token.get("user_id")

        comment = await db.execute(select(Comment).filter_by(id=comment_id, user_id=user_id))
        comment = comment.scalar_one_or_none()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found "
            )

        await db.delete(comment)
        await db.commit()


        return {"message": "Comment successfully deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete comment: {str(e)}"
        )






@router.get("/my_comments_list", response_model=list[CommentResponse])
async def my_comments_list(
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(jwt_bearer),
):
    try:

        decoded_token = jwt_auth.decode_token(token)
        if not decoded_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


        user_id = decoded_token.get("user_id")


        result = await db.execute(select(Comment).filter_by(user_id=user_id))
        comments = result.scalars().all()

        if not comments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No comments found for this user"
            )


        return [CommentResponse.from_orm(comment) for comment in comments]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch user's comments: {str(e)}"
        )



@router.get("/comments_list_by_university/{university_id}", response_model=list[CommentResponse])
async def comments_by_university(
    university_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(Comment).filter_by(university_id=university_id))
        comments = result.scalars().all()

        if not comments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No comments found for this university"
            )

        return [CommentResponse.from_orm(comment) for comment in comments]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch comments for university: {str(e)}"
        )
