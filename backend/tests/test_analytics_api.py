"""API endpoint tests for the M4 analytics overview route.

These cover the HTTP contract only — status codes, required-parameter and range
validation, the {"data": ...} envelope, authentication, and account ownership —
against the real router stack. The aggregation/eligibility rules themselves are
exercised at the service level in ``test_analytics_overview.py``.
"""

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

START = "2026-01-01"
END = "2026-01-31"
TXN_DATE = "2026-01-15T10:00:00Z"


def register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Overview User"},
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return response.json()["data"]["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_account(client: TestClient, headers: dict, name: str):
    response = client.post(
        "/api/v1/accounts", headers=headers, json={"name": name, "account_type": "BANK"}
    )
    return response.json()["data"]


def _create_category(client: TestClient, headers: dict, name: str, category_type: str) -> str:
    response = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": f"{name} {uuid4().hex[:8]}", "type": category_type},
    )
    return response.json()["data"]["id"]


def _create_transaction(client, headers, account_id, category_id, txn_type, amount):
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


def _adjust(client, headers, account_id, amount):
    return client.post(
        f"/api/v1/accounts/{account_id}/balance-adjustment",
        headers=headers,
        json={"amount": amount, "transaction_date": TXN_DATE},
    )


# The endpoint returns the flat totals inside the project's {"data": ...} envelope.
def test_overview_returns_totals_envelope(client: TestClient):
    headers = _auth(register_and_login(client, "overview@example.com"))
    account = _create_account(client, headers, "Main Bank")
    income = _create_category(client, headers, "Salary", "INCOME")
    expense = _create_category(client, headers, "Groceries", "EXPENSE")
    _create_transaction(client, headers, account["id"], income, "INCOME", "100.00")
    _create_transaction(client, headers, account["id"], expense, "EXPENSE", "40.00")
    _adjust(client, headers, account["id"], "15.00")

    response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {
        "start_date",
        "end_date",
        "total_income",
        "total_expense",
        "net_cash_flow",
        "net_balance_adjustment",
    }
    assert data["start_date"] == START
    assert data["end_date"] == END
    assert Decimal(data["total_income"]) == Decimal("100.00")
    assert Decimal(data["total_expense"]) == Decimal("40.00")
    assert Decimal(data["net_cash_flow"]) == Decimal("60.00")
    assert Decimal(data["net_balance_adjustment"]) == Decimal("15.00")


# Missing start_date/end_date is a 422 with the dedicated code.
def test_overview_requires_date_range(client: TestClient):
    headers = _auth(register_and_login(client, "overview-nodate@example.com"))
    response = client.get("/api/v1/analytics/overview", headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_DATE_RANGE_REQUIRED"


# start_date after end_date is rejected by the shared filter validation.
def test_overview_rejects_inverted_range(client: TestClient):
    headers = _auth(register_and_login(client, "overview-badrange@example.com"))
    response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
        params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_INVALID_DATE_RANGE"


# The endpoint is authenticated.
def test_overview_requires_authentication(client: TestClient):
    response = client.get(
        "/api/v1/analytics/overview",
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 401


# A caller cannot scope the report to another user's account.
def test_overview_rejects_foreign_account(client: TestClient):
    owner_headers = _auth(register_and_login(client, "overview-owner@example.com"))
    owner_account = _create_account(client, owner_headers, "Owner Bank")
    other_headers = _auth(register_and_login(client, "overview-other@example.com"))

    response = client.get(
        "/api/v1/analytics/overview",
        headers=other_headers,
        params={"start_date": START, "end_date": END, "account_id": owner_account["id"]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


# The income endpoint returns the total and per-category breakdown in the envelope.
def test_income_returns_breakdown_envelope(client: TestClient):
    headers = _auth(register_and_login(client, "income@example.com"))
    account = _create_account(client, headers, "Main Bank")
    salary = _create_category(client, headers, "Salary", "INCOME")
    interest = _create_category(client, headers, "Interest", "INCOME")
    _create_transaction(client, headers, account["id"], salary, "INCOME", "75.00")
    _create_transaction(client, headers, account["id"], interest, "INCOME", "25.00")

    response = client.get(
        "/api/v1/analytics/income",
        headers=headers,
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"start_date", "end_date", "total_income", "categories"}
    assert data["start_date"] == START
    assert data["end_date"] == END
    assert Decimal(data["total_income"]) == Decimal("100.00")

    by_id = {row["category_id"]: row for row in data["categories"]}
    assert set(by_id) == {salary, interest}
    assert set(by_id[salary]) == {"category_id", "category_name", "amount", "percentage"}
    assert Decimal(by_id[salary]["amount"]) == Decimal("75.00")
    assert Decimal(by_id[salary]["percentage"]) == Decimal("75.00")
    assert Decimal(by_id[interest]["percentage"]) == Decimal("25.00")


# Missing start_date/end_date is a 422 with the dedicated code.
def test_income_requires_date_range(client: TestClient):
    headers = _auth(register_and_login(client, "income-nodate@example.com"))
    response = client.get("/api/v1/analytics/income", headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_DATE_RANGE_REQUIRED"


# start_date after end_date is rejected by the shared filter validation.
def test_income_rejects_inverted_range(client: TestClient):
    headers = _auth(register_and_login(client, "income-badrange@example.com"))
    response = client.get(
        "/api/v1/analytics/income",
        headers=headers,
        params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_INVALID_DATE_RANGE"


# The endpoint is authenticated.
def test_income_requires_authentication(client: TestClient):
    response = client.get(
        "/api/v1/analytics/income",
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 401


# A caller cannot scope the report to another user's account.
def test_income_rejects_foreign_account(client: TestClient):
    owner_headers = _auth(register_and_login(client, "income-owner@example.com"))
    owner_account = _create_account(client, owner_headers, "Owner Bank")
    other_headers = _auth(register_and_login(client, "income-other@example.com"))

    response = client.get(
        "/api/v1/analytics/income",
        headers=other_headers,
        params={"start_date": START, "end_date": END, "account_id": owner_account["id"]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


# The expenses endpoint returns the total and per-category breakdown in the envelope.
def test_expenses_returns_breakdown_envelope(client: TestClient):
    headers = _auth(register_and_login(client, "expenses@example.com"))
    account = _create_account(client, headers, "Main Bank")
    groceries = _create_category(client, headers, "Groceries", "EXPENSE")
    rent = _create_category(client, headers, "Rent", "EXPENSE")
    _create_transaction(client, headers, account["id"], groceries, "EXPENSE", "75.00")
    _create_transaction(client, headers, account["id"], rent, "EXPENSE", "25.00")

    response = client.get(
        "/api/v1/analytics/expenses",
        headers=headers,
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"start_date", "end_date", "total_expense", "categories"}
    assert data["start_date"] == START
    assert data["end_date"] == END
    assert Decimal(data["total_expense"]) == Decimal("100.00")

    by_id = {row["category_id"]: row for row in data["categories"]}
    assert set(by_id) == {groceries, rent}
    assert set(by_id[groceries]) == {"category_id", "category_name", "amount", "percentage"}
    assert Decimal(by_id[groceries]["amount"]) == Decimal("75.00")
    assert Decimal(by_id[groceries]["percentage"]) == Decimal("75.00")
    assert Decimal(by_id[rent]["percentage"]) == Decimal("25.00")


# Missing start_date/end_date is a 422 with the dedicated code.
def test_expenses_requires_date_range(client: TestClient):
    headers = _auth(register_and_login(client, "expenses-nodate@example.com"))
    response = client.get("/api/v1/analytics/expenses", headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_DATE_RANGE_REQUIRED"


# start_date after end_date is rejected by the shared filter validation.
def test_expenses_rejects_inverted_range(client: TestClient):
    headers = _auth(register_and_login(client, "expenses-badrange@example.com"))
    response = client.get(
        "/api/v1/analytics/expenses",
        headers=headers,
        params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_INVALID_DATE_RANGE"


# The endpoint is authenticated.
def test_expenses_requires_authentication(client: TestClient):
    response = client.get(
        "/api/v1/analytics/expenses",
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 401


# A caller cannot scope the report to another user's account.
def test_expenses_rejects_foreign_account(client: TestClient):
    owner_headers = _auth(register_and_login(client, "expenses-owner@example.com"))
    owner_account = _create_account(client, owner_headers, "Owner Bank")
    other_headers = _auth(register_and_login(client, "expenses-other@example.com"))

    response = client.get(
        "/api/v1/analytics/expenses",
        headers=other_headers,
        params={"start_date": START, "end_date": END, "account_id": owner_account["id"]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


# The categories endpoint returns per-category totals, counts and shares in the envelope.
def test_categories_returns_breakdown_envelope(client: TestClient):
    headers = _auth(register_and_login(client, "categories@example.com"))
    account = _create_account(client, headers, "Main Bank")
    groceries = _create_category(client, headers, "Groceries", "EXPENSE")
    rent = _create_category(client, headers, "Rent", "EXPENSE")
    _create_transaction(client, headers, account["id"], groceries, "EXPENSE", "50.00")
    _create_transaction(client, headers, account["id"], groceries, "EXPENSE", "25.00")
    _create_transaction(client, headers, account["id"], rent, "EXPENSE", "25.00")

    response = client.get(
        "/api/v1/analytics/categories",
        headers=headers,
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"start_date", "end_date", "total_expense", "categories"}
    assert data["start_date"] == START
    assert data["end_date"] == END
    assert Decimal(data["total_expense"]) == Decimal("100.00")

    # Ordered by amount descending: groceries (75.00) before rent (25.00).
    assert [row["category_id"] for row in data["categories"]] == [groceries, rent]
    by_id = {row["category_id"]: row for row in data["categories"]}
    assert set(by_id[groceries]) == {
        "category_id",
        "category_name",
        "amount",
        "percentage",
        "transaction_count",
    }
    assert Decimal(by_id[groceries]["amount"]) == Decimal("75.00")
    assert Decimal(by_id[groceries]["percentage"]) == Decimal("75.00")
    assert by_id[groceries]["transaction_count"] == 2
    assert by_id[rent]["transaction_count"] == 1


# Missing start_date/end_date is a 422 with the dedicated code.
def test_categories_requires_date_range(client: TestClient):
    headers = _auth(register_and_login(client, "categories-nodate@example.com"))
    response = client.get("/api/v1/analytics/categories", headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_DATE_RANGE_REQUIRED"


# start_date after end_date is rejected by the shared filter validation.
def test_categories_rejects_inverted_range(client: TestClient):
    headers = _auth(register_and_login(client, "categories-badrange@example.com"))
    response = client.get(
        "/api/v1/analytics/categories",
        headers=headers,
        params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_INVALID_DATE_RANGE"


# The endpoint is authenticated.
def test_categories_requires_authentication(client: TestClient):
    response = client.get(
        "/api/v1/analytics/categories",
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 401


# A caller cannot scope the report to another user's account.
def test_categories_rejects_foreign_account(client: TestClient):
    owner_headers = _auth(register_and_login(client, "categories-owner@example.com"))
    owner_account = _create_account(client, owner_headers, "Owner Bank")
    other_headers = _auth(register_and_login(client, "categories-other@example.com"))

    response = client.get(
        "/api/v1/analytics/categories",
        headers=other_headers,
        params={"start_date": START, "end_date": END, "account_id": owner_account["id"]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


def _create_account_full(
    client, headers, name, account_type="BANK", opening_balance=None, currency="INR"
):
    body = {"name": name, "account_type": account_type, "currency": currency}
    if opening_balance is not None:
        body["opening_balance"] = opening_balance
    response = client.post("/api/v1/accounts", headers=headers, json=body)
    return response.json()["data"]


# The accounts endpoint returns the snapshot and per-currency totals in the envelope.
def test_accounts_returns_snapshot_envelope(client: TestClient):
    headers = _auth(register_and_login(client, "accounts@example.com"))
    _create_account_full(client, headers, "HDFC Bank", "BANK", "50000.00")
    _create_account_full(client, headers, "Amazon ICICI", "CREDIT_CARD", "12000.00")

    response = client.get("/api/v1/analytics/accounts", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"accounts", "totals_by_currency"}

    by_type = {row["account_type"]: row for row in data["accounts"]}
    assert set(by_type) == {"BANK", "CREDIT_CARD"}
    assert set(by_type["BANK"]) == {
        "account_id",
        "account_name",
        "account_type",
        "currency",
        "current_balance",
        "financial_position",
        "is_archived",
    }
    assert Decimal(str(by_type["BANK"]["financial_position"])) == Decimal("50000.00")
    assert Decimal(str(by_type["CREDIT_CARD"]["financial_position"])) == Decimal("-12000.00")

    totals = {row["currency"]: row for row in data["totals_by_currency"]}
    assert Decimal(str(totals["INR"]["total_assets"])) == Decimal("50000.00")
    assert Decimal(str(totals["INR"]["total_liabilities"])) == Decimal("12000.00")
    assert Decimal(str(totals["INR"]["net_position"])) == Decimal("38000.00")


# The snapshot needs no date range (unlike the period reports) and still returns 200.
def test_accounts_requires_no_date_range(client: TestClient):
    headers = _auth(register_and_login(client, "accounts-nodate@example.com"))
    _create_account_full(client, headers, "Main Bank", "BANK", "100.00")

    response = client.get("/api/v1/analytics/accounts", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["accounts"][0]["account_name"] == "Main Bank"


# The endpoint is authenticated.
def test_accounts_requires_authentication(client: TestClient):
    response = client.get("/api/v1/analytics/accounts")
    assert response.status_code == 401


# A caller cannot scope the report to another user's account.
def test_accounts_rejects_foreign_account(client: TestClient):
    owner_headers = _auth(register_and_login(client, "accounts-owner@example.com"))
    owner_account = _create_account(client, owner_headers, "Owner Bank")
    other_headers = _auth(register_and_login(client, "accounts-other@example.com"))

    response = client.get(
        "/api/v1/analytics/accounts",
        headers=other_headers,
        params={"account_id": owner_account["id"]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


# The trends endpoint returns the monthly time-series inside the envelope.
def test_trends_returns_timeseries_envelope(client: TestClient):
    headers = _auth(register_and_login(client, "trends@example.com"))
    account = _create_account(client, headers, "Main Bank")
    income = _create_category(client, headers, "Salary", "INCOME")
    expense = _create_category(client, headers, "Groceries", "EXPENSE")
    _create_transaction(client, headers, account["id"], income, "INCOME", "100.00")
    _create_transaction(client, headers, account["id"], expense, "EXPENSE", "40.00")

    response = client.get(
        "/api/v1/analytics/trends",
        headers=headers,
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"start_date", "end_date", "group_by", "trends"}
    assert data["start_date"] == START
    assert data["end_date"] == END
    assert data["group_by"] == "month"

    assert len(data["trends"]) == 1
    row = data["trends"][0]
    assert set(row) == {"period", "currency", "income", "expense", "net_cash_flow"}
    assert row["period"] == "2026-01"
    assert row["currency"] == "INR"
    assert Decimal(str(row["income"])) == Decimal("100.00")
    assert Decimal(str(row["expense"])) == Decimal("40.00")
    assert Decimal(str(row["net_cash_flow"])) == Decimal("60.00")


# Missing start_date/end_date is a 422 with the dedicated code.
def test_trends_requires_date_range(client: TestClient):
    headers = _auth(register_and_login(client, "trends-nodate@example.com"))
    response = client.get("/api/v1/analytics/trends", headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_DATE_RANGE_REQUIRED"


# start_date after end_date is rejected by the shared filter validation.
def test_trends_rejects_inverted_range(client: TestClient):
    headers = _auth(register_and_login(client, "trends-badrange@example.com"))
    response = client.get(
        "/api/v1/analytics/trends",
        headers=headers,
        params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_INVALID_DATE_RANGE"


# An unsupported group_by is rejected with the dedicated 422 code.
def test_trends_rejects_unsupported_group_by(client: TestClient):
    headers = _auth(register_and_login(client, "trends-groupby@example.com"))
    response = client.get(
        "/api/v1/analytics/trends",
        headers=headers,
        params={"start_date": START, "end_date": END, "group_by": "week"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYTICS_INVALID_GROUP_BY"


# group_by defaults to "month" when the parameter is omitted.
def test_trends_defaults_group_by_to_month(client: TestClient):
    headers = _auth(register_and_login(client, "trends-default@example.com"))
    response = client.get(
        "/api/v1/analytics/trends",
        headers=headers,
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 200
    assert response.json()["data"]["group_by"] == "month"


# The endpoint is authenticated.
def test_trends_requires_authentication(client: TestClient):
    response = client.get(
        "/api/v1/analytics/trends",
        params={"start_date": START, "end_date": END},
    )
    assert response.status_code == 401


# A caller cannot scope the report to another user's account.
def test_trends_rejects_foreign_account(client: TestClient):
    owner_headers = _auth(register_and_login(client, "trends-owner@example.com"))
    owner_account = _create_account(client, owner_headers, "Owner Bank")
    other_headers = _auth(register_and_login(client, "trends-other@example.com"))

    response = client.get(
        "/api/v1/analytics/trends",
        headers=other_headers,
        params={"start_date": START, "end_date": END, "account_id": owner_account["id"]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"




