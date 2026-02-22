import logging

from fastapi import APIRouter, HTTPException

from app.schemas.generation import ImageGenerateRequest, ImageGenerateResponse
from app.services.image_service import generate_images

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(req: ImageGenerateRequest):
    try:
        urls = await generate_images(
            prompt=req.prompt,
            model=req.model,
            aspect_ratio=req.aspect_ratio,
            number_of_images=req.number_of_images,
            api_key=req.api_key,
            auth_type=req.auth_type,
        )
        return ImageGenerateResponse(images=urls, model=req.model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Image generation failed")
        raise HTTPException(status_code=500, detail=str(e))
