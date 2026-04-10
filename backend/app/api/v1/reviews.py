"""Review endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.review import PaginatedReviews, ReviewCreate, ReviewOut
from app.services import review_service

router = APIRouter()


@router.post("", response_model=ReviewOut, status_code=201)
async def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewOut:
    """Create a review for a completed booking."""
    review = await review_service.create_review(db, data, current_user)
    return ReviewOut.model_validate(review)


@router.get("/property/{property_id}", response_model=PaginatedReviews)
async def list_property_reviews(
    property_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedReviews:
    """List reviews for a property (public)."""
    items, total = await review_service.list_property_reviews(db, property_id, page, page_size)
    return PaginatedReviews(
        items=[ReviewOut.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/host", response_model=PaginatedReviews)
async def list_host_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedReviews:
    """List all reviews for properties owned by the current host."""
    items, total = await review_service.list_host_reviews(
        db, current_user.id, page, page_size
    )
    return PaginatedReviews(
        items=[ReviewOut.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )
