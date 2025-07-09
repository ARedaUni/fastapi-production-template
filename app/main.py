from fastapi import FastAPI
from app.core.config import settings
from app.api import router

app = FastAPI()
app.include_router(router, prefix=settings.V1_STR)


