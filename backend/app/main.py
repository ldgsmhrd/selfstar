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
from dotenv import load_dotenv, dotenv_values
import os
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.health import HealthResponse

# .env 파일 로드 순서
# 1) 프로젝트 루트 .env
load_dotenv(dotenv_path=".env", override=True)
# 2) app/.env (보조 또는 덮어쓰기)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

# 로깅 초기화
logger = get_logger("env_loader")

# (디버그) 프로젝트 루트의 .env 파일 경로와 내용을 로그로 출력
logger.info("프로젝트 루트 .env 파일을 불러오는 중…")
try:
    with open(".env", "r", encoding="utf-8") as env_file:
        logger.info(".env 파일 내용:\n" + env_file.read())
except FileNotFoundError:
    logger.error("프로젝트 루트에서 .env 파일을 찾지 못했습니다.")
except UnicodeDecodeError as e:
    logger.error(f"인코딩 문제로 .env 파일을 읽지 못했습니다: {e}")

# 주요 환경변수 로깅
logger.info(f"KAKAO_CLIENT_ID: {os.getenv('KAKAO_CLIENT_ID')}")
logger.info(f"BACKEND_URL: {os.getenv('BACKEND_URL')}")
logger.info(f"FRONTEND_URL: {os.getenv('FRONTEND_URL')}")
logger.info(f"SESSION_SECRET: {os.getenv('SESSION_SECRET')}")

# (디버그) 루트/app의 .env 키/값 전체 로드 및 로그
env_values_root = dotenv_values(".env")
env_values_app = dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))
logger.info(f"루트 .env 로드 값: {env_values_root}")
logger.info(f"app/.env 로드 값: {env_values_app}")

app = FastAPI(debug=True)

# ===== CORS =====
FRONTEND_URL = settings.FRONTEND_URL
STRICT = settings.STRICT_CORS
allow_origins = [FRONTEND_URL, FRONTEND_URL.rstrip("/")] if STRICT else ["*"]

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

# ===== Static media (/media) =====
# 이미지 저장 경로를 앱 폴더 내부 media/로 설정 (환경변수 MEDIA_ROOT로 오버라이드 가능)
MEDIA_ROOT = os.getenv("MEDIA_ROOT") or os.path.join(os.path.dirname(__file__), "media")
try:
    os.makedirs(MEDIA_ROOT, exist_ok=True)
except Exception as _e:
    logger.error(f"Failed to create media directory {MEDIA_ROOT}: {_e}")

try:
    app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")
    logger.info(f"Mounted static media at /media -> {MEDIA_ROOT}")
except Exception as _e:
    logger.error(f"Failed to mount /media: {_e}")

# ===== Health =====
@app.get("/")
def root():
    return {"message": "Welcome to the API!"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# (디버그) 등록된 경로를 보려면 /__routes 로 확인 가능
@app.get("/__routes")
def routes_debug():
    return sorted(app.router.routes, key=lambda r: getattr(r, "path", ""))
    # 또는: return [getattr(r, "path", "") for r in app.router.routes]

# ===== App lifecycle =====
@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse.ok()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
