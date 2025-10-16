"""
AI FastAPI application entry (under serving/fastapi_app).
- Exposes `ai.serving.fastapi_app.main:app`
- Loads repo .env
- Includes routes from routes/image_model
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
Top-level AI FastAPI application entry.
- Mounts routers under root ('/health', '/predict').
- Keeps the app path stable: `ai.main:app`
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
