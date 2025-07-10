"""FastAPI exception handlers."""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.security import OAuth2Error


async def oauth2_exception_handler(request: Request, exc: OAuth2Error):
    """Handle OAuth2Error exceptions with proper OAuth2 error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error,
            "error_description": exc.error_description
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with OAuth2 error format for token endpoints."""
    # Check if this is a token endpoint request
    if request.url.path.endswith("/token"):
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_request",
                "error_description": f"Missing required parameter: {exc.errors()[0]['loc'][-1]}"
            }
        )
    # For other endpoints, return default validation error
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    ) 