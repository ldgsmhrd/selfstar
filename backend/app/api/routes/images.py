# backend/app/routes/images.py
from fastapi import APIRouter, HTTPException
import os
import httpx
import logging
import base64
from datetime import datetime

from app.api.schemas.images import GenerateImageRequest

router = APIRouter(prefix="/api", tags=["images"])
log = logging.getLogger("images")


@router.post("/images") 
async def generate_image(payload: GenerateImageRequest):
    """
    프론트 입력을 가공 없이 AI 서비스로 전달하고,
    data URI 이미지를 저장 후 URL과 함께 반환한다.
    """
    # Gemini만 사용하므로 폴백을 비활성화하고 항상 엄격 모드로 처리합니다.
    strict = True
    ai_url = os.getenv("AI_SERVICE_URL") or "http://localhost:8600"

    # 그대로 전달할 바디
    body = payload.model_dump(exclude_none=True)

    # 안전 로그(민감/대용량 없음)
    try:
        log.info(
            "img.generate pass-through keys=%s",
            sorted(list(body.keys())),
        )
    except Exception:
        pass

    # --- AI 서비스 호출 ---
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{ai_url.rstrip('/')}/predict", json=body)
    except Exception as e:
        # 폴백 없이 즉시 실패 처리
        raise HTTPException(status_code=502, detail=f"ai_delegate_error: {e}")

    # --- 성공 응답 처리 ---
    if r is not None and r.status_code == 200:
        data = r.json()
        if data.get("ok") and data.get("image"):
            data_uri = data["image"]
            # /media 저장 시도 (data URI가 너무 작으면 저장 생략)
            try:
                if data_uri.startswith("data:") and "," in data_uri:
                    header, b64 = data_uri.split(",", 1)
                    mime = header.split(";")[0].split(":", 1)[1] if ":" in header else "image/png"
                    ext = {
                        "image/png": ".png",
                        "image/jpeg": ".jpg",
                        "image/webp": ".webp",
                    }.get(mime, ".bin")
                    raw = base64.b64decode(b64)
                    if not raw or len(raw) < 64:
                        log.warning("image bytes too small: %s bytes", len(raw) if raw else 0)
                        return {"ok": True, "image": data_uri}

                    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # backend/app
                    media_root = os.getenv("MEDIA_ROOT") or os.path.join(app_dir, "media")
                    os.makedirs(media_root, exist_ok=True)
                    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"gen_{ts}{ext}"
                    out_path = os.path.join(media_root, filename)
                    with open(out_path, "wb") as f:
                        f.write(raw)
                    return {"ok": True, "image": data_uri, "url": f"/media/{filename}"}
            except Exception as se:
                log.warning("failed to save media: %s", se)
                return {"ok": True, "image": data_uri}

        # AI가 ok=false거나 image 없음 → 즉시 실패 처리
        raise HTTPException(status_code=502, detail=f"ai_failed: {r.text}")

        # AI 서버 사용이 필수이므로, 여기까지 도달했다면 가용한 응답이 없는 상태입니다.
        raise HTTPException(status_code=503, detail="ai_unavailable")
