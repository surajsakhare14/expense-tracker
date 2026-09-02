"""Protected category endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryDataResponse,
    CategoryListResponse,
    CategoryType,
    CategoryUpdateRequest,
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CategoryCreateRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CategoryDataResponse:
    return CategoryService(session).create_category(current_user["user_id"], request)


@router.get("", status_code=status.HTTP_200_OK)
async def list_categories(
    category_type: CategoryType | None = Query(None, alias="type"),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CategoryListResponse:
    return CategoryService(session).list_categories(current_user["user_id"], category_type)


@router.get("/{category_id}", status_code=status.HTTP_200_OK)
async def get_category(
    category_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CategoryDataResponse:
    return CategoryService(session).get_category(category_id, current_user["user_id"])


@router.patch("/{category_id}", status_code=status.HTTP_200_OK)
async def update_category(
    category_id: str,
    request: CategoryUpdateRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CategoryDataResponse:
    return CategoryService(session).update_category(category_id, current_user["user_id"], request)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_category(
    category_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> None:
    CategoryService(session).archive_category(category_id, current_user["user_id"])
