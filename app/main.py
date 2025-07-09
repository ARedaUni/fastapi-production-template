from fastapi import FastAPI
from app.core.config import get_settings
from app.api import router

app = FastAPI()
settings = get_settings()
app.include_router(router, prefix=settings.V1_STR)


