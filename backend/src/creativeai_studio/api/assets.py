from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from creativeai_studio.api.deps import AppContext, get_ctx
from creativeai_studio.media_meta import read_image_size, read_video_meta_ffprobe
from creativeai_studio.model_catalog import get_model

router = APIRouter(prefix="/assets")


def _asset_response_with_source_model(ctx: AppContext, asset: dict) -> dict:
    out = dict(asset)
    out["source_model_id"] = None
    out["source_model_name"] = None

    source_job_id = out.get("source_job_id")
    if not source_job_id:
        return out

    job = ctx.jobs.get(str(source_job_id))
    if not job:
        return out

    model_id = job.get("model_id")
    if not model_id:
        return out

    out["source_model_id"] = str(model_id)
    model = get_model(str(model_id))
    if model and model.get("display_name"):
        out["source_model_name"] = str(model["display_name"])
    return out


@router.post("/upload")
async def upload_asset(file: UploadFile = File(...), ctx: AppContext = Depends(get_ctx)):
    mime = file.content_type or "application/octet-stream"
    if not (mime.startswith("image/") or mime.startswith("video/")):
        raise HTTPException(status_code=400, detail="Only image/video supported")

    asset_id = uuid.uuid4().hex
    data = await file.read()
    stored = ctx.asset_store.save_upload(
        asset_id=asset_id,
        filename=file.filename or "upload.bin",
        content=data,
    )

    width = height = None
    duration = None
    if stored.mime_type.startswith("image/"):
        width, height = read_image_size(stored.abs_path)
    elif stored.mime_type.startswith("video/"):
        try:
            width, height, duration = read_video_meta_ffprobe(stored.abs_path)
        except Exception:  # noqa: BLE001
            width = height = None
            duration = None

    asset = ctx.assets.insert_upload(
        asset_id=asset_id,
        media_type="image" if stored.mime_type.startswith("image/") else "video",
        file_path=stored.rel_path,
        mime_type=stored.mime_type,
        size_bytes=stored.size_bytes,
        width=width,
        height=height,
        duration_seconds=duration,
    )

    return {
        "id": asset["id"],
        "media_type": asset["media_type"],
        "origin": asset["origin"],
        "mime_type": asset["mime_type"],
        "width": asset["width"],
        "height": asset["height"],
        "duration_seconds": asset["duration_seconds"],
    }


@router.get("")
def list_assets(
    ctx: AppContext = Depends(get_ctx),
    media_type: str | None = None,
    origin: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    assets = ctx.assets.list(media_type=media_type, origin=origin, limit=limit, offset=offset)
    return [_asset_response_with_source_model(ctx, a) for a in assets]


@router.get("/{asset_id}")
def get_asset(asset_id: str, ctx: AppContext = Depends(get_ctx)):
    a = ctx.assets.get(asset_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    return _asset_response_with_source_model(ctx, a)


@router.get("/{asset_id}/content")
def asset_content(asset_id: str, ctx: AppContext = Depends(get_ctx)):
    a = ctx.assets.get(asset_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    abs_path = ctx.asset_store.resolve(a["file_path"])
    return FileResponse(abs_path, media_type=a["mime_type"])
