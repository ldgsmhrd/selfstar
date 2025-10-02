from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(prefix="", tags=["health"])  # no extra prefix so it's /health


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
