import pytest


@pytest.mark.asyncio
async def test_signup_and_login(client):
    signup_res = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "alice@example.com",
            "password": "password123",
            "full_name": "Alice",
        },
    )
    assert signup_res.status_code == 200
    signup_body = signup_res.json()
    assert signup_body["success"] is True
    assert signup_body["data"]["user"]["email"] == "alice@example.com"
    assert signup_body["data"]["access_token"]

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert login_res.status_code == 200
    login_body = login_res.json()
    assert login_body["success"] is True
    assert login_body["data"]["access_token"]


@pytest.mark.asyncio
async def test_signup_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "password123"}
    first = await client.post("/api/v1/auth/signup", json=payload)
    second = await client.post("/api/v1/auth/signup", json=payload)

    assert first.status_code == 200
    assert second.status_code == 409
    body = second.json()
    assert body["success"] is False
    assert body["error"]["code"] == "email_exists"
