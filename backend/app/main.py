"""
[파트 개요] Backend 메인 엔트리포인트
- 프론트 통신: CORS/세션 설정으로 프론트(기본 5174)와 안전한 쿠키/요청 교환
- AI 통신: 이미지 생성 등은 images 라우터에서 AI 서버(기본 8600)로 위임
- 외부 통신: OAuth 등 외부 프로바이더는 auth 라우터에서 처리
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import logging
from dotenv import load_dotenv, dotenv_values, find_dotenv
import os
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.health import HealthResponse
from urllib.parse import urlparse
import asyncio

# .env 파일 로드 순서 (컨테이너/로컬 모두에서 동작)
# - 앱 디렉터리: /app/app
# - 리포지토리 루트(컨테이너 기준): /app
_APP_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_APP_DIR, ".."))  # /app/app -> /app
_ROOT_ENV = os.path.join(_REPO_ROOT, ".env")  # /app/.env

# 1) 리포지토리 루트 .env (최우선)
load_dotenv(dotenv_path=_ROOT_ENV, override=True)
# 2) app/.env (보조 또는 덮어쓰기)
load_dotenv(dotenv_path=os.path.join(_APP_DIR, ".env"), override=True)

# 로깅 초기화
logger = get_logger("env_loader")

# (디버그) 프로젝트 루트의 .env 파일 경로와 내용을 로그로 출력
logger.info("리포지토리 루트 .env 파일을 불러오는 중…")
if not os.path.exists(_ROOT_ENV):
    logger.warning(f"루트 .env 파일({_ROOT_ENV})을 찾지 못했습니다. compose/env_file 또는 환경변수를 사용 중일 수 있습니다.")

# 주요 환경변수 로깅
logger.info(f"KAKAO_CLIENT_ID set: {'yes' if os.getenv('KAKAO_CLIENT_ID') else 'no'}")
logger.info(f"BACKEND_URL: {os.getenv('BACKEND_URL')}")
logger.info(f"FRONTEND_URL: {os.getenv('FRONTEND_URL')}")
logger.info(f"SESSION_SECRET set: {'yes' if os.getenv('SESSION_SECRET') else 'no'}")

# (디버그) 루트/app의 .env 키/값 전체 로드 및 로그
try:
    env_values_root = dotenv_values(_ROOT_ENV)
    logger.info(f"루트 .env 키 수: {len(env_values_root or {})}")
except Exception:
    pass
try:
    env_values_app = dotenv_values(os.path.join(_APP_DIR, ".env"))
    logger.info(f"app/.env 키 수: {len(env_values_app or {})}")
except Exception:
    pass

app = FastAPI(debug=True)

# ===== CORS =====
# 브라우저 쿠키(credential)를 사용하므로 절대 와일드카드(*)를 쓰지 않습니다.
# FRONTEND_URL 을 기반으로 localhost/127.0.0.1 변형과 5173/5174 포트까지 화이트리스트에 추가합니다.
FRONTEND_URL = settings.FRONTEND_URL

def _origin_variants(url: str) -> list[str]:
    try:
        p = urlparse(url)
        if not p.scheme or not p.netloc:
            return []
        host = p.hostname or "localhost"
        port = p.port or (5174 if host in {"localhost", "127.0.0.1"} else None)
        scheme = p.scheme
        candidates = set()
        def add(h: str, prt: int|None):
            if prt:
                base = f"{scheme}://{h}:{prt}"
            else:
                base = f"{scheme}://{h}"
            candidates.add(base)
            candidates.add(base.rstrip('/'))
        # 입력 URL 그대로
        add(host, port)
        # localhost/127.0.0.1 상호 변환
        if host == "localhost":
            add("127.0.0.1", port)
        if host == "127.0.0.1":
            add("localhost", port)
        # Vite 기본 포트 변형
        for alt_port in (5173, 5174):
            if port != alt_port:
                add(host, alt_port)
                add("127.0.0.1", alt_port)
                add("localhost", alt_port)
        return sorted(candidates)
    except Exception:
        return []

allow_origins = sorted(set([FRONTEND_URL, FRONTEND_URL.rstrip("/")] + _origin_variants(FRONTEND_URL)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Session (쿠키 기반) =====
SESSION_SECRET = settings.SESSION_SECRET
# 세션을 1일(86400초) 동안 유지
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, max_age=86400)

# (디버그) 세션 시크릿과 MySQL 풀 초기화 로그
logger.info(f"SESSION_SECRET: {SESSION_SECRET}")
logger.info("Initializing MySQL pool...")

# ===== Routers =====
# api 라우터 집계(import 에러 무시)
try:
    from app.api.routes import router as api_router
    app.include_router(api_router)
    logger.info("api_router registered from app.api.routes")
except Exception as e:
    logger.warning(f"No api_router found in app.api.routes: {e}")

# 중요 엔드포인트는 개별 포함도 시도하여, 일부 라우트 모듈 오류로 집계가 누락되어도 최소 동작 보장
try:
    from app.api.routes.instagram_comments import router as ig_comments_router
    # /api 접두사 경로로만 노출 (정책)
    app.include_router(ig_comments_router, prefix="/api")
    logger.info("instagram_comments router registered explicitly under /api prefix")
except Exception as e:
    logger.warning(f"Failed to register instagram_comments router under /api: {e}")

try:
    from app.api.routes.instagram_insights import router as ig_insights_router
    app.include_router(ig_insights_router, prefix="/api")
    logger.info("instagram_insights router registered explicitly under /api prefix")
except Exception as e:
    logger.warning(f"Failed to register instagram_insights router under /api: {e}")

# chat 라우터도 /api 접두사 경로를 병행 제공 (nginx 특수 매핑 미적용 환경 대비)
try:
    from app.api.routes.chat import router as chat_router_direct
    app.include_router(chat_router_direct, prefix="/api")
    logger.info("chat router additionally registered under /api prefix")
except Exception as e:
    logger.warning(f"Failed to additionally register chat router under /api: {e}")

# ===== Static mounts =====
# media (기존 자산)
_DEFAULT_MEDIA = os.path.join(os.path.dirname(__file__), "media")
MEDIA_ROOT = os.getenv("MEDIA_ROOT") or _DEFAULT_MEDIA
try:
    os.makedirs(MEDIA_ROOT, exist_ok=True)
except Exception as _e:
    logger.error(f"Failed to create media directory {MEDIA_ROOT}: {_e}")

try:
    app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")
    logger.info(f"Mounted static media at /media -> {MEDIA_ROOT}")
except Exception as _e:
    logger.error(f"Failed to mount /media: {_e}")

# (제거) files 정적 마운트는 더 이상 사용하지 않음(S3로 대체)

# ===== Health =====
@app.get("/")
def root():
    return {"message": "Welcome to the API!"}

# (디버그) 등록된 경로를 보려면 /__routes 로 확인 가능
@app.get("/__routes")
def routes_debug():
    # Route 객체 자체는 JSON 직렬화가 어려우므로 경로 문자열만 반환
    return sorted([getattr(r, "path", "") for r in app.router.routes])

# ===== App lifecycle =====
@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse.ok()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

# ===== Background: Daily insights snapshot =====
async def _daily_snapshot_loop():
    """Run once a day: iterate linked personas and perform snapshot."""
    # Lazy imports to avoid circular
    from app.api.core.mysql import get_mysql_pool
    from app.api.routes.instagram_insights import perform_snapshot
    import aiomysql
    while True:
        try:
            pool = await get_mysql_pool()
            personas = []
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    # ss_persona에 IG가 연결되어 있고, persona 토큰도 존재하는 페르소나만
                    await cur.execute(
                        """
                        SELECT p.user_id, p.user_persona_num
                        FROM ss_persona p
                        JOIN ss_instagram_connector_persona t
                          ON t.user_id = p.user_id AND t.user_persona_num = p.user_persona_num
                        WHERE p.ig_user_id IS NOT NULL
                        LIMIT 500
                        """
                    )
                    personas = await cur.fetchall() or []
            for row in personas:
                try:
                    await perform_snapshot(int(row["user_id"]), int(row["user_persona_num"]))
                except Exception:
                    # non-fatal; continue others
                    pass
        except Exception:
            pass
        # sleep until next run (~24h). Start quickly next day; if server restarts midday, still runs 24h cadence.
        await asyncio.sleep(60 * 60 * 24)


@app.on_event("startup")
async def _start_background_tasks():
    # fire-and-forget daily loop
    try:
        asyncio.create_task(_daily_snapshot_loop())
    except Exception:
        pass
