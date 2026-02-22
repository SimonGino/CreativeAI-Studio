from pydantic import BaseModel

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


class SettingsResponse(BaseModel):
    gemini_api_key_configured: bool
    vertex_ai_configured: bool


class SettingsUpdate(BaseModel):
    gemini_api_key: str | None = None


@router.get("", response_model=SettingsResponse)
async def get_settings():
    return SettingsResponse(
        gemini_api_key_configured=bool(settings.gemini_api_key),
        vertex_ai_configured=bool(settings.vertex_ai_service_account_json),
    )


@router.put("")
async def update_settings(req: SettingsUpdate):
    if req.gemini_api_key is not None:
        settings.gemini_api_key = req.gemini_api_key
    return {"ok": True}
