import asyncio

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings


async def upload_pet_image(file: UploadFile) -> str:
    settings = get_settings()
    if not all(
        [
            settings.cloudinary_cloud_name,
            settings.cloudinary_api_key,
            settings.cloudinary_api_secret,
        ]
    ):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Image storage is not configured")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only image uploads are allowed")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image is larger than 10 MB")
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        content,
        folder="littlellama/pets",
        resource_type="image",
    )
    return str(result["secure_url"])
