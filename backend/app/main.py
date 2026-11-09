"""Coco English API — application entrypoint."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.schemas.session_schemas import err

app = FastAPI(title="Coco English API")
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Keep validation failures inside the uniform response envelope."""
    return JSONResponse(
        status_code=422,
        content=err("validation_error", "Invalid request payload."),
    )
