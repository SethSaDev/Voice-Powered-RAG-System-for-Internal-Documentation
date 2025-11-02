"""
API V1 Router - Register all endpoints
"""

from fastapi import APIRouter
from api.v1.endpoints import voice, documents, conversations, analytics, auth

api_router = APIRouter()

# Health check (no prefix)
api_router.add_api_route("/health", lambda: {"status": "ok"}, methods=["GET"])

# Auth endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
)

# Voice endpoints
api_router.include_router(
    voice.router,
    prefix="/voice",
    tags=["voice"],
)

# Document management
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"],
)

# Conversation history
api_router.include_router(
    conversations.router,
    prefix="/conversations",
    tags=["conversations"],
)

# Analytics & metrics
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"],
)