"""API endpoint tests for the 0005 transfer routes.

These cover the HTTP contract only — status codes, request validation, the
{"data": ...} envelope, authentication, and user isolation — against the real
router stack. Balance arithmetic and concurrency are exercised by the transfer
service tests; here we assert the endpoints wire through and reject bad input.
"""

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

TRANSFER_DATE = "2026-01-15T10:00:00Z"


def register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Transfer User"},
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return response.json()["data"]["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_account(client: TestClient, headers: dict, name: str, account_type: str = "BANK"):
    response = client.post(
        "/api/v1/accounts", headers=headers, json={"name": name, "account_type": account_type}
    )
    return response.json()["data"]


def _adjust(client: TestClient, headers: dict, account_id: str, amount: str) -> None:
    client.post(
        f"/api/v1/accounts/{account_id}/balance-adjustment",
        headers=headers,
        json={"amount": amount, "transaction_date": TRANSFER_DATE},
    )


def _create_transfer(client: TestClient, headers: dict, source_id: str, dest_id: str, amount: str):
    return client.post(
        "/api/v1/transfers",
        headers=headers,
        json={
            "source_account_id": source_id,
            "destination_account_id": dest_id,
            "amount": amount,
            "transfer_date": TRANSFER_DATE,
        },
    )


def _balance(client: TestClient, headers: dict, account_id: str) -> Decimal:
    data = client.get(f"/api/v1/accounts/{account_id}", headers=headers).json()["data"]
    return Decimal(data["current_balance"])


# 15. POST creates a completed transfer.
def test_create_transfer_completed(client: TestClient):
    headers = _auth(register_and_login(client, "tf-create@example.com"))
    source = _create_account(client, headers, "Source")
    dest = _create_account(client, headers, "Dest")
    response = _create_transfer(client, headers, source["id"], dest["id"], "100.00")
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "COMPLETED"
    assert Decimal(data["amount"]) == Decimal("100")


# 16. GET lists the user's transfers.
def test_list_transfers_returns_created(client: TestClient):
    headers = _auth(register_and_login(client, "tf-list@example.com"))
    source = _create_account(client, headers, "Source")
    dest = _create_account(client, headers, "Dest")
    _create_transfer(client, headers, source["id"], dest["id"], "25.00")
    response = client.get("/api/v1/transfers", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


# 17. GET /{id} returns the transfer.
def test_get_transfer_by_id(client: TestClient):
    headers = _auth(register_and_login(client, "tf-get@example.com"))
    source = _create_account(client, headers, "Source")
    dest = _create_account(client, headers, "Dest")
    created = _create_transfer(client, headers, source["id"], dest["id"], "25.00")
    transfer_id = created.json()["data"]["id"]
    response = client.get(f"/api/v1/transfers/{transfer_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == transfer_id


# 18. PATCH updates amount / description / date.
def test_patch_transfer_updates_editable_fields(client: TestClient):
    headers = _auth(register_and_login(client, "tf-patch@example.com"))
    source = _create_account(client, headers, "Source")
    dest = _create_account(client, headers, "Dest")
    created = _create_transfer(client, headers, source["id"], dest["id"], "25.00")
    transfer_id = created.json()["data"]["id"]
    response = client.patch(
        f"/api/v1/transfers/{transfer_id}",
        headers=headers,
        json={"amount": "40.00", "description": "Rent split", "transfer_date": TRANSFER_DATE},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert Decimal(data["amount"]) == Decimal("40")
    assert data["description"] == "Rent split"


# 19. PATCH cannot change the source or destination account.
def test_patch_transfer_cannot_change_accounts(client: TestClient):
    headers = _auth(register_and_login(client, "tf-immutable@example.com"))
    source = _create_account(client, headers, "Source")
    dest = _create_account(client, headers, "Dest")
    other = _create_account(client, headers, "Other")
    created = _create_transfer(client, headers, source["id"], dest["id"], "25.00")
    transfer_id = created.json()["data"]["id"]
    assert client.patch(
        f"/api/v1/transfers/{transfer_id}",
        headers=headers,
        json={"source_account_id": other["id"]},
    ).status_code == 422
    assert client.patch(
        f"/api/v1/transfers/{transfer_id}",
        headers=headers,
        json={"destination_account_id": other["id"]},
    ).status_code == 422


# 20. DELETE returns 204 and reverses the transfer's balance effect.
def test_delete_transfer_reverses_effect(client: TestClient):
    headers = _auth(register_and_login(client, "tf-delete@example.com"))
    source = _create_account(client, headers, "Source")
    dest = _create_account(client, headers, "Dest")
    _adjust(client, headers, source["id"], "1000.00")
    created = _create_transfer(client, headers, source["id"], dest["id"], "300.00")
    transfer_id = created.json()["data"]["id"]
    assert _balance(client, headers, source["id"]) == Decimal("700")
    assert _balance(client, headers, dest["id"]) == Decimal("300")
    assert client.delete(f"/api/v1/transfers/{transfer_id}", headers=headers).status_code == 204
    assert _balance(client, headers, source["id"]) == Decimal("1000")
    assert _balance(client, headers, dest["id"]) == Decimal("0")


# 21. Unknown transfer returns the existing 404 convention.
def test_unknown_transfer_returns_404(client: TestClient):
    headers = _auth(register_and_login(client, "tf-404@example.com"))
    assert client.get(f"/api/v1/transfers/{uuid4()}", headers=headers).status_code == 404


# 22. Invalid transfer input returns 422.
def test_invalid_transfer_input_returns_422(client: TestClient):
    headers = _auth(register_and_login(client, "tf-422@example.com"))
    source = _create_account(client, headers, "Source")
    dest = _create_account(client, headers, "Dest")
    response = client.post(
        "/api/v1/transfers",
        headers=headers,
        json={
            "source_account_id": source["id"],
            "destination_account_id": dest["id"],
            "amount": "0",
            "transfer_date": TRANSFER_DATE,
        },
    )
    assert response.status_code == 422


# 23. Transfer endpoints follow the existing auth response convention.
def test_transfer_endpoints_require_valid_authentication(client: TestClient):
    assert client.get("/api/v1/transfers").status_code == 401
    assert client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": "a",
            "destination_account_id": "b",
            "amount": "1",
            "transfer_date": TRANSFER_DATE,
        },
    ).status_code == 401
    assert client.get("/api/v1/transfers", headers=_auth("invalid-token")).status_code == 401


# 25. A user cannot retrieve another user's transfer.
def test_cannot_retrieve_another_users_transfer(client: TestClient):
    owner = _auth(register_and_login(client, "tf-owner@example.com"))
    source = _create_account(client, owner, "Source")
    dest = _create_account(client, owner, "Dest")
    created = _create_transfer(client, owner, source["id"], dest["id"], "25.00")
    transfer_id = created.json()["data"]["id"]
    other = _auth(register_and_login(client, "tf-intruder@example.com"))
    assert client.get(f"/api/v1/transfers/{transfer_id}", headers=other).status_code == 404


# 27. A user cannot use another user's account in a transfer.
def test_cannot_use_another_users_account_in_transfer(client: TestClient):
    owner = _auth(register_and_login(client, "tf-acct-owner@example.com"))
    owner_account = _create_account(client, owner, "Owner Bank")
    other = _auth(register_and_login(client, "tf-acct-intruder@example.com"))
    other_account = _create_account(client, other, "Intruder Bank")
    response = _create_transfer(client, other, other_account["id"], owner_account["id"], "10.00")
    assert response.status_code == 404
