"""Health check route."""

from typing import Any

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.session_schemas import ok

router = APIRouter()


@router.get("/api/health")
def health() -> dict[str, Any]:
    return ok({"status": "ok", "app": settings.app_name})
