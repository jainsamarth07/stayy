"""Aggregated API v1 router."""

from fastapi import APIRouter

from app.api.v1 import admin, auth, bookings, memberships, messages, properties, reviews

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(properties.router, prefix="/properties", tags=["Properties"])
api_v1_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_v1_router.include_router(messages.router, prefix="", tags=["Messaging"])
api_v1_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_v1_router.include_router(memberships.router, prefix="/memberships", tags=["Memberships"])
api_v1_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
