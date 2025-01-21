import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from uuid import UUID
from database import get_db
from .models import News
from .schemas import NewsCreate, NewsResponse, NewsUpdate
from user.models import Users
from user.jwt_auth import JWTBearer, JWTAuth

router = APIRouter()
logger = logging.getLogger(__name__)

jwt_auth = JWTAuth()


@router.post("/news_create/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    news: NewsCreate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(JWTBearer(jwt_auth))
):

    logger.info("Creating news item with data: %s", news.dict())

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
            detail="Only staff users can create news"
        )

    new_news = News(
        title=news.title,
        photo=news.photo,
        body=news.body,
        created_by_id=current_user_id
    )

    db.add(new_news)
    try:
        await db.commit()
        await db.refresh(new_news)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create news: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create news: {str(e)}"
        )

    return NewsResponse(
        id=new_news.id,
        title=new_news.title,
        photo=new_news.photo,
        body=news.body,
        created_by_id=current_user_id
    )



@router.put("/news_update/{news_id}/", response_model=NewsResponse)
async def update_news(
    news_id: UUID,
    news: NewsUpdate,
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

    result = await db.execute(select(News).where(News.id == news_id))
    existing_news = result.scalar()

    if not existing_news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News item not found"
        )

    if existing_news.created_by_id != UUID(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this news item"
        )

    try:
        query = (
            update(News)
            .where(News.id == news_id)
            .values(
                title=news.title or existing_news.title,
                photo=news.photo or existing_news.photo,
                body=news.body or existing_news.body
            )
        )
        await db.execute(query)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update news: {str(e)}"
        )

    return NewsResponse(
        id=news_id,
        title=news.title or existing_news.title,
        photo=news.photo or existing_news.photo,
        body=news.body or existing_news.body,
        created_by_id=current_user_id
    )



@router.delete("/news_delete/{news_id}/", status_code=status.HTTP_200_OK)
async def delete_news(
    news_id: UUID,
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

    result = await db.execute(select(News).where(News.id == news_id))
    existing_news = result.scalar()

    if not existing_news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News item not found"
        )

    if existing_news.created_by_id != UUID(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this news item"
        )

    try:
        await db.execute(delete(News).where(News.id == news_id))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete news: {str(e)}"
        )

    return {"message": "News successfully deleted."}



@router.get("/all_news_list/", response_model=list[NewsResponse])
async def list_all_news(db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(News))
    news_list = result.scalars().all()

    return [
        NewsResponse(
            id=article.id,
            title=article.title,
            photo=article.photo,
            body=article.body,
            created_by_id=article.created_by_id
        )
        for article in news_list
    ]



@router.get("/my_news_list/", response_model=list[NewsResponse])
async def list_my_news(
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

    result = await db.execute(select(News).where(News.created_by_id == current_user_id))
    my_news = result.scalars().all()

    return [
        NewsResponse(
            id=article.id,
            title=article.title,
            photo=article.photo,
            body=article.body,
            created_by_id=article.created_by_id
        )
        for article in my_news
    ]
