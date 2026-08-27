"""Tests for the Accounts domain."""

from decimal import Decimal

from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Account User"},
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return response.json()["data"]["access_token"]


def test_create_account_initializes_zero_balance(client: TestClient):
    token = register_and_login(client, "accounts@example.com")
    response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "HDFC Bank", "account_type": "BANK", "currency": "inr"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "HDFC Bank"
    assert data["currency"] == "INR"
    assert Decimal(data["current_balance"]) == Decimal("0")


def test_account_crud_and_archive(client: TestClient):
    token = register_and_login(client, "crud-accounts@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/accounts", headers=headers, json={"name": "Cash", "account_type": "CASH"}
    )
    account_id = created.json()["data"]["id"]

    updated = client.patch(
        f"/api/v1/accounts/{account_id}", headers=headers, json={"name": "Wallet Cash"}
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Wallet Cash"

    archived = client.delete(f"/api/v1/accounts/{account_id}", headers=headers)
    assert archived.status_code == 204
    assert client.get(f"/api/v1/accounts/{account_id}", headers=headers).status_code == 404
    included = client.get(
        f"/api/v1/accounts/{account_id}?include_archived=true", headers=headers
    )
    assert included.status_code == 200
    assert included.json()["data"]["is_active"] is False


def test_active_account_names_are_case_insensitive_and_archived_names_reusable(client: TestClient):
    token = register_and_login(client, "names@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    first = client.post(
        "/api/v1/accounts", headers=headers, json={"name": "HDFC", "account_type": "BANK"}
    )
    assert first.status_code == 201
    duplicate = client.post(
        "/api/v1/accounts", headers=headers, json={"name": " hdfc ", "account_type": "BANK"}
    )
    assert duplicate.status_code == 409
    account_id = first.json()["data"]["id"]
    assert client.delete(f"/api/v1/accounts/{account_id}", headers=headers).status_code == 204
    reused = client.post(
        "/api/v1/accounts", headers=headers, json={"name": "HDFC", "account_type": "BANK"}
    )
    assert reused.status_code == 201


def test_account_rejects_invalid_type_currency_and_balance_override(client: TestClient):
    token = register_and_login(client, "validation@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    invalid_type = client.post(
        "/api/v1/accounts", headers=headers, json={"name": "UPI", "account_type": "UPI_ACCOUNT"}
    )
    assert invalid_type.status_code == 422
    invalid_currency = client.post(
        "/api/v1/accounts",
        headers=headers,
        json={"name": "Bad", "account_type": "BANK", "currency": "US"},
    )
    assert invalid_currency.status_code == 422
    balance_override = client.post(
        "/api/v1/accounts",
        headers=headers,
        json={"name": "Should Be Zero", "account_type": "BANK", "current_balance": 1000},
    )
    assert balance_override.status_code == 201
    assert Decimal(balance_override.json()["data"]["current_balance"]) == Decimal("0")


def test_accounts_are_user_isolated(client: TestClient):
    owner_token = register_and_login(client, "owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    created = client.post(
        "/api/v1/accounts", headers=owner_headers, json={"name": "Private", "account_type": "BANK"}
    )
    account_id = created.json()["data"]["id"]
    other_token = register_and_login(client, "other@example.com")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/v1/accounts/{account_id}", headers=other_headers).status_code == 404
    assert client.patch(
        f"/api/v1/accounts/{account_id}", headers=other_headers, json={"name": "Stolen"}
    ).status_code == 404


def test_list_accounts_returns_active_only_by_default_and_orders_newest_first(client: TestClient):
    token = register_and_login(client, "list@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    first = client.post(
        "/api/v1/accounts", headers=headers, json={"name": "First", "account_type": "BANK"}
    ).json()["data"]
    second = client.post(
        "/api/v1/accounts", headers=headers, json={"name": "Second", "account_type": "CASH"}
    ).json()["data"]
    client.delete(f"/api/v1/accounts/{first['id']}", headers=headers)

    active = client.get("/api/v1/accounts", headers=headers)
    assert active.status_code == 200
    assert [account["id"] for account in active.json()["data"]] == [second["id"]]

    archived = client.get("/api/v1/accounts?include_archived=true", headers=headers)
    assert archived.status_code == 200
    archived_ids = [account["id"] for account in archived.json()["data"]]
    repeated = client.get("/api/v1/accounts?include_archived=true", headers=headers)
    assert archived_ids == [account["id"] for account in repeated.json()["data"]]
    assert set(archived_ids) == {first["id"], second["id"]}


def test_list_accounts_is_user_isolated(client: TestClient):
    owner_token = register_and_login(client, "list-owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    client.post(
        "/api/v1/accounts", headers=owner_headers, json={"name": "Owner", "account_type": "BANK"}
    )
    other_token = register_and_login(client, "list-other@example.com")
    response = client.get(
        "/api/v1/accounts", headers={"Authorization": f"Bearer {other_token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_all_approved_account_types_are_supported(client: TestClient):
    token = register_and_login(client, "types@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    account_types = ["BANK", "CASH", "CREDIT_CARD", "WALLET", "OTHER"]
    for account_type in account_types:
        response = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={"name": account_type, "account_type": account_type},
        )
        assert response.status_code == 201
        assert response.json()["data"]["account_type"] == account_type


def test_account_endpoints_require_authentication(client: TestClient):
    assert client.get("/api/v1/accounts").status_code == 401
    assert client.post(
        "/api/v1/accounts", json={"name": "No Auth", "account_type": "BANK"}
    ).status_code == 401


def test_account_endpoints_reject_invalid_bearer_token(client: TestClient):
    headers = {"Authorization": "Bearer invalid-token"}
    assert client.get("/api/v1/accounts", headers=headers).status_code == 401
    assert client.post(
        "/api/v1/accounts",
        headers=headers,
        json={"name": "Invalid Auth", "account_type": "BANK"},
    ).status_code == 401
