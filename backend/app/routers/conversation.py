from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.conversation_service import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
)

router = APIRouter()


@router.get("", response_model=list[ConversationResponse])
async def list_all(db: AsyncSession = Depends(get_db)):
    return await list_conversations(db)


@router.post("", response_model=ConversationResponse)
async def create(req: ConversationCreate, db: AsyncSession = Depends(get_db)):
    return await create_conversation(db, req.title)


@router.get("/{conv_id}", response_model=ConversationDetailResponse)
async def get_detail(conv_id: str, db: AsyncSession = Depends(get_db)):
    conv = await get_conversation(db, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/{conv_id}")
async def delete(conv_id: str, db: AsyncSession = Depends(get_db)):
    ok = await delete_conversation(db, conv_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


@router.post("/{conv_id}/messages", response_model=MessageResponse)
async def create_message(conv_id: str, req: MessageCreate, db: AsyncSession = Depends(get_db)):
    conv = await get_conversation(db, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await add_message(
        db, conv_id, req.role, req.content, req.media_type, req.media_url, req.model, req.config
    )
