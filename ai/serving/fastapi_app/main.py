"""
[파트 개요] AI 서빙 엔트리
- 프론트 통신: 직접 없음, /health, /predict 제공
- 백엔드 통신: 백엔드(images 라우터)로부터 /predict 요청을 위임받아 처리
- 외부 통신: 선택적으로 Gemini(google-genai)를 통해 이미지 생성 호출
"""
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

# 리포지토리 루트의 .env 로드(이 파일 기준 ../../..)
_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
try:
    load_dotenv(dotenv_path=_ENV_PATH, override=False)
    log.info(f"Loaded .env from {_ENV_PATH}")
except Exception as _e:
    log.warning(f".env load failed: {_e}")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-serving"}



class PredictRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., min_length=1, max_length=10)
    feature: Optional[str] = Field(None, max_length=200)
    options: List[str] = Field(default_factory=list)


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


@app.post("/predict")
def predict(req: PredictRequest):
    try:
    # Pillow 미설치 시 500 대신 최소한의 placeholder 이미지를 반환
        if Image is None:
            log.warning("Pillow not installed; returning placeholder image. Install ai/requirements.txt to enable text rendering.")
            # 1x1 투명 PNG
            tiny_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
            return {"ok": True, "image": f"data:image/png;base64,{tiny_png_b64}"}

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

    # 견고한 폰트 로더: Windows에서 한글을 지원하는 유니코드 폰트를 우선 시도
        def load_font(size: int = 24):
            candidates = [
                # Windows의 한글 폰트 후보
                "C:/Windows/Fonts/malgun.ttf",  # Malgun Gothic
                "C:/Windows/Fonts/malgunbd.ttf",
                # Arial Unicode MS (있다면)
                "C:/Windows/Fonts/arialuni.ttf",
                # 최종 백업: Arial
                "C:/Windows/Fonts/arial.ttf",
                "arial.ttf",
            ]
            for path in candidates:
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
            # 마지막 수단: 기본 비트맵 폰트(ASCII). 필요 시 텍스트 정제.
            return ImageFont.load_default()

        font = load_font(24)

    # 제한적인 폰트 환경에서도 비-ASCII 문자가 포함될 수 있는 텍스트를 안전하게 그리기
        def safe_text(xy, text: str, fill, font):
            try:
                draw.text(xy, text, fill=fill, font=font)
            except Exception:
                # 최후의 수단: 충돌 방지를 위해 비-ASCII 제거
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

