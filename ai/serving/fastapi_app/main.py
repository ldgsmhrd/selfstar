"""
[파트 개요] AI 서빙 엔트리
- 프론트 통신: 직접 없음, /health, /predict 제공
- 백엔드 통신: 백엔드(images 라우터)로부터 /predict 요청을 위임받아 처리
- 외부 통신: 선택적으로 Gemini(google-genai)를 통해 이미지 생성 호출
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Callable
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

# 리포지토리 루트의 .env 로드(이 파일 기준 ../../..)
_APP_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_APP_DIR, "..", "..", ".."))
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


# ====== 요청 스키마: 프론트/백에서 넘어온 값을 "그대로" 받는다. ======
class PredictRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., min_length=1, max_length=10)
    age: Optional[int] = None
    options: List[str] = Field(default_factory=list)

    faceShape: Optional[str] = None
    skinTone: Optional[str] = None
    hair: Optional[str] = None
    eyes: Optional[str] = None
    nose: Optional[str] = None
    lips: Optional[str] = None

    bodyType: Optional[str] = None
    glasses: Optional[str] = None
    personalities: Optional[List[str]] = None

    # 하위호환(남아있을 수 있는 구 필드)
    feature: Optional[str] = Field(None, max_length=2000)
    featureCombined: Optional[str] = Field(None, max_length=2000)


def _dynamic_model():
    """
    모델 함수를 동적으로 로드.
    우선순위:
      1) AI_MODEL_MODULE + AI_MODEL_FUNC (기본 generate_image_from_payload, 폴백 generate_image)
      2) ai.models.imagemodel_gemini
      3) models.imagemodel_gemini
    """
    env_module = os.getenv("AI_MODEL_MODULE")
    func_name_env = os.getenv("AI_MODEL_FUNC")  # 사용자가 명시했으면 우선 사용
    candidates = []

    if env_module:
        candidates.append(env_module)
        if env_module.startswith("ai."):
            candidates.append(env_module[len("ai."):])
        else:
            candidates.append("ai." + env_module)
    else:
        candidates.extend([
            "ai.models.imagemodel_gemini",
            "models.imagemodel_gemini",
        ])

    last_err = None
    for module_name in candidates:
        try:
            mod = importlib.import_module(module_name)
            # 새 시그니처 우선: generate_image_from_payload(payload)
            fn_new = getattr(mod, "generate_image_from_payload", None)
            if callable(fn_new):
                log.info(f"Loaded model function: {module_name}.generate_image_from_payload")
                return fn_new

            # 환경변수로 직접 지정된 함수명 시도
            if func_name_env:
                fn_env = getattr(mod, func_name_env, None)
                if callable(fn_env):
                    log.info(f"Loaded model function: {module_name}.{func_name_env}")
                    return fn_env

            # 레거시 시그니처: generate_image(name, gender, feature, options)
            fn_old = getattr(mod, "generate_image", None)
            if callable(fn_old):
                log.info(f"Loaded legacy model function: {module_name}.generate_image")
                return fn_old
        except Exception as e:
            last_err = e
            log.warning(f"Dynamic model import failed for {module_name}: {e}")

    if last_err:
        log.warning(f"Model import ultimately failed: {last_err}")
    return None


MODEL_FN: Optional[Callable[..., Any]] = _dynamic_model()

# 기본적으로 모델 필요(이전 strict 동작 유지)
os.environ.setdefault("AI_REQUIRE_MODEL", "1")


@app.post("/predict")
async def predict(req: PredictRequest):
    try:
        require_model = (os.getenv("AI_REQUIRE_MODEL", "1").strip().lower() in ("1", "true", "yes"))
        log.info("/predict called: name=%s, gender=%s, require_model=%s", req.name, req.gender, require_model)

        if not callable(MODEL_FN):
            msg = "model_unavailable: set GOOGLE_API_KEY and AI_MODEL_MODULE=ai.models.imagemodel_gemini"
            log.warning(msg)
            if require_model:
                raise HTTPException(status_code=503, detail=msg)

        result = None
        if callable(MODEL_FN):
            try:
                # 1) 새 시그니처 지원: payload 그대로 전달
                if MODEL_FN.__name__ == "generate_image_from_payload":
                    payload = req.dict(exclude_none=True)
                    result = MODEL_FN(payload)  # type: ignore
                else:
                    # 2) 레거시 시그니처 폴백: 가능한 한 원본 유지
                    #    feature는 구 모델 호환을 위해 전달(없으면 "")
                    result = MODEL_FN(
                        req.name,
                        req.gender,                       # 표준화 없이 그대로
                        req.feature or req.featureCombined or "",  # 하위호환
                        req.options or []
                    )  # type: ignore
            except Exception as e:
                log.error("Model error: %s", e)
                if require_model:
                    raise HTTPException(status_code=503, detail=f"model_failed: {e}")

        # ---- 출력 인코딩 ----
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

        # ---- 폴백 (모델 불필요 모드에서만) ----
        if not require_model and Image is not None:
            try:
                img = Image.new("RGB", (768, 1024), color=(240, 242, 245))
                draw = ImageDraw.Draw(img)
                text = f"{req.name} / {req.gender}\nPlaceholder portrait"
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
