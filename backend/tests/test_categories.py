"""Tests for the Categories domain."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category

SYSTEM_FOOD_ID = "10000000-0000-0000-0000-000000000001"


def register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Category User"},
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return response.json()["data"]["access_token"]


def test_create_list_filter_update_and_archive_custom_category(
    client: TestClient, session: Session
):
    assert session.get(Category, SYSTEM_FOOD_ID) is not None
    token = register_and_login(client, "categories@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/categories", headers=headers, json={"name": " Dining ", "type": "EXPENSE"}
    )
    assert created.status_code == 201
    category = created.json()["data"]
    assert category["name"] == "Dining"
    assert category["type"] == "EXPENSE"
    assert category["is_system"] is False

    listed = client.get("/api/v1/categories?type=EXPENSE", headers=headers)
    assert listed.status_code == 200
    assert {"Food", "Dining"}.issubset({entry["name"] for entry in listed.json()["data"]})

    updated = client.patch(
        f"/api/v1/categories/{category['id']}", headers=headers, json={"name": "Restaurants"}
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Restaurants"

    archived = client.delete(f"/api/v1/categories/{category['id']}", headers=headers)
    assert archived.status_code == 204
    listed_after_archive = client.get("/api/v1/categories", headers=headers)
    assert "Restaurants" not in {entry["name"] for entry in listed_after_archive.json()["data"]}


def test_custom_category_type_can_change_before_transaction_model_exists(client: TestClient):
    token = register_and_login(client, "type-change@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/categories", headers=headers, json={"name": "Correction", "type": "EXPENSE"}
    )
    category_id = created.json()["data"]["id"]
    updated = client.patch(
        f"/api/v1/categories/{category_id}", headers=headers, json={"type": "INCOME"}
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["type"] == "INCOME"


def test_active_custom_category_names_are_case_insensitive_and_reusable(client: TestClient):
    token = register_and_login(client, "names-categories@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    first = client.post(
        "/api/v1/categories", headers=headers, json={"name": "Dining", "type": "EXPENSE"}
    )
    assert first.status_code == 201
    duplicate = client.post(
        "/api/v1/categories", headers=headers, json={"name": " dining ", "type": "EXPENSE"}
    )
    assert duplicate.status_code == 409
    different_type = client.post(
        "/api/v1/categories", headers=headers, json={"name": "Dining", "type": "INCOME"}
    )
    assert different_type.status_code == 201
    archived = client.delete(
        f"/api/v1/categories/{first.json()['data']['id']}", headers=headers
    )
    assert archived.status_code == 204
    reused = client.post(
        "/api/v1/categories", headers=headers, json={"name": "Dining", "type": "EXPENSE"}
    )
    assert reused.status_code == 201


def test_custom_category_cannot_shadow_active_system_category(client: TestClient):
    token = register_and_login(client, "system-name-conflict@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    exact_match = client.post(
        "/api/v1/categories", headers=headers, json={"name": "Food", "type": "EXPENSE"}
    )
    assert exact_match.status_code == 409

    case_insensitive_match = client.post(
        "/api/v1/categories", headers=headers, json={"name": "food", "type": "EXPENSE"}
    )
    assert case_insensitive_match.status_code == 409

    different_type = client.post(
        "/api/v1/categories", headers=headers, json={"name": "Food", "type": "INCOME"}
    )
    assert different_type.status_code == 201


def test_custom_category_name_scope_is_user_specific(client: TestClient):
    first_token = register_and_login(client, "first-category-user@example.com")
    first_headers = {"Authorization": f"Bearer {first_token}"}
    first = client.post(
        "/api/v1/categories", headers=first_headers, json={"name": "Gaming", "type": "EXPENSE"}
    )
    assert first.status_code == 201

    same_user_exact = client.post(
        "/api/v1/categories", headers=first_headers, json={"name": "Gaming", "type": "EXPENSE"}
    )
    assert same_user_exact.status_code == 409

    same_user_case_insensitive = client.post(
        "/api/v1/categories", headers=first_headers, json={"name": "gaming", "type": "EXPENSE"}
    )
    assert same_user_case_insensitive.status_code == 409

    second_token = register_and_login(client, "second-category-user@example.com")
    second = client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {second_token}"},
        json={"name": "Gaming", "type": "EXPENSE"},
    )
    assert second.status_code == 201


def test_system_categories_are_immutable(client: TestClient, session: Session):
    assert session.get(Category, SYSTEM_FOOD_ID) is not None
    token = register_and_login(client, "system-categories@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.patch(
        f"/api/v1/categories/{SYSTEM_FOOD_ID}", headers=headers, json={"name": "Meals"}
    ).status_code == 409
    assert client.delete(f"/api/v1/categories/{SYSTEM_FOOD_ID}", headers=headers).status_code == 409


def test_categories_are_user_isolated(client: TestClient):
    owner_token = register_and_login(client, "category-owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    created = client.post(
        "/api/v1/categories", headers=owner_headers, json={"name": "Private", "type": "EXPENSE"}
    )
    category_id = created.json()["data"]["id"]
    other_token = register_and_login(client, "category-other@example.com")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/v1/categories/{category_id}", headers=other_headers).status_code == 404
    assert client.patch(
        f"/api/v1/categories/{category_id}", headers=other_headers, json={"name": "Stolen"}
    ).status_code == 404
    assert (
        client.delete(f"/api/v1/categories/{category_id}", headers=other_headers).status_code == 404
    )
    listed = client.get("/api/v1/categories", headers=other_headers).json()["data"]
    assert "Private" not in {category["name"] for category in listed}


def test_categories_reject_invalid_input_and_internal_fields(client: TestClient):
    token = register_and_login(client, "category-validation@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post(
        "/api/v1/categories", headers=headers, json={"name": "Bad", "type": "TRANSFER"}
    ).status_code == 422
    assert client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Bad", "type": "EXPENSE", "user_id": "forbidden"},
    ).status_code == 422
    assert client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Bad", "type": "EXPENSE", "parent_id": str(uuid4())},
    ).status_code == 422


def test_category_endpoints_require_valid_authentication(client: TestClient):
    assert client.get("/api/v1/categories").status_code == 401
    assert client.post(
        "/api/v1/categories", json={"name": "No Auth", "type": "EXPENSE"}
    ).status_code == 401
    assert client.get(
        "/api/v1/categories", headers={"Authorization": "Bearer invalid-token"}
    ).status_code == 401


def test_category_database_constraints(session: Session):
    invalid_scope = Category(
        id=str(uuid4()),
        user_id=None,
        name="Invalid Scope",
        category_type="EXPENSE",
        is_system=False,
        is_active=True,
    )
    session.add(invalid_scope)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("Invalid system/user scope must fail.")

    invalid_parent = Category(
        id=str(uuid4()),
        user_id=None,
        name="Invalid Parent",
        category_type="EXPENSE",
        parent_id=None,
        is_system=True,
        is_active=False,
    )
    session.add(invalid_parent)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("Inactive system category must fail.")
