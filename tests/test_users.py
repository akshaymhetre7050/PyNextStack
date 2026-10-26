"""
Regression tests for TEST-2: Duplicate email/username check uses AND instead of OR,
allowing duplicate accounts.

Verifies the fix applied to app.routers.users.user_exists and the /check_user_exists endpoint.

Covers:
- Regression: an existing email OR an existing username is detected on its own
- Happy path: exact match and brand-new users
- Edge cases: single-field lookups, no arguments, empty strings
"""
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.routers import users

EXISTING_USER = {"username": "alice", "email": "alice@example.com"}


@pytest_asyncio.fixture
async def user_collection(monkeypatch):
    """In-memory users collection seeded with one user, swapped in for the real MongoDB collection."""
    collection = AsyncMongoMockClient()["test_db"]["users"]
    await collection.insert_one(dict(EXISTING_USER))
    monkeypatch.setattr(users, "user_collection", collection)
    return collection


@pytest_asyncio.fixture
async def client(user_collection):
    app = FastAPI()
    app.include_router(users.router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# --- Regression -----------------------------------------------------------

@pytest.mark.asyncio
async def test_user_exists_existing_email_new_username_returns_true(user_collection):
    assert await users.user_exists(email="alice@example.com", username="bob") is True


@pytest.mark.asyncio
async def test_user_exists_new_email_existing_username_returns_true(user_collection):
    assert await users.user_exists(email="bob@example.com", username="alice") is True


@pytest.mark.asyncio
async def test_check_user_exists_endpoint_existing_email_new_username_returns_true(client):
    response = await client.get("/check_user_exists", params={"email": "alice@example.com", "username": "bob"})
    assert response.status_code == 200
    assert response.json() is True


# --- Happy path -----------------------------------------------------------

@pytest.mark.asyncio
async def test_user_exists_both_fields_match_returns_true(user_collection):
    assert await users.user_exists(email="alice@example.com", username="alice") is True


@pytest.mark.asyncio
async def test_user_exists_new_email_and_username_returns_false(user_collection):
    assert await users.user_exists(email="bob@example.com", username="bob") is False


@pytest.mark.asyncio
async def test_check_user_exists_endpoint_new_user_returns_false(client):
    response = await client.get("/check_user_exists", params={"email": "bob@example.com", "username": "bob"})
    assert response.status_code == 200
    assert response.json() is False


# --- Edge cases -----------------------------------------------------------

@pytest.mark.asyncio
async def test_user_exists_email_only_existing_returns_true(user_collection):
    assert await users.user_exists(email="alice@example.com") is True


@pytest.mark.asyncio
async def test_user_exists_username_only_existing_returns_true(user_collection):
    assert await users.user_exists(username="alice") is True


@pytest.mark.asyncio
async def test_user_exists_no_arguments_returns_false(user_collection):
    assert await users.user_exists() is False


@pytest.mark.asyncio
async def test_user_exists_empty_strings_returns_false(user_collection):
    assert await users.user_exists(email="", username="") is False


@pytest.mark.asyncio
async def test_check_user_exists_endpoint_no_params_returns_400(client):
    response = await client.get("/check_user_exists")
    assert response.status_code == 400
