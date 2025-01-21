from fastapi import APIRouter
from user.views import router as auth_router
from location.views import router as location_router
from category.views import router as category_router
from univer.views import router as univer_router
from news.views import router as news_router
from comment.views import router as comment_router
from cart.views import router as cart_router
from student.views import router as student_router


api_router = APIRouter()

api_router.include_router(auth_router, prefix='', tags=['Auth'])
api_router.include_router(cart_router, prefix='', tags=['Cart'])
api_router.include_router(location_router, prefix='', tags=['Location'])
api_router.include_router(category_router, prefix='', tags=['Category'])
api_router.include_router(univer_router, prefix='', tags=['University'])
api_router.include_router(student_router, prefix='', tags=['Students'])
api_router.include_router(comment_router, prefix='', tags=['Comments'])
api_router.include_router(news_router, prefix='', tags=['News'])


