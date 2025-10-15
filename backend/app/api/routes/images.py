# backend/app/routes/images.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import html
import os
import httpx
import logging
import base64
from datetime import datetime

router = APIRouter(prefix="/api", tags=["images"])
log = logging.getLogger("images")


# 프론트에서 오는 값을 "그대로" 받는 스키마
class GenerateImageRequest(BaseModel):
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


@router.post("/image/generate")
async def generate_image(payload: GenerateImageRequest):
    """
    프론트 입력을 가공 없이 AI 서비스로 전달하고,
    data URI 이미지를 저장 후 URL과 함께 반환한다.
    """
    strict = os.getenv("AI_REQUIRE_MODEL", "true").lower() in {"1", "true", "yes", "y"}
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
        if strict:
            raise HTTPException(status_code=502, detail=f"ai_delegate_error: {e}")
        # non-strict이면 아래 폴백으로 진행
        r = None

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

        # AI가 ok=false거나 image 없음
        if strict:
            raise HTTPException(status_code=502, detail=f"ai_failed: {r.text}")
        return {"ok": False, "message": "ai_failed"}

    # --- strict 모드면 여기서 종료 ---
    if strict:
        raise HTTPException(status_code=503, detail="ai_unavailable")

    # --- non-strict 폴백: 간단한 SVG 카드 반환 ---
    try:
        name = html.escape(payload.name)
        gender = html.escape(payload.gender)
        # 폴백에서는 핵심 정보만 표시
        svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' width='520' height='520'>
  <defs>
    <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#3b82f6'/>
      <stop offset='100%' stop-color='#06b6d4'/>
    </linearGradient>
  </defs>
  <rect width='100%' height='100%' fill='url(#g)'/>
  <rect x='16' y='16' width='488' height='488' rx='24' fill='white' opacity='0.18'/>
  <g fill='#0f172a'>
    <text x='260' y='120' text-anchor='middle' font-size='28' font-weight='700'>SelfStar.AI</text>
    <text x='40' y='180' font-size='18'>이름: {name}</text>
    <text x='40' y='215' font-size='18'>성별: {gender}</text>
    <text x='40' y='250' font-size='16'>이미지 생성 서버에 연결되지 않아 폴백 SVG를 표시합니다.</text>
  </g>
</svg>
""".strip()

        data_url = "data:image/svg+xml;utf8," + svg.replace("\n", "").replace("  ", " ")
        # 저장 시도
        try:
            app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            media_root = os.getenv("MEDIA_ROOT") or os.path.join(app_dir, "media")
            os.makedirs(media_root, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"gen_{ts}.svg"
            out_path = os.path.join(media_root, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(svg)
            return {"ok": True, "image": data_url, "url": f"/media/{filename}"}
        except Exception as se:
            log.warning("fallback save media failed: %s", se)
            return {"ok": True, "image": data_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"generation_failed: {e}")
