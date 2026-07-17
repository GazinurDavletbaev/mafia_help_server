from fastapi import APIRouter
from .crud import router as crud_router
from .members import router as members_router
from .requests import router as requests_router
from .judges import router as judges_router
from .rating import router as rating_router

router = APIRouter()

router.include_router(crud_router)
router.include_router(members_router)
router.include_router(requests_router)
router.include_router(judges_router)
router.include_router(rating_router)
