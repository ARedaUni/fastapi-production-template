from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.api import router
from app.core.security import OAuth2Error
from app.core.exceptions import oauth2_exception_handler, validation_exception_handler

app = FastAPI()

# Register exception handlers
app.add_exception_handler(OAuth2Error, oauth2_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(router, prefix=settings.V1_STR)


