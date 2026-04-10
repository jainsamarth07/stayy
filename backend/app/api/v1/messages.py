"""Messaging endpoints — conversations and messages."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.message import (
    ConversationCreate,
    MessageCreate,
    MessageOut,
    PaginatedMessages,
)
from app.services import message_service

router = APIRouter()


@router.post("/conversations", response_model=dict, status_code=201)
async def start_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start a new conversation thread about a property."""
    conv = await message_service.start_conversation(db, data, current_user)
    return conv


@router.get("/conversations", response_model=dict)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all conversations for the current user."""
    items, total = await message_service.list_conversations(db, current_user, page, page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/conversations/{conversation_id}", response_model=dict)
async def get_conversation_detail(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get conversation metadata (property title, other party name)."""
    return await message_service.get_conversation_detail(db, conversation_id, current_user)


@router.get("/conversations/{conversation_id}/messages", response_model=PaginatedMessages)
async def get_messages(
    conversation_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedMessages:
    """Get messages in a conversation thread."""
    items, total = await message_service.get_messages(
        db, conversation_id, current_user, page, page_size
    )
    return PaginatedMessages(
        items=[MessageOut.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=201,
)
async def send_message(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    """Send a message in an existing conversation."""
    msg = await message_service.send_message(db, conversation_id, data, current_user)
    return MessageOut.model_validate(msg)


@router.put("/messages/{message_id}/read", response_model=MessageOut)
async def mark_message_read(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    """Mark a message as read."""
    msg = await message_service.mark_message_read(db, message_id, current_user)
    return MessageOut.model_validate(msg)
