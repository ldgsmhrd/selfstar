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

try:
    from .images import router as images_router
    router.include_router(images_router)
except Exception:
    pass

try:
    from .userdata import router as userinfo_router
    router.include_router(userinfo_router, tags=["users"])
except Exception:
    pass

try:
    from .persona import router as persona_router
    router.include_router(persona_router, tags=["personas"])
except Exception:
    pass

try:
    from .oauth_instagram import router as ig_router
    router.include_router(ig_router)
except Exception:
    pass

try:
    from .instagram_webhook import router as ig_webhook_router
    router.include_router(ig_webhook_router)
except Exception:
    pass

try:
    from .files import router as files_router
    router.include_router(files_router)
except Exception:
    pass

"""
주의: instagram 관련 일반 API(게시글/인사이트/게시)는 /api 접두사로만 노출하기 위해
여기(router 집계)에서는 등록하지 않습니다. app.main에서 prefix="/api"로만 include합니다.
- instagram_publish
- instagram_comments
- instagram_insights
OAuth(redirect/callback)은 기존처럼 /oauth/instagram 경로로 유지합니다.
"""

# instagram_comments: app.main에서 /api 접두사로만 등록

# instagram_insights: app.main에서 /api 접두사로만 등록

try:
    # chat 라우터는 전역(router)에는 등록하지 않습니다.
    # 백엔드 엔트리(app.main)에서 '/api' 접두사로만 노출하여
    # 일관되게 /api/chat 경로만 사용하도록 강제합니다.
    pass
except Exception:
    pass
