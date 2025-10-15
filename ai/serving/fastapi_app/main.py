"""
[파트 개요] AI 서빙 엔트리
- 프론트 통신: 직접 없음, /health, /predict 제공
- 백엔드 통신: 백엔드(images 라우터)로부터 /predict 요청을 위임받아 처리
- 외부 통신: 선택적으로 Gemini(google-genai)를 통해 이미지 생성 호출
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import base64
from io import BytesIO
import logging
import traceback
import importlib
import os
from dotenv import load_dotenv
import sys

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

# 리포지토리 루트의 .env 로드(이 파일 기준 ../../..)
_APP_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_APP_DIR, "..", "..", ".."))
# Ensure repository root is importable (for ai.models.*)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
_ENV_PATH = os.path.join(_REPO_ROOT, ".env")
try:
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
    log.info(f"[ai] Loaded repo .env from {_ENV_PATH}")
except Exception as _e:
    log.warning(f".env load failed: {_e}")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-serving"}



class PredictRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., min_length=1, max_length=10)
    feature: Optional[str] = Field(None, max_length=2000)
    options: List[str] = Field(default_factory=list)
    # Accept same optional detailed fields as frontend/backend
    featureCombined: Optional[str] = Field(None, max_length=2000)
    faceShape: Optional[str] = None
    skinTone: Optional[str] = None
    hair: Optional[str] = None
    eyes: Optional[str] = None
    nose: Optional[str] = None
    lips: Optional[str] = None
    personalities: Optional[List[str]] = None


def _dynamic_model():

    env_module = os.getenv("AI_MODEL_MODULE")
    func_name = os.getenv("AI_MODEL_FUNC", "generate_image")

    candidates = []
    if env_module:
        candidates.append(env_module)
    # ai. 로 시작하면 접두어를 제거한 변형도 시도
        if env_module.startswith("ai."):
            candidates.append(env_module[len("ai."):])
        else:
            candidates.append("ai." + env_module)
    else:
        candidates.extend([
            "ai.models.imagemodel_gemini",
            "models.imagemodel_gemini",
        ])

    for module_name in candidates:
        try:
            mod = importlib.import_module(module_name)
            fn = getattr(mod, func_name)
            if callable(fn):
                log.info(f"Loaded model function: {module_name}.{func_name}")
                return fn
            log.warning(f"Function not callable: {module_name}.{func_name}")
        except Exception as e:
            log.warning(f"Dynamic model import failed for {module_name}: {e}")
    return None


MODEL_FN = _dynamic_model()

# Require model by default (previous strict behavior)
os.environ.setdefault("AI_REQUIRE_MODEL", "1")


@app.post("/predict")
async def predict(req: PredictRequest):
    try:
        require_model = (os.getenv("AI_REQUIRE_MODEL", "1").strip().lower() in ("1", "true", "yes"))
        log.info("/predict called: name=%s, gender=%s, require_model=%s", req.name, req.gender, require_model)

        # Gender normalization for downstream model
        def _gender_std(g: str) -> str:
            g = (g or "").strip().lower()
            mapping = {
                "여": "female", "여자": "female", "f": "female", "female": "female",
                "남": "male", "남자": "male", "m": "male", "male": "male",
            }
            return mapping.get(g, g or "unknown")

        # Build rich feature string
        parts: list[str] = []
        if req.feature:
            parts.append(str(req.feature))
        if req.featureCombined and req.featureCombined not in parts:
            parts.append(str(req.featureCombined))
        detail_bits: list[str] = []
        if req.faceShape: detail_bits.append(f"얼굴형:{req.faceShape}")
        if req.skinTone:  detail_bits.append(f"피부톤:{req.skinTone}")
        if req.hair:      detail_bits.append(f"헤어:{req.hair}")
        if req.eyes:      detail_bits.append(f"눈:{req.eyes}")
        if req.nose:      detail_bits.append(f"코:{req.nose}")
        if req.lips:      detail_bits.append(f"입:{req.lips}")
        if detail_bits:
            parts.append(", ".join(detail_bits))
        if req.personalities:
            try:
                parts.append("성격:" + "/".join([str(p) for p in req.personalities]))
            except Exception:
                pass
        feature_rich = " | ".join([p for p in parts if p]).strip()
        if len(feature_rich) > 1800:
            feature_rich = feature_rich[:1800]

        # If model required but not loaded, error
        if not callable(MODEL_FN):
            msg = "model_unavailable: set GOOGLE_API_KEY and AI_MODEL_MODULE=ai.models.imagemodel_gemini"
            log.warning(msg)
            if require_model:
                raise HTTPException(status_code=503, detail=msg)

        # Call model if available
        result = None
        if callable(MODEL_FN):
            try:
                result = MODEL_FN(req.name, _gender_std(req.gender), feature_rich or (req.feature or ""), req.options or [])
            except Exception as e:
                log.error("Gemini model error: %s", e)
                if require_model:
                    raise HTTPException(status_code=503, detail=f"gemini_failed: {e}")

        # Encode outputs
        if Image is not None and isinstance(result, Image.Image):
            buf = BytesIO(); result.save(buf, format="PNG")
            data = base64.b64encode(buf.getvalue()).decode("ascii")
            return {"ok": True, "image": f"data:image/png;base64,{data}"}
        elif isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], (bytes, bytearray)):
            buf, mime = result
            mime = mime or "image/png"
            data = base64.b64encode(buf).decode("ascii")
            return {"ok": True, "image": f"data:{mime};base64,{data}"}
        elif isinstance(result, (bytes, bytearray)):
            data = base64.b64encode(result).decode("ascii")
            return {"ok": True, "image": f"data:image/png;base64,{data}"}

        # Fallback placeholder if model not required
        if not require_model and Image is not None:
            try:
                img = Image.new("RGB", (768, 1024), color=(240, 242, 245))
                draw = ImageDraw.Draw(img)
                text = f"{req.name} / { _gender_std(req.gender) }\nPlaceholder portrait"
                draw.text((24, 24), text, fill=(30, 30, 30))
                buf = BytesIO(); img.save(buf, format="PNG")
                data = base64.b64encode(buf.getvalue()).decode("ascii")
                return {"ok": True, "image": f"data:image/png;base64,{data}"}
            except Exception as fe:
                log.warning("Fallback image failed: %s", fe)

        raise HTTPException(status_code=503, detail="unsupported_model_output")
    except HTTPException:
        raise
    except Exception as e:
        log.error("/predict failed: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"predict_failed: {e}")

