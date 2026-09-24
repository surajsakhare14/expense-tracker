from fastapi import APIRouter

from app.api.v1.accounts.router import router as accounts_router
from app.api.v1.auth.router import profile_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.categories.router import router as categories_router
from app.api.v1.transactions.router import balance_router as balance_adjustment_router
from app.api.v1.transactions.router import router as transactions_router
from app.api.v1.transfers.router import router as transfers_router

router = APIRouter()

# Include auth routers
router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(accounts_router)
router.include_router(categories_router)
router.include_router(transactions_router)
router.include_router(transfers_router)
router.include_router(balance_adjustment_router)