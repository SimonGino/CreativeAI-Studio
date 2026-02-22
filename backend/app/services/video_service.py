import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generation import GenerationTask
from app.providers import get_provider
from app.utils.file_storage import save_media

logger = logging.getLogger(__name__)


async def start_video_task(
    db: AsyncSession,
    prompt: str,
    model: str,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
    resolution: str = "720p",
    generate_audio: bool = True,
    image_data: bytes | None = None,
    api_key: str | None = None,
    auth_type: str = "gemini",
    message_id: str | None = None,
) -> GenerationTask:
    """Start a video generation task and return the task record."""
    provider = get_provider(auth_type, api_key)

    operation_id = await provider.start_video_generation(
        prompt=prompt,
        model=model,
        aspect_ratio=aspect_ratio,
        duration_seconds=duration_seconds,
        resolution=resolution,
        generate_audio=generate_audio,
        image_data=image_data,
    )

    task = GenerationTask(
        message_id=message_id,
        operation_id=operation_id,
        status="processing",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def poll_and_update(
    db: AsyncSession,
    task_id: str,
    api_key: str | None = None,
    auth_type: str = "gemini",
):
    """Poll video generation status and yield updates."""
    task = await db.get(GenerationTask, task_id)
    if not task:
        yield {"status": "failed", "error": "Task not found"}
        return

    provider = get_provider(auth_type, api_key)

    while task.status == "processing":
        try:
            status = await provider.poll_video_status(task.operation_id)

            if status.done:
                if status.error:
                    task.status = "failed"
                    task.error = status.error
                else:
                    video_url = await save_media(status.video_bytes, "mp4")
                    task.status = "completed"
                    task.result_url = video_url
                    task.progress = 1.0

                task.updated_at = datetime.now(timezone.utc)
                await db.commit()

                yield {
                    "status": task.status,
                    "progress": task.progress,
                    "video_url": task.result_url,
                    "error": task.error,
                }
                return

            task.progress = status.progress
            task.updated_at = datetime.now(timezone.utc)
            await db.commit()

            yield {
                "status": "processing",
                "progress": status.progress,
            }

        except Exception as e:
            logger.exception("Error polling video status")
            task.status = "failed"
            task.error = str(e)
            task.updated_at = datetime.now(timezone.utc)
            await db.commit()
            yield {"status": "failed", "error": str(e)}
            return

        await asyncio.sleep(10)
