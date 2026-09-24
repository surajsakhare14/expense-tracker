"""API endpoint tests for the 0005 transaction and balance-adjustment routes.

These cover the HTTP contract only — status codes, request validation, the
{"data": ...} envelope, authentication, and user isolation — against the real
router stack. Balance arithmetic and service rules are exercised by the
service tests; here we assert the endpoints wire through and reject bad input.
"""

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

TXN_DATE = "2026-01-15T10:00:00Z"


def register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Txn User"},
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


def _create_category(client: TestClient, headers: dict, name: str, category_type: str) -> str:
    # Suffix with a random token so the name never shadows a seeded system
    # category (e.g. "Salary", "Groceries"), which would return 409.
    response = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": f"{name} {uuid4().hex[:8]}", "type": category_type},
    )
    return response.json()["data"]["id"]


def _create_transaction(
    client: TestClient,
    headers: dict,
    account_id: str,
    category_id: str,
    txn_type: str,
    amount: str,
):
    return client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "account_id": account_id,
            "category_id": category_id,
            "transaction_type": txn_type,
            "amount": amount,
            "transaction_date": TXN_DATE,
        },
    )


# 1. POST creates an INCOME transaction.
def test_create_income_transaction(client: TestClient):
    headers = _auth(register_and_login(client, "txn-income@example.com"))
    account = _create_account(client, headers, "Salary Bank")
    category = _create_category(client, headers, "Salary", "INCOME")
    response = _create_transaction(client, headers, account["id"], category, "INCOME", "500.00")
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["transaction_type"] == "INCOME"
    assert data["status"] == "COMPLETED"
    assert Decimal(data["amount"]) == Decimal("500")


# 2. POST creates an EXPENSE transaction.
def test_create_expense_transaction(client: TestClient):
    headers = _auth(register_and_login(client, "txn-expense@example.com"))
    account = _create_account(client, headers, "Spending Bank")
    category = _create_category(client, headers, "Groceries", "EXPENSE")
    response = _create_transaction(client, headers, account["id"], category, "EXPENSE", "42.50")
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["transaction_type"] == "EXPENSE"
    assert Decimal(data["amount"]) == Decimal("42.50")


# 3. GET lists the user's transactions.
def test_list_transactions_returns_created(client: TestClient):
    headers = _auth(register_and_login(client, "txn-list@example.com"))
    account = _create_account(client, headers, "Bank")
    category = _create_category(client, headers, "Groceries", "EXPENSE")
    _create_transaction(client, headers, account["id"], category, "EXPENSE", "20.00")
    response = client.get("/api/v1/transactions", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["transaction_type"] == "EXPENSE"


# 4. GET /{id} returns the transaction.
def test_get_transaction_by_id(client: TestClient):
    headers = _auth(register_and_login(client, "txn-get@example.com"))
    account = _create_account(client, headers, "Bank")
    category = _create_category(client, headers, "Salary", "INCOME")
    created = _create_transaction(client, headers, account["id"], category, "INCOME", "10.00")
    txn_id = created.json()["data"]["id"]
    response = client.get(f"/api/v1/transactions/{txn_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == txn_id


# 5. PATCH updates an allowed field.
def test_patch_transaction_updates_allowed_field(client: TestClient):
    headers = _auth(register_and_login(client, "txn-patch@example.com"))
    account = _create_account(client, headers, "Bank")
    category = _create_category(client, headers, "Salary", "INCOME")
    created = _create_transaction(client, headers, account["id"], category, "INCOME", "10.00")
    txn_id = created.json()["data"]["id"]
    response = client.patch(
        f"/api/v1/transactions/{txn_id}", headers=headers, json={"description": "Updated note"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["description"] == "Updated note"


# 6. DELETE returns 204 and soft-deletes (the row is then unreadable).
def test_delete_transaction_soft_deletes(client: TestClient):
    headers = _auth(register_and_login(client, "txn-delete@example.com"))
    account = _create_account(client, headers, "Bank")
    category = _create_category(client, headers, "Salary", "INCOME")
    created = _create_transaction(client, headers, account["id"], category, "INCOME", "10.00")
    txn_id = created.json()["data"]["id"]
    assert client.delete(f"/api/v1/transactions/{txn_id}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/transactions/{txn_id}", headers=headers).status_code == 404


# 7. Unknown transaction returns the existing 404 convention.
def test_unknown_transaction_returns_404(client: TestClient):
    headers = _auth(register_and_login(client, "txn-404@example.com"))
    assert client.get(f"/api/v1/transactions/{uuid4()}", headers=headers).status_code == 404


# 8. Invalid transaction input returns 422.
def test_invalid_transaction_input_returns_422(client: TestClient):
    headers = _auth(register_and_login(client, "txn-422@example.com"))
    account = _create_account(client, headers, "Bank")
    response = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "account_id": account["id"],
            "transaction_type": "EXPENSE",
            "amount": "-5",
            "transaction_date": TXN_DATE,
        },
    )
    assert response.status_code == 422


# 9. Client cannot supply status on transaction creation.
def test_status_cannot_be_supplied_on_create(client: TestClient):
    headers = _auth(register_and_login(client, "txn-status@example.com"))
    account = _create_account(client, headers, "Bank")
    category = _create_category(client, headers, "Salary", "INCOME")
    response = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "account_id": account["id"],
            "category_id": category,
            "transaction_type": "INCOME",
            "amount": "10.00",
            "transaction_date": TXN_DATE,
            "status": "PENDING",
        },
    )
    assert response.status_code == 422


# 10. OPENING_BALANCE cannot be created through the normal transaction API.
def test_opening_balance_type_rejected(client: TestClient):
    headers = _auth(register_and_login(client, "txn-opening@example.com"))
    account = _create_account(client, headers, "Bank")
    response = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "account_id": account["id"],
            "transaction_type": "OPENING_BALANCE",
            "amount": "10.00",
            "transaction_date": TXN_DATE,
        },
    )
    assert response.status_code == 422


# 11. BALANCE_ADJUSTMENT cannot be created through the normal transaction API.
def test_balance_adjustment_type_rejected(client: TestClient):
    headers = _auth(register_and_login(client, "txn-adjust-type@example.com"))
    account = _create_account(client, headers, "Bank")
    response = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "account_id": account["id"],
            "transaction_type": "BALANCE_ADJUSTMENT",
            "amount": "10.00",
            "transaction_date": TXN_DATE,
        },
    )
    assert response.status_code == 422


# 12. POST balance-adjustment creates a completed adjustment.
def test_balance_adjustment_creates_completed_adjustment(client: TestClient):
    headers = _auth(register_and_login(client, "adjust-create@example.com"))
    account = _create_account(client, headers, "Bank")
    response = client.post(
        f"/api/v1/accounts/{account['id']}/balance-adjustment",
        headers=headers,
        json={"amount": "250.00", "transaction_date": TXN_DATE},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["transaction_type"] == "BALANCE_ADJUSTMENT"
    assert data["status"] == "COMPLETED"


# 13. Balance adjustment changes the account balance (signed amount applied raw).
def test_balance_adjustment_changes_account_balance(client: TestClient):
    headers = _auth(register_and_login(client, "adjust-balance@example.com"))
    account = _create_account(client, headers, "Bank")
    url = f"/api/v1/accounts/{account['id']}/balance-adjustment"
    client.post(url, headers=headers, json={"amount": "250.00", "transaction_date": TXN_DATE})
    client.post(url, headers=headers, json={"amount": "-150.00", "transaction_date": TXN_DATE})
    refreshed = client.get(f"/api/v1/accounts/{account['id']}", headers=headers).json()["data"]
    assert Decimal(refreshed["current_balance"]) == Decimal("100")


# 14. Balance adjustment cannot accept a category or status from the client.
def test_balance_adjustment_rejects_client_category_or_status(client: TestClient):
    headers = _auth(register_and_login(client, "adjust-forbid@example.com"))
    account = _create_account(client, headers, "Bank")
    url = f"/api/v1/accounts/{account['id']}/balance-adjustment"
    with_category = client.post(
        url,
        headers=headers,
        json={"amount": "10.00", "transaction_date": TXN_DATE, "category_id": str(uuid4())},
    )
    assert with_category.status_code == 422
    with_status = client.post(
        url,
        headers=headers,
        json={"amount": "10.00", "transaction_date": TXN_DATE, "status": "PENDING"},
    )
    assert with_status.status_code == 422


# 23. Transaction endpoints follow the existing auth response convention.
def test_transaction_endpoints_require_valid_authentication(client: TestClient):
    assert client.get("/api/v1/transactions").status_code == 401
    assert client.post(
        "/api/v1/transactions",
        json={
            "account_id": "x",
            "transaction_type": "INCOME",
            "amount": "1",
            "transaction_date": TXN_DATE,
        },
    ).status_code == 401
    assert client.get("/api/v1/transactions", headers=_auth("invalid-token")).status_code == 401


# 24. A user cannot retrieve another user's transaction.
def test_cannot_retrieve_another_users_transaction(client: TestClient):
    owner = _auth(register_and_login(client, "txn-owner@example.com"))
    account = _create_account(client, owner, "Owner Bank")
    category = _create_category(client, owner, "Salary", "INCOME")
    created = _create_transaction(client, owner, account["id"], category, "INCOME", "10.00")
    txn_id = created.json()["data"]["id"]
    other = _auth(register_and_login(client, "txn-intruder@example.com"))
    assert client.get(f"/api/v1/transactions/{txn_id}", headers=other).status_code == 404


# 26. A user cannot use another user's account for a transaction.
def test_cannot_use_another_users_account_for_transaction(client: TestClient):
    owner = _auth(register_and_login(client, "txn-acct-owner@example.com"))
    owner_account = _create_account(client, owner, "Owner Bank")
    other = _auth(register_and_login(client, "txn-acct-intruder@example.com"))
    other_category = _create_category(client, other, "Salary", "INCOME")
    response = _create_transaction(
        client, other, owner_account["id"], other_category, "INCOME", "10.00"
    )
    assert response.status_code == 404
