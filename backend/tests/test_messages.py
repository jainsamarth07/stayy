"""Messaging endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_conversation_requires_auth(client: AsyncClient) -> None:
    """Test starting a conversation requires authentication."""
    response = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": str(uuid.uuid4()),
            "message": "Hello, is this property available?",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_conversations_empty(client: AsyncClient, user_token: str) -> None:
    """Test listing conversations when none exist."""
    response = await client.get(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_start_conversation_invalid_property(
    client: AsyncClient, user_token: str
) -> None:
    """Test starting conversation with nonexistent property returns 404."""
    response = await client.post(
        "/api/v1/conversations",
        json={
            "property_id": str(uuid.uuid4()),
            "message": "Hello, is this available?",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_messages_invalid_conversation(
    client: AsyncClient, user_token: str
) -> None:
    """Test getting messages from a nonexistent conversation returns 404."""
    response = await client.get(
        f"/api/v1/conversations/{uuid.uuid4()}/messages",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404
