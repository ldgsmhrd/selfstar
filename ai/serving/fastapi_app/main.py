"""
SelfStar AI FastAPI entrypoint
- Exposes: /health, /predict, /chat, /chat/image, /chat/health
- Loads repo root .env so GOOGLE_API_KEY etc are available
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
try:
	from ai.serving.fastapi_app.routes.caption import router as caption_router
	_HAS_CAPTION = True
except Exception as e:
	import logging as _logging
	_logging.getLogger("ai-main").error("caption router import failed: %s", e)
	_HAS_CAPTION = False
try:
	from ai.serving.fastapi_app.routes.chat import router as chat_router
	_HAS_CHAT = True
except Exception as e:
	# Defer import errors to runtime logs but keep server up
	import logging
	logging.getLogger("ai-main").error("chat router import failed: %s", e)
	_HAS_CHAT = False

app = FastAPI(title="SelfStar AI", version="0.1.0")
app.include_router(image_router)
if _HAS_CHAT:
	app.include_router(chat_router)
if _HAS_CAPTION:
	app.include_router(caption_router)

# Optional comment model router
try:
	from ai.serving.fastapi_app.routes.comment_model import router as comment_router
	app.include_router(comment_router)
except Exception as e:
	import logging
	logging.getLogger("ai-main").error("comment router import failed: %s", e)

@app.get("/__routes")
def __routes():
	# quick route list for debugging
	return sorted([getattr(r, "path", "") for r in app.router.routes])
