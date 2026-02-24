from __future__ import annotations

from fastapi import APIRouter

from creativeai_studio.model_catalog import list_models

router = APIRouter(prefix="/models")


@router.get("")
def get_models():
    return list_models()

