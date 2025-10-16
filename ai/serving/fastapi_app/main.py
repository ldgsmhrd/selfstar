"""
serving/fastapi_app 하위의 AI FastAPI 애플리케이션 엔트리입니다.
ai.serving.fastapi_app.main:app 엔드포인트를 노출합니다.
저장소 루트의 .env를 로드합니다.
routes/image_model에서 라우터를 포함합니다.
"""
from fastapi import FastAPI
from dotenv import load_dotenv
import os
import sys

# Ensure repo root .env is visible
_THIS = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_THIS, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
load_dotenv(dotenv_path=os.path.join(_ROOT, ".env"), override=True)

from ai.serving.fastapi_app.routes.image_model import router as image_router

app = FastAPI(title="SelfStar AI", version="0.1.0")
app.include_router(image_router)
"""
최상위 AI FastAPI 애플리케이션 엔트리입니다.
루트 경로에 라우터를 마운트합니다('/health', '/predict').
앱 경로를 고정합니다: ai.main:app
"""
from fastapi import FastAPI
from dotenv import load_dotenv
import os
import sys

# Ensure repo root .env is visible
_THIS = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_THIS, ".."))
if _ROOT not in sys.path:
	sys.path.insert(0, _ROOT)
load_dotenv(dotenv_path=os.path.join(_ROOT, ".env"), override=True)

from ai.serving.fastapi_app.routes.image_model import router as image_router

app = FastAPI(title="SelfStar AI", version="0.1.0")
app.include_router(image_router)
