"""Property listing endpoints."""

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_host
from app.models.user import User
from app.schemas.property import (
    HourlyBookingConfigUpdate,
    PropertyCreate,
    PropertyOut,
    PropertySearchParams,
    PropertyUpdate,
)
from app.services import property_service, upload_service

router = APIRouter()


@router.get("", response_model=dict)
async def search_properties(
    city: str | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    max_guests: int | None = Query(None, ge=1),
    hourly_available: bool | None = None,
    host_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Search and filter property listings (public)."""
    params = PropertySearchParams(
        city=city,
        min_price=min_price,
        max_price=max_price,
        max_guests=max_guests,
        hourly_available=hourly_available,
        host_id=host_id,
        page=page,
        page_size=page_size,
    )
    properties, total = await property_service.search_properties(db, params)
    return {
        "items": [PropertyOut.model_validate(p) for p in properties],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{property_id}", response_model=PropertyOut)
async def get_property(
    property_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> PropertyOut:
    """Get a single property by ID (public)."""
    prop = await property_service.get_property(db, property_id)
    return PropertyOut.model_validate(prop)


@router.post("", response_model=PropertyOut, status_code=201)
async def create_property(
    data: PropertyCreate,
    host: User = Depends(require_host),
    db: AsyncSession = Depends(get_db),
) -> PropertyOut:
    """Create a new property listing (host only, requires active membership)."""
    prop = await property_service.create_property(db, data, host)
    return PropertyOut.model_validate(prop)


@router.put("/{property_id}", response_model=PropertyOut)
async def update_property(
    property_id: uuid.UUID,
    data: PropertyUpdate,
    host: User = Depends(require_host),
    db: AsyncSession = Depends(get_db),
) -> PropertyOut:
    """Update a property listing (owner only)."""
    prop = await property_service.update_property(db, property_id, data, host)
    return PropertyOut.model_validate(prop)


@router.delete("/{property_id}", status_code=204)
async def delete_property(
    property_id: uuid.UUID,
    host: User = Depends(require_host),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete (deactivate) a property listing (owner only)."""
    await property_service.delete_property(db, property_id, host)


@router.post("/{property_id}/images", status_code=201)
async def upload_property_image(
    property_id: uuid.UUID,
    file: UploadFile = File(...),
    is_primary: bool = Query(False),
    host: User = Depends(require_host),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload an image for a property (owner only)."""
    from fastapi import HTTPException
    from fastapi import status as http_status

    # Validate declared content type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{content_type}' not allowed. Accepted: JPEG, PNG, WebP, GIF.",
        )

    # Read with size cap (UploadFile.read() is the portable async API)
    max_size = 10 * 1024 * 1024  # 10 MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10 MB.",
        )

    # Validate magic bytes — content_type is user-controlled and can be spoofed
    magic_map = {
        b"\xff\xd8\xff": "image/jpeg",
        b"\x89PNG\r\n\x1a\n": "image/png",
        b"RIFF": "image/webp",   # WebP starts with RIFF....WEBP
        b"GIF87a": "image/gif",
        b"GIF89a": "image/gif",
    }
    detected = None
    for magic, mime in magic_map.items():
        if contents[:len(magic)] == magic:
            detected = mime
            break
    if detected is None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image (magic bytes mismatch).",
        )

    image_url = upload_service.upload_image(contents, detected)
    image = await property_service.add_property_image(db, property_id, image_url, is_primary, host)
    return {"id": str(image.id), "image_url": image.image_url, "is_primary": image.is_primary}


@router.put("/{property_id}/hourly", response_model=PropertyOut)
async def configure_hourly_booking(
    property_id: uuid.UUID,
    data: HourlyBookingConfigUpdate,
    host: User = Depends(require_host),
    db: AsyncSession = Depends(get_db),
) -> PropertyOut:
    """Enable/configure hourly booking for a property (owner only)."""
    prop = await property_service.configure_hourly_booking(db, property_id, data, host)
    return PropertyOut.model_validate(prop)
