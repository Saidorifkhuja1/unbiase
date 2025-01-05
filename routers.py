from fastapi import APIRouter
from user.views import router as auth_router



api_router = APIRouter()

api_router.include_router(auth_router, prefix='', tags=['Auth'])


