"""Protected account endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.account import (
    AccountCreateRequest,
    AccountDataResponse,
    AccountListResponse,
    AccountUpdateRequest,
)
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_account(
    request: AccountCreateRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AccountDataResponse:
    return AccountService(session).create_account(current_user["user_id"], request)


@router.get("", status_code=status.HTTP_200_OK)
async def list_accounts(
    include_archived: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AccountListResponse:
    return AccountService(session).list_accounts(
        current_user["user_id"], include_archived=include_archived
    )


@router.get("/{account_id}", status_code=status.HTTP_200_OK)
async def get_account(
    account_id: str,
    include_archived: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AccountDataResponse:
    return AccountService(session).get_account(
        account_id, current_user["user_id"], include_archived=include_archived
    )


@router.patch("/{account_id}", status_code=status.HTTP_200_OK)
async def update_account(
    account_id: str,
    request: AccountUpdateRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AccountDataResponse:
    return AccountService(session).update_account(account_id, current_user["user_id"], request)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_account(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> None:
    AccountService(session).archive_account(account_id, current_user["user_id"])
