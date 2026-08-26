from fastapi import APIRouter

from app.api.v1.auth.router import profile_router
from app.api.v1.auth.router import router as auth_router

router = APIRouter()

# Include auth routers
router.include_router(auth_router)
router.include_router(profile_router)