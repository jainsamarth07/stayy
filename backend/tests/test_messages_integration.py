"""Integration tests for messaging endpoints — conversations and messages."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_conversation_success(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Guest can start a conversation about a property."""
    response = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Hi, is this property available next month?",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["property_id"] == created_property["id"]
    assert data["guest_id"] is not None
    assert data["host_id"] is not None
    assert data["last_message"]["content"] == "Hi, is this property available next month?"
    assert "id" in data


@pytest.mark.asyncio
async def test_start_conversation_host_cannot_message_self(
    client: AsyncClient, host_with_membership: str, created_property: dict
) -> None:
    """Host cannot start a conversation on their own property."""
    response = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Talking to myself?",
        },
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_start_duplicate_conversation(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Cannot start a duplicate conversation for the same property."""
    await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "First message",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Duplicate message",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_send_message_in_conversation(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Both guest and host can send messages in a conversation."""
    # Start conversation
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Hello!",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    # Host replies
    reply_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Hi! Yes, the property is available."},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert reply_resp.status_code == 201
    assert reply_resp.json()["content"] == "Hi! Yes, the property is available."

    # Guest replies again
    reply_resp2 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Great, I'll book it!"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert reply_resp2.status_code == 201


@pytest.mark.asyncio
async def test_get_messages_in_conversation(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Get all messages in a conversation."""
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Initial message",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    # Send a few more
    await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Reply 1"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Reply 2"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_conversations_with_data(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """List conversations returns enriched data with last_message and unread_count."""
    await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Is this available?",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.get(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    conv = data["items"][0]
    assert "last_message" in conv
    assert "unread_count" in conv
    assert "property_title" in conv or "property_id" in conv


@pytest.mark.asyncio
async def test_list_conversations_as_host(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Host sees conversations about their properties."""
    await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Question about parking",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.get(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_conversation_detail(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Get conversation detail includes property title and other party name."""
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Detail test",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    response = await client.get(
        f"/api/v1/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv_id
    assert "property_title" in data
    assert "other_party_name" in data


@pytest.mark.asyncio
async def test_get_conversation_detail_as_host(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Host can also get conversation detail."""
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Host detail test",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    response = await client.get(
        f"/api/v1/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == conv_id


@pytest.mark.asyncio
async def test_mark_message_read(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Host can mark a guest's message as read."""
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Please read this",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    # Get messages to find the message id
    msgs_resp = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    msg_id = msgs_resp.json()["items"][0]["id"]

    # Mark as read
    response = await client.put(
        f"/api/v1/messages/{msg_id}/read",
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    assert response.json()["is_read"] is True


@pytest.mark.asyncio
async def test_mark_own_message_read_fails(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Sender cannot mark their own message as read."""
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "My own message",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    msgs_resp = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    msg_id = msgs_resp.json()["items"][0]["id"]

    response = await client.put(
        f"/api/v1/messages/{msg_id}/read",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_mark_nonexistent_message_read(
    client: AsyncClient, user_token: str
) -> None:
    """Marking a nonexistent message returns 404."""
    response = await client.put(
        f"/api/v1/messages/{uuid.uuid4()}/read",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_message_nonparticipant(
    client: AsyncClient, user_token: str, guest_token: str, created_property: dict
) -> None:
    """Non-participant cannot send a message in a conversation."""
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Original message",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    response = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "I shouldn't be here"},
        headers={"Authorization": f"Bearer {guest_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_conversation_nonparticipant(
    client: AsyncClient, user_token: str, guest_token: str, created_property: dict
) -> None:
    """Non-participant cannot view a conversation."""
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": created_property["id"],
            "message": "Private conversation",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    conv_id = conv_resp.json()["id"]

    response = await client.get(
        f"/api/v1/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {guest_token}"},
    )
    assert response.status_code == 403
