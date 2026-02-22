import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.schemas.generation import VideoGenerateRequest, VideoGenerateResponse, VideoStatusResponse
from app.services.video_service import poll_and_update, start_video_task

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(req: VideoGenerateRequest, db: AsyncSession = Depends(get_db)):
    try:
        task = await start_video_task(
            db=db,
            prompt=req.prompt,
            model=req.model,
            aspect_ratio=req.aspect_ratio,
            duration_seconds=req.duration_seconds,
            resolution=req.resolution,
            generate_audio=req.generate_audio,
            api_key=req.api_key,
            auth_type=req.auth_type,
        )
        return VideoGenerateResponse(task_id=task.id, status=task.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Video generation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/status")
async def video_status_stream(
    task_id: str,
    auth_type: str = "gemini",
    api_key: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    async def event_generator():
        async for update in poll_and_update(db, task_id, api_key, auth_type):
            yield {"event": "status", "data": json.dumps(update)}

    return EventSourceResponse(event_generator())
