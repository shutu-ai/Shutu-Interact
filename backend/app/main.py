"""Coco English API — application entrypoint."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.schemas.session_schemas import err

logger = logging.getLogger(__name__)

app = FastAPI(title="Coco English API")
app.include_router(api_router)

# The kiosk frontend is served from its own origin (plan §8 Phase 4).
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Keep validation failures inside the uniform response envelope."""
    return JSONResponse(
        status_code=422,
        content=err("validation_error", "Invalid request payload."),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all: every failure answers in the uniform envelope.

    Anonymous logging only — the exception message may contain child
    context, so the type name is logged, never the message (spec §7.3).
    """
    logger.error(
        "unhandled_error path=%s error_type=%s",
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content=err("internal_error", "Internal server error."),
    )

