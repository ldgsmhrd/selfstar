from fastapi import APIRouter

router = APIRouter()

try:
    from .auth import router as auth_router
    router.include_router(auth_router)
except Exception:
    pass

try:
    from .posts import router as posts_router
    router.include_router(posts_router, tags=["posts"])
except Exception:
    pass
