from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message


async def list_conversations(db: AsyncSession) -> list[Conversation]:
    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation(db: AsyncSession, conv_id: str) -> Conversation | None:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conv_id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one_or_none()


async def create_conversation(db: AsyncSession, title: str = "New Conversation") -> Conversation:
    conv = Conversation(title=title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def delete_conversation(db: AsyncSession, conv_id: str) -> bool:
    conv = await db.get(Conversation, conv_id)
    if not conv:
        return False
    await db.delete(conv)
    await db.commit()
    return True


async def add_message(
    db: AsyncSession,
    conv_id: str,
    role: str,
    content: str,
    media_type: str | None = None,
    media_url: str | None = None,
    model: str | None = None,
    config: dict | None = None,
) -> Message:
    msg = Message(
        conversation_id=conv_id,
        role=role,
        content=content,
        media_type=media_type,
        media_url=media_url,
        model=model,
        config=config,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
