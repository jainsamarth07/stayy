"""Messaging service — conversations and messages."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.message import Conversation, Message
from app.models.property import Property
from app.models.user import User
from app.schemas.message import ConversationCreate, MessageCreate


async def start_conversation(
    db: AsyncSession, data: ConversationCreate, guest: User
) -> dict:
    """Start a new conversation thread about a property."""
    # Validate property
    prop_result = await db.execute(select(Property).where(Property.id == data.property_id))
    prop = prop_result.scalar_one_or_none()
    if prop is None or not prop.is_active:
        raise NotFoundError("Property not found or inactive")
    if prop.host_id == guest.id:
        raise BadRequestError("Cannot message yourself")

    # Check for existing conversation
    existing = await db.execute(
        select(Conversation).where(
            and_(
                Conversation.property_id == data.property_id,
                Conversation.guest_id == guest.id,
                Conversation.host_id == prop.host_id,
            )
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise BadRequestError(
            "Conversation already exists for this property."
            " Send a message instead."
        )

    conversation = Conversation(
        property_id=data.property_id,
        guest_id=guest.id,
        host_id=prop.host_id,
    )
    db.add(conversation)
    await db.flush()

    # Add initial message
    message = Message(
        conversation_id=conversation.id,
        sender_id=guest.id,
        content=data.message,
    )
    db.add(message)
    await db.flush()

    # Return enriched dict matching ConversationOut schema
    return {
        "id": conversation.id,
        "property_id": conversation.property_id,
        "guest_id": conversation.guest_id,
        "host_id": conversation.host_id,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "last_message": {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "content": message.content,
            "message_type": message.message_type,
            "is_read": message.is_read,
            "created_at": message.created_at,
        },
        "unread_count": 0,
    }


async def send_message(
    db: AsyncSession, conversation_id: uuid.UUID, data: MessageCreate, sender: User
) -> Message:
    """Send a message in an existing conversation."""
    conversation = await _get_conversation_for_user(db, conversation_id, sender.id)

    message = Message(
        conversation_id=conversation.id,
        sender_id=sender.id,
        content=data.content,
    )
    db.add(message)

    # Bump conversation updated_at so the list sorts correctly
    conversation.updated_at = datetime.now(UTC)

    await db.flush()
    return message


async def list_conversations(
    db: AsyncSession, user: User, page: int = 1, page_size: int = 20
) -> tuple[list[dict], int]:
    """List conversations for the current user with last_message and unread_count."""
    user_filter = or_(Conversation.guest_id == user.id, Conversation.host_id == user.id)

    count_result = await db.execute(
        select(func.count()).select_from(Conversation).where(user_filter)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Conversation)
        .where(user_filter)
        .order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    conversations = list(result.scalars().all())

    # Enrich each conversation with last_message, unread_count, property title, other party name
    enriched: list[dict] = []
    for conv in conversations:
        # Fetch last message
        last_msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()

        # Count unread messages (sent by the other party)
        unread_result = await db.execute(
            select(func.count())
            .select_from(Message)
            .where(
                and_(
                    Message.conversation_id == conv.id,
                    Message.sender_id != user.id,
                    Message.is_read == False,  # noqa: E712
                )
            )
        )
        unread_count = unread_result.scalar() or 0

        # Fetch property title
        prop_result = await db.execute(
            select(Property.title).where(Property.id == conv.property_id)
        )
        property_title = prop_result.scalar_one_or_none() or "Unknown Property"

        # Fetch other party's name
        other_id = conv.host_id if conv.guest_id == user.id else conv.guest_id
        other_result = await db.execute(
            select(User.full_name).where(User.id == other_id)
        )
        other_party_name = other_result.scalar_one_or_none() or "Unknown User"

        conv_dict = {
            "id": conv.id,
            "property_id": conv.property_id,
            "guest_id": conv.guest_id,
            "host_id": conv.host_id,
            "property_title": property_title,
            "other_party_name": other_party_name,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "last_message": {
                "id": last_msg.id,
                "conversation_id": last_msg.conversation_id,
                "sender_id": last_msg.sender_id,
                "content": last_msg.content,
                "message_type": last_msg.message_type,
                "is_read": last_msg.is_read,
                "created_at": last_msg.created_at,
            } if last_msg else None,
            "unread_count": unread_count,
        }
        enriched.append(conv_dict)

    return enriched, total


async def get_conversation_detail(
    db: AsyncSession, conversation_id: uuid.UUID, user: User
) -> dict:
    """Get conversation metadata including property title and other party name."""
    conv = await _get_conversation_for_user(db, conversation_id, user.id)

    # Fetch property title
    prop_result = await db.execute(
        select(Property.title).where(Property.id == conv.property_id)
    )
    property_title = prop_result.scalar_one_or_none() or "Unknown Property"

    # Fetch other party's name
    other_id = conv.host_id if conv.guest_id == user.id else conv.guest_id
    other_result = await db.execute(
        select(User.full_name).where(User.id == other_id)
    )
    other_party_name = other_result.scalar_one_or_none() or "Unknown User"

    return {
        "id": conv.id,
        "property_id": conv.property_id,
        "guest_id": conv.guest_id,
        "host_id": conv.host_id,
        "current_user_id": str(user.id),
        "property_title": property_title,
        "other_party_name": other_party_name,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
    }


async def get_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user: User,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Message], int]:
    """Get messages in a conversation (with pagination)."""
    await _get_conversation_for_user(db, conversation_id, user.id)

    count_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .where(Message.conversation_id == conversation_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def mark_conversation_read(
    db: AsyncSession, conversation_id: uuid.UUID, user: User
) -> int:
    """Mark all unread messages in a conversation as read for the current user.

    Only messages sent by the *other* party are touched (you cannot mark your
    own messages as read).  Returns the number of messages updated.
    """
    from sqlalchemy import update  # local import to keep top-level imports minimal

    await _get_conversation_for_user(db, conversation_id, user.id)

    result = await db.execute(
        update(Message)
        .where(
            and_(
                Message.conversation_id == conversation_id,
                Message.sender_id != user.id,
                Message.is_read == False,  # noqa: E712
            )
        )
        .values(is_read=True)
    )
    await db.flush()
    return result.rowcount


async def mark_message_read(db: AsyncSession, message_id: uuid.UUID, user: User) -> Message:
    """Mark a message as read."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    if message is None:
        raise NotFoundError("Message not found")

    # Ensure user is in the conversation
    await _get_conversation_for_user(db, message.conversation_id, user.id)

    # Only the recipient can mark as read (not the sender)
    if message.sender_id == user.id:
        raise BadRequestError("Cannot mark your own message as read")

    message.is_read = True
    await db.flush()
    return message


async def _get_conversation_for_user(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    """Fetch conversation and verify user is a participant."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise NotFoundError("Conversation not found")
    if conversation.guest_id != user_id and conversation.host_id != user_id:
        raise ForbiddenError("You are not part of this conversation")
    return conversation
