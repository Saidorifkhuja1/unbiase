from fastapi import APIRouter
from user.views import router as auth_router
#from location.views import router as location_router


api_router = APIRouter()

api_router.include_router(auth_router, prefix='', tags=['Auth'])
#location_router.include_router(location_router, prefix='', tags=['Locarion'])


