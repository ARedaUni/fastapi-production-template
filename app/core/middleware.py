"""Rate limiting middleware using slowapi."""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def get_client_ip(request: Request) -> str:
    """Get client IP address for rate limiting."""
    return get_remote_address(request)

# Create rate limiter instance with a global default limit
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["100/minute"]
)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom rate limit exceeded handler."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}"
        }
    )
