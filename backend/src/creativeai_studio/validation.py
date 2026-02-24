from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from creativeai_studio.api.deps import AppContext
from creativeai_studio.model_catalog import get_model

AuthMode = Literal["api_key", "vertex"]


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedJobCreate:
    job_type: str
    model_id: str
    auth_mode: AuthMode
    params: dict[str, Any]


def resolve_auth_mode(payload: dict[str, Any], ctx: AppContext) -> AuthMode:
    override = (payload.get("auth") or {}).get("mode")
    if override in ("api_key", "vertex"):
        return override
    default_mode = (ctx.settings.get_json("default_auth_mode") or {"mode": "api_key"}).get(
        "mode", "api_key"
    )
    return default_mode if default_mode in ("api_key", "vertex") else "api_key"


def validate_job_create(payload: dict[str, Any], ctx: AppContext) -> ValidatedJobCreate:
    job_type = str(payload.get("job_type") or "")
    model_id = str(payload.get("model_id") or "")
    if not job_type:
        raise ValidationError("job_type is required")
    if not model_id:
        raise ValidationError("model_id is required")

    model = get_model(model_id)
    if model is None:
        raise ValidationError("Unknown model_id")

    auth_mode = resolve_auth_mode(payload, ctx)
    if auth_mode not in set(model.get("auth_support") or []):
        raise ValidationError("Auth mode not supported for model")

    params = dict(payload.get("params") or {})
    if payload.get("prompt") is not None:
        params.setdefault("prompt", payload.get("prompt"))

    if job_type == "video.extend":
        if auth_mode != "vertex":
            raise ValidationError("video.extend requires vertex auth")
        if not ctx.settings.get_str("vertex_gcs_bucket"):
            raise ValidationError("VERTEX_GCS_BUCKET not configured")

    if job_type == "image.generate" and params.get("reference_image_asset_id"):
        if not model.get("reference_image_supported"):
            raise ValidationError("reference_image not supported for model")

    params = _normalize_aspect_ratio(params, model, ctx)
    return ValidatedJobCreate(job_type=job_type, model_id=model_id, auth_mode=auth_mode, params=params)


def _parse_ratio(r: str) -> float | None:
    if ":" not in r:
        return None
    a, b = r.split(":", 1)
    try:
        return float(a) / float(b)
    except Exception:
        return None


def _pick_nearest_ratio(target: float, candidates: list[str]) -> str | None:
    scored: list[tuple[float, str]] = []
    for r in candidates:
        v = _parse_ratio(r)
        if v is None:
            continue
        scored.append((abs(v - target), r))
    if not scored:
        return None
    scored.sort(key=lambda t: t[0])
    return scored[0][1]


def _normalize_aspect_ratio(params: dict[str, Any], model: dict[str, Any], ctx: AppContext) -> dict[str, Any]:
    aspect = params.get("aspect_ratio")
    if not aspect:
        return params

    supported = [r for r in (model.get("aspect_ratios") or []) if r != "auto"]
    if aspect != "auto":
        if supported and aspect not in supported:
            raise ValidationError("aspect_ratio not supported")
        return params

    default_aspect = "1:1" if model.get("media_type") == "image" else "16:9"
    input_asset_id = (
        params.get("reference_image_asset_id")
        or params.get("start_image_asset_id")
        or params.get("end_image_asset_id")
    )
    if not input_asset_id or not supported:
        params["aspect_ratio"] = default_aspect
        return params

    asset = ctx.assets.get(str(input_asset_id))
    if not asset or not asset.get("width") or not asset.get("height"):
        params["aspect_ratio"] = default_aspect
        return params

    target = float(asset["width"]) / float(asset["height"])
    chosen = _pick_nearest_ratio(target, supported) or default_aspect
    params["aspect_ratio"] = chosen
    return params
