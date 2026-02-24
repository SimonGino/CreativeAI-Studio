from __future__ import annotations

from fastapi import APIRouter, Depends

from creativeai_studio.api.deps import AppContext, get_ctx

router = APIRouter(prefix="/settings")


@router.get("")
def get_settings(ctx: AppContext = Depends(get_ctx)):
    default_auth = "api_key"

    has_api_key = ctx.settings.get_str("google_api_key") is not None
    has_ark_api_key = ctx.settings.get_str("ark_api_key") is not None

    return {
        "default_auth_mode": default_auth,
        "google_api_key_present": has_api_key,
        "ark_api_key_present": has_ark_api_key,
    }


@router.put("")
def put_settings(payload: dict, ctx: AppContext = Depends(get_ctx)):
    mode = payload.get("default_auth_mode")
    if mode == "api_key":
        ctx.settings.set_json("default_auth_mode", {"mode": mode})

    if "google_api_key" in payload and payload["google_api_key"]:
        ctx.settings.set_str("google_api_key", str(payload["google_api_key"]))
    if "ark_api_key" in payload and payload["ark_api_key"]:
        ctx.settings.set_str("ark_api_key", str(payload["ark_api_key"]))

    return get_settings(ctx)


@router.post("/test")
def test_settings(ctx: AppContext = Depends(get_ctx)):
    results: dict[str, dict] = {}

    api_key = ctx.settings.get_str("google_api_key")
    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            client.models.list(config={"page_size": 1})
            results["google_api_key"] = {"ok": True}
        except Exception as e:  # noqa: BLE001
            results["google_api_key"] = {"ok": False, "error": str(e)}
    else:
        results["google_api_key"] = {"ok": False, "error": "google_api_key not set"}

    ark_api_key = ctx.settings.get_str("ark_api_key")
    if ark_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(base_url="https://ark.cn-beijing.volces.com/api/v3", api_key=ark_api_key)
            models = client.models.list()
            if getattr(models, "data", None) is not None:
                _ = models.data[:1]
            else:
                next(iter(models), None)
            results["ark_api_key"] = {"ok": True}
        except Exception as e:  # noqa: BLE001
            results["ark_api_key"] = {"ok": False, "error": str(e)}
    else:
        results["ark_api_key"] = {"ok": False, "error": "ark_api_key not set"}

    return results
