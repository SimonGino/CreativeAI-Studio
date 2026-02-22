from __future__ import annotations

from app.config import settings
from app.providers.base import ImageProvider, VideoProvider
from app.providers.gemini_api import GeminiAPIProvider
from app.providers.vertex_ai import VertexAIProvider


def get_provider(auth_type: str = "gemini", api_key: str | None = None) -> GeminiAPIProvider | VertexAIProvider:
    """Factory: create provider based on auth type."""
    if auth_type == "vertex":
        sa_json = settings.vertex_ai_service_account_json
        if not sa_json:
            raise ValueError("Vertex AI requires service account JSON path")
        return VertexAIProvider(sa_json)

    # Default: Gemini API
    key = api_key or settings.gemini_api_key
    if not key:
        raise ValueError("Gemini API key is required")
    return GeminiAPIProvider(key)


__all__ = ["get_provider", "ImageProvider", "VideoProvider", "GeminiAPIProvider", "VertexAIProvider"]
