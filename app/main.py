from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.api import router
from app.core.security import OAuth2Error
from app.api.exceptions import oauth2_exception_handler, validation_exception_handler
from app.core.middleware import limiter, rate_limit_exceeded_handler

# Add OpenAPI customization
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A lightweight FastAPI template for production",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register exception handlers
app.add_exception_handler(OAuth2Error, oauth2_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.include_router(router, prefix=settings.V1_STR)


