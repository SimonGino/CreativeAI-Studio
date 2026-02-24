from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from creativeai_studio.api.deps import AppContext, get_ctx
from creativeai_studio.validation import ValidationError, validate_job_create

router = APIRouter(prefix="/jobs")


def _create_job(payload: dict, ctx: AppContext, runner) -> dict:
    try:
        v = validate_job_create(payload, ctx)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    job_id = uuid.uuid4().hex
    job = ctx.jobs.create(
        job_id=job_id,
        job_type=v.job_type,
        model_id=v.model_id,
        auth_mode=v.auth_mode,
        params=v.params,
    )

    params = v.params
    if v.job_type == "image.generate":
        ref_ids = params.get("reference_image_asset_ids")
        if isinstance(ref_ids, list):
            for ref_id in ref_ids:
                if ref_id:
                    ctx.job_assets.add(job_id=job_id, asset_id=str(ref_id), role="input_reference")
        elif params.get("reference_image_asset_id"):
            ctx.job_assets.add(job_id=job_id, asset_id=str(params["reference_image_asset_id"]), role="input_reference")
    if v.job_type == "video.generate":
        if params.get("start_image_asset_id"):
            ctx.job_assets.add(job_id=job_id, asset_id=str(params["start_image_asset_id"]), role="input_start")
        if params.get("end_image_asset_id"):
            ctx.job_assets.add(job_id=job_id, asset_id=str(params["end_image_asset_id"]), role="input_end")

    if runner is not None:
        runner.enqueue(job_id)

    return job


@router.post("")
def create_job(payload: dict, request: Request, ctx: AppContext = Depends(get_ctx)):
    return _create_job(payload=payload, ctx=ctx, runner=request.app.state.runner)


@router.get("")
def list_jobs(
    ctx: AppContext = Depends(get_ctx),
    status: str | None = None,
    job_type: str | None = None,
    model_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    return ctx.jobs.list(status=status, job_type=job_type, model_id=model_id, limit=limit, offset=offset)


@router.get("/{job_id}")
def get_job(job_id: str, ctx: AppContext = Depends(get_ctx)):
    job = ctx.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    assets = ctx.job_assets.list_by_job(job_id)
    return {**job, "job_assets": assets}


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str, ctx: AppContext = Depends(get_ctx)):
    job = ctx.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "queued":
        ctx.jobs.set_status(job_id, "canceled")
    else:
        ctx.jobs.request_cancel(job_id)
    return {"ok": True}


@router.post("/{job_id}/clone")
def clone_job(job_id: str, request: Request, payload: dict | None = None, ctx: AppContext = Depends(get_ctx)):
    src = ctx.jobs.get(job_id)
    if not src:
        raise HTTPException(status_code=404, detail="Job not found")

    payload = payload or {}
    new_payload = {
        "job_type": src["job_type"],
        "model_id": src["model_id"],
        "params": dict(src.get("params") or {}),
        "auth": {"mode": src["auth_mode"]},
    }
    if payload.get("prompt") is not None:
        new_payload["params"]["prompt"] = payload.get("prompt")
    if isinstance(payload.get("params"), dict):
        new_payload["params"].update(payload["params"])
    if isinstance(payload.get("auth"), dict) and payload["auth"].get("mode"):
        new_payload["auth"]["mode"] = payload["auth"]["mode"]

    return _create_job(payload=new_payload, ctx=ctx, runner=request.app.state.runner)
