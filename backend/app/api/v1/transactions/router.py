"""Protected transaction endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.transaction import (
    BalanceAdjustmentRequest,
    TransactionCreateRequest,
    TransactionDataResponse,
    TransactionListResponse,
    TransactionResponse,
    TransactionStatus,
    TransactionType,
    TransactionUpdateRequest,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Balance adjustment lives under the account resource but is a transaction
# operation, so it ships from this module and is registered separately.
balance_router = APIRouter(prefix="/accounts", tags=["transactions"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    request: TransactionCreateRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> TransactionDataResponse:
    transaction = TransactionService(session).create_transaction(
        current_user["user_id"],
        account_id=request.account_id,
        transaction_type=request.transaction_type,
        amount=request.amount,
        transaction_date=request.transaction_date,
        category_id=request.category_id,
        description=request.description,
        merchant_name=request.merchant_name,
    )
    return TransactionDataResponse(data=_to_response(transaction))


@router.get("", status_code=status.HTTP_200_OK)
async def list_transactions(
    account_id: str | None = Query(None),
    category_id: str | None = Query(None),
    transaction_type: TransactionType | None = Query(None),
    transaction_status: TransactionStatus | None = Query(None, alias="status"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> TransactionListResponse:
    items, _total = TransactionService(session).list_transactions(
        current_user["user_id"],
        account_id=account_id,
        category_id=category_id,
        transaction_type=transaction_type,
        status=transaction_status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return TransactionListResponse(data=[_to_response(item) for item in items])


@router.get("/{transaction_id}", status_code=status.HTTP_200_OK)
async def get_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> TransactionDataResponse:
    transaction = TransactionService(session).get_transaction(
        transaction_id, current_user["user_id"]
    )
    return TransactionDataResponse(data=_to_response(transaction))


@router.patch("/{transaction_id}", status_code=status.HTTP_200_OK)
async def update_transaction(
    transaction_id: str,
    request: TransactionUpdateRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> TransactionDataResponse:
    values = request.model_dump(exclude_unset=True)
    transaction = TransactionService(session).update_transaction(
        transaction_id, current_user["user_id"], values
    )
    return TransactionDataResponse(data=_to_response(transaction))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> None:
    TransactionService(session).delete_transaction(transaction_id, current_user["user_id"])


@balance_router.post("/{account_id}/balance-adjustment", status_code=status.HTTP_201_CREATED)
async def create_balance_adjustment(
    account_id: str,
    request: BalanceAdjustmentRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> TransactionDataResponse:
    transaction = TransactionService(session).create_transaction(
        current_user["user_id"],
        account_id=account_id,
        transaction_type="BALANCE_ADJUSTMENT",
        amount=request.amount,
        transaction_date=request.transaction_date,
        category_id=None,
        description=request.description,
    )
    return TransactionDataResponse(data=_to_response(transaction))


def _to_response(transaction) -> TransactionResponse:
    return TransactionResponse.model_validate(transaction, from_attributes=True)
