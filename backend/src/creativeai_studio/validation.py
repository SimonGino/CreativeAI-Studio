from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from creativeai_studio.api.deps import AppContext
from creativeai_studio.model_catalog import get_model

AuthMode = Literal["api_key"]


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
    if override == "vertex":
        raise ValidationError("Vertex AI auth mode has been removed. Use api_key.")
    if override == "api_key":
        return override
    return "api_key"


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
    if model.get("coming_soon"):
        raise ValidationError("Model is coming soon and cannot be selected yet")

    auth_mode = resolve_auth_mode(payload, ctx)
    if auth_mode not in set(model.get("auth_support") or []):
        raise ValidationError("Auth mode not supported for model")

    params = dict(payload.get("params") or {})
    if payload.get("prompt") is not None:
        params.setdefault("prompt", payload.get("prompt"))

    if job_type == "video.extend":
        raise ValidationError("video.extend is disabled because Vertex AI auth mode has been removed")

    if job_type == "image.generate":
        params = _normalize_reference_images(params, model)
        _validate_image_size(params, model)
        _validate_sequential_image_generation(params, model)
    elif job_type == "video.generate":
        _validate_video_duration(params, model)

    params = _normalize_aspect_ratio(params, model, ctx)
    return ValidatedJobCreate(job_type=job_type, model_id=model_id, auth_mode=auth_mode, params=params)


def _normalize_reference_images(params: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    raw_multi = params.get("reference_image_asset_ids")
    ids: list[str] = []
    if raw_multi is not None:
        if not isinstance(raw_multi, list):
            raise ValidationError("reference_image_asset_ids must be a list")
        for item in raw_multi:
            value = str(item or "").strip()
            if value:
                ids.append(value)

    single = str(params.get("reference_image_asset_id") or "").strip()
    if single and single not in ids:
        ids.insert(0, single)

    if not ids:
        params.pop("reference_image_asset_ids", None)
        return params

    if not model.get("reference_image_supported"):
        raise ValidationError("reference_image not supported for model")

    max_reference_images = model.get("max_reference_images")
    if max_reference_images is not None and len(ids) > int(max_reference_images):
        raise ValidationError(f"reference_image count exceeds max {int(max_reference_images)}")

    params["reference_image_asset_ids"] = ids
    params["reference_image_asset_id"] = ids[0]
    return params


def _validate_sequential_image_generation(params: dict[str, Any], model: dict[str, Any]) -> None:
    output_count_for_limit = 1
    seq = params.get("sequential_image_generation")
    if seq is None:
        _validate_image_total_limit(params, model, output_count_for_limit=output_count_for_limit)
        return
    if seq not in ("disabled", "auto"):
        raise ValidationError("sequential_image_generation must be disabled or auto")

    if seq == "disabled":
        _validate_image_total_limit(params, model, output_count_for_limit=output_count_for_limit)
        return

    if not model.get("sequential_image_generation_supported"):
        raise ValidationError("sequential_image_generation not supported for model")

    opts = params.get("sequential_image_generation_options")
    if opts is None:
        _validate_image_total_limit(params, model, output_count_for_limit=output_count_for_limit)
        return
    if not isinstance(opts, dict):
        raise ValidationError("sequential_image_generation_options must be an object")

    max_images = opts.get("max_images")
    if max_images is None:
        _validate_image_total_limit(params, model, output_count_for_limit=output_count_for_limit)
        return

    try:
        max_images_int = int(max_images)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError("max_images must be an integer") from exc

    if max_images_int < 1:
        raise ValidationError("max_images must be >= 1")

    model_max_images = model.get("max_output_images")
    if model_max_images is not None and max_images_int > int(model_max_images):
        raise ValidationError(f"max_images exceeds model max {int(model_max_images)}")

    output_count_for_limit = max_images_int
    _validate_image_total_limit(params, model, output_count_for_limit=output_count_for_limit)
    params["sequential_image_generation_options"] = {"max_images": max_images_int}


def _validate_image_total_limit(
    params: dict[str, Any],
    model: dict[str, Any],
    *,
    output_count_for_limit: int,
) -> None:
    total_limit = model.get("max_total_images")
    if total_limit is None:
        return
    ref_count = len(params.get("reference_image_asset_ids") or [])
    if ref_count + int(output_count_for_limit) > int(total_limit):
        raise ValidationError(f"reference_image count + max_images exceeds {int(total_limit)}")


def _validate_image_size(params: dict[str, Any], model: dict[str, Any]) -> None:
    image_size = params.get("image_size")
    if image_size is None:
        return

    supported = model.get("resolution_presets")
    if not supported:
        return

    value = str(image_size).strip().lower()
    if not value:
        return

    supported_norm = {str(v).strip().lower() for v in supported if str(v).strip()}
    if supported_norm and value not in supported_norm:
        allowed = ", ".join(str(v) for v in supported)
        raise ValidationError(f"image_size not supported; allowed: {allowed}")


def _validate_video_duration(params: dict[str, Any], model: dict[str, Any]) -> None:
    supported = model.get("duration_seconds")
    if not supported:
        return

    supported_ints = [int(v) for v in supported]
    if params.get("duration_seconds") is None:
        params["duration_seconds"] = supported_ints[0]
        return

    try:
        value = int(params.get("duration_seconds"))
    except Exception as exc:  # noqa: BLE001
        raise ValidationError("duration_seconds must be an integer") from exc

    if value not in supported_ints:
        allowed = ", ".join(str(v) for v in supported_ints)
        raise ValidationError(f"duration_seconds not supported; allowed: {allowed}")
    params["duration_seconds"] = value


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
