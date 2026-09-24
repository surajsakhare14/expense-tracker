"""Protected transfer endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.transfer import (
    TransferCreateRequest,
    TransferDataResponse,
    TransferListResponse,
    TransferResponse,
    TransferStatus,
    TransferUpdateRequest,
)
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_transfer(
    request: TransferCreateRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> TransferDataResponse:
    transfer = TransferService(session).create_transfer(
        current_user["user_id"],
        source_account_id=request.source_account_id,
        destination_account_id=request.destination_account_id,
        amount=request.amount,
        transfer_date=request.transfer_date,
        description=request.description,
    )
    return TransferDataResponse(data=_to_response(transfer))


@router.get("", status_code=status.HTTP_200_OK)
async def list_transfers(
    account_id: str | None = Query(None),
    transfer_status: TransferStatus | None = Query(None, alias="status"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> TransferListResponse:
    items, _total = TransferService(session).list_transfers(
        current_user["user_id"],
        account_id=account_id,
        status=transfer_status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return TransferListResponse(data=[_to_response(item) for item in items])


@router.get("/{transfer_id}", status_code=status.HTTP_200_OK)
async def get_transfer(
    transfer_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> TransferDataResponse:
    transfer = TransferService(session).get_transfer(transfer_id, current_user["user_id"])
    return TransferDataResponse(data=_to_response(transfer))


@router.patch("/{transfer_id}", status_code=status.HTTP_200_OK)
async def update_transfer(
    transfer_id: str,
    request: TransferUpdateRequest,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> TransferDataResponse:
    values = request.model_dump(exclude_unset=True)
    transfer = TransferService(session).update_transfer(
        transfer_id, current_user["user_id"], values
    )
    return TransferDataResponse(data=_to_response(transfer))


@router.delete("/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transfer(
    transfer_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> None:
    TransferService(session).delete_transfer(transfer_id, current_user["user_id"])


def _to_response(transfer) -> TransferResponse:
    return TransferResponse.model_validate(transfer, from_attributes=True)
