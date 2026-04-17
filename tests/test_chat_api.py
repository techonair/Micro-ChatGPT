import pytest


@pytest.mark.asyncio
async def test_chat_and_history_flow(client):
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "chat@example.com", "password": "password123"},
    )
    user_id = signup.json()["data"]["user"]["id"]

    chat_res = await client.post(
        "/api/v1/chat",
        json={
            "user_id": user_id,
            "message": "Hello there",
            "provider": "openai",
        },
    )
    assert chat_res.status_code == 200
    chat_body = chat_res.json()["data"]
    assert chat_body["session_id"]
    assert "openai-stub" in chat_body["output_text"]
    session_id = chat_body["session_id"]

    history_res = await client.get(f"/api/v1/history/{user_id}", params={"session_id": session_id})
    assert history_res.status_code == 200
    history_data = history_res.json()["data"]
    assert len(history_data["turns"]) == 1
    assert history_data["turns"][0]["input_text"] == "Hello there"


@pytest.mark.asyncio
async def test_chat_unknown_user(client):
    res = await client.post(
        "/api/v1/chat",
        json={"user_id": "missing", "message": "Hi", "provider": "openai"},
    )
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "user_not_found"
