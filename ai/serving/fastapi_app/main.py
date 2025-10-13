from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import base64
from io import BytesIO
import logging
import traceback
import importlib
import os
from dotenv import load_dotenv

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None  # type: ignore

app = FastAPI(title="AI Serving Minimal", version="0.0.1")
log = logging.getLogger("ai-serving")
logging.basicConfig(level=logging.INFO)

# 사용법:
#  - 기본 로컬 데모: 내장 Pillow 생성기 사용(환경변수 미설정)
#  - Gemini 사용:
#      setx GOOGLE_API_KEY "<your_key>"
#      setx AI_MODEL_MODULE "ai.models.imagemodel_gemini"
#      setx AI_MODEL_FUNC "generate_image"
#    재기동 후 /predict 호출 시 Gemini가 이미지 생성

# Load .env from repo root (../../.. from this file)
_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
try:
    load_dotenv(dotenv_path=_ENV_PATH, override=False)
    log.info(f"Loaded .env from {_ENV_PATH}")
except Exception as _e:
    log.warning(f".env load failed: {_e}")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-serving"}

# Run dev server example (from repo root):
#   python -m uvicorn ai.serving.fastapi_app.main:app --host 0.0.0.0 --port 8600 --reload


class PredictRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., min_length=1, max_length=10)
    feature: Optional[str] = Field(None, max_length=200)
    options: List[str] = Field(default_factory=list)


def _dynamic_model():
    """환경변수로 지정된 모델을 동적으로 임포트하여 함수 핸들을 반환합니다."""
    module_name = os.getenv("AI_MODEL_MODULE", "ai.models.imagemodel_gemini")
    func_name = os.getenv("AI_MODEL_FUNC", "generate_image")
    try:
        mod = importlib.import_module(module_name)
        fn = getattr(mod, func_name)
        if callable(fn):
            log.info(f"Loaded model function: {module_name}.{func_name}")
            return fn
        log.warning(f"Function not callable: {module_name}.{func_name}")
    except Exception as e:
        log.warning(f"Dynamic model import failed: {e}")
    return None


MODEL_FN = _dynamic_model()


@app.post("/predict")
def predict(req: PredictRequest):
    try:
        if Image is None:
            raise RuntimeError("Pillow not installed. Install ai/requirements.txt (needs Pillow).")

        # 동적 모델이 있으면 우선 사용
        if callable(MODEL_FN):
            try:
                result = MODEL_FN(req.name, req.gender, req.feature, req.options)
                if isinstance(result, Image.Image):
                    buf = BytesIO(); result.save(buf, format="PNG")
                    data = base64.b64encode(buf.getvalue()).decode("ascii")
                    return {"ok": True, "image": f"data:image/png;base64,{data}"}
                elif isinstance(result, (bytes, bytearray)):
                    data = base64.b64encode(result).decode("ascii")
                    return {"ok": True, "image": f"data:image/png;base64,{data}"}
                else:
                    log.warning("MODEL_FN returned unsupported type; falling back to built-in generator")
            except Exception as e:
                log.error("Model function error: %s", e)

        img = Image.new("RGB", (640, 640), (15, 23, 42))
        draw = ImageDraw.Draw(img)

        # Robust font loader: prefer a Unicode-capable font (Korean supported) on Windows
        def load_font(size: int = 24):
            candidates = [
                # Common Windows fonts (Korean)
                "C:/Windows/Fonts/malgun.ttf",  # Malgun Gothic
                "C:/Windows/Fonts/malgunbd.ttf",
                # Arial Unicode MS (if available)
                "C:/Windows/Fonts/arialuni.ttf",
                # Fallback to Arial
                "C:/Windows/Fonts/arial.ttf",
                "arial.ttf",
            ]
            for path in candidates:
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
            # Final fallback: default bitmap font (ASCII). We'll sanitize text if needed.
            return ImageFont.load_default()

        font = load_font(24)

        # Safely draw text that may contain non-ASCII characters even with limited fonts
        def safe_text(xy, text: str, fill, font):
            try:
                draw.text(xy, text, fill=fill, font=font)
            except Exception:
                # As a last resort, strip non-ASCII to avoid crashes
                ascii_text = text.encode("ascii", "ignore").decode("ascii")
                draw.text(xy, ascii_text, fill=fill, font=font)

        y = 40
        safe_text((32, y), "SelfStar.AI - Image Model", fill=(255,255,255), font=font); y += 40
        safe_text((32, y), f"이름: {req.name}", fill=(200, 230, 255), font=font); y += 32
        safe_text((32, y), f"성별: {req.gender}", fill=(200, 230, 255), font=font); y += 32
        safe_text((32, y), f"특징: {req.feature or '-'}", fill=(200, 230, 255), font=font); y += 32
        safe_text((32, y), f"옵션: {', '.join(req.options) or '(none)'}", fill=(200, 230, 255), font=font)

        buf = BytesIO()
        img.save(buf, format="PNG")
        data = base64.b64encode(buf.getvalue()).decode("ascii")
        return {"ok": True, "image": f"data:image/png;base64,{data}"}
    except HTTPException:
        raise
    except Exception as e:
        log.error("/predict failed: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"predict_failed: {e}")

