"""Messaging Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Request schema for starting a new conversation about a property."""
    property_id: uuid.UUID
    message: str = Field(..., min_length=1, max_length=5000)


class MessageCreate(BaseModel):
    """Request schema for sending a message in a conversation."""
    content: str = Field(..., min_length=1, max_length=5000)


class MessageOut(BaseModel):
    """Response schema for a single message."""
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    message_type: str = "text"
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    """Response schema for a conversation with last message and unread count."""
    id: uuid.UUID
    property_id: uuid.UUID
    guest_id: uuid.UUID
    host_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    last_message: MessageOut | None = None
    unread_count: int = 0

    model_config = {"from_attributes": True}


class PaginatedMessages(BaseModel):
    """Paginated wrapper for message lists."""
    items: list[MessageOut]
    total: int
    page: int
    page_size: int
