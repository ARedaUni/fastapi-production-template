from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", status_code=200)
async def root():
    return {"health": "ok"}


