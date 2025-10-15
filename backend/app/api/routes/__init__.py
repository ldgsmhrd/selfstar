from fastapi import APIRouter
import logging

log = logging.getLogger("api.routes")

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

added_userinfo = False
for modname in (".유저정보데이터", ".userdata"):
    try:
        userinfo_router = __import__(__name__ + modname, fromlist=["router"]).router  # type: ignore
        router.include_router(userinfo_router, tags=["users"])
        log.info(f"registered userinfo router from {modname}")
        added_userinfo = True
        break
    except Exception as e:
        log.warning(f"failed to register userinfo router from {modname}: {e}")
if not added_userinfo:
    log.error("no userinfo router registered; /user/me/birthday will 404")
