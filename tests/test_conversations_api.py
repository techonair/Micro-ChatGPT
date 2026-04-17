import pytest


@pytest.mark.asyncio
async def test_conversation_crud_flow(client):
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "conv@example.com", "password": "password123"},
    )
    user_id = signup.json()["data"]["user"]["id"]

    create_res = await client.post(
        "/api/v1/conversations",
        json={
            "user_id": user_id,
            "message": "Start a new conversation",
            "provider": "openai",
        },
    )
    assert create_res.status_code == 200
    create_data = create_res.json()["data"]
    conversation_id = create_data["conversation_id"]
    assert conversation_id
    assert create_data["first_message"]["session_id"] == conversation_id

    list_res = await client.get("/api/v1/conversations", params={"user_id": user_id})
    assert list_res.status_code == 200
    sessions = list_res.json()["data"]["conversations"]
    assert any(s["conversation_id"] == conversation_id for s in sessions)

    detail_res = await client.get(f"/api/v1/conversations/{conversation_id}", params={"user_id": user_id})
    assert detail_res.status_code == 200
    assert len(detail_res.json()["data"]["turns"]) == 1

    add_msg = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "user_id": user_id,
            "message": "Second message",
            "provider": "openai",
        },
    )
    assert add_msg.status_code == 200
    assert add_msg.json()["data"]["session_id"] == conversation_id

    detail_res_2 = await client.get(f"/api/v1/conversations/{conversation_id}", params={"user_id": user_id})
    assert detail_res_2.status_code == 200
    assert len(detail_res_2.json()["data"]["turns"]) == 2

    delete_res = await client.delete(f"/api/v1/conversations/{conversation_id}", params={"user_id": user_id})
    assert delete_res.status_code == 200
    assert delete_res.json()["data"]["deleted"] is True

    detail_after_delete = await client.get(f"/api/v1/conversations/{conversation_id}", params={"user_id": user_id})
    assert detail_after_delete.status_code == 404
    assert detail_after_delete.json()["error"]["code"] == "conversation_not_found"


@pytest.mark.asyncio
async def test_add_message_to_missing_conversation_returns_404(client):
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "conv404@example.com", "password": "password123"},
    )
    user_id = signup.json()["data"]["user"]["id"]

    res = await client.post(
        "/api/v1/conversations/missing-conversation/messages",
        json={
            "user_id": user_id,
            "message": "hello",
            "provider": "openai",
        },
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "conversation_not_found"
