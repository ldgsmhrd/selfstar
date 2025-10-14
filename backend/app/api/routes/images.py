"""
[파트 개요] 이미지 생성 라우터
- 프론트 통신: /api/image/generate 엔드포인트 제공
- AI 통신: AI 서비스(/predict)에 요청 위임 후 data URI 수신 → media 파일로 저장
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import html
import os
import httpx
import logging
import base64
from datetime import datetime
import pathlib

router = APIRouter(prefix="/api", tags=["images"])
log = logging.getLogger("images")


class GenerateImageRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., min_length=1, max_length=10)
    feature: Optional[str] = Field(None, max_length=200)
    options: List[str] = Field(default_factory=list)


@router.post("/image/generate")
async def generate_image(payload: GenerateImageRequest):
  """
  AI 서비스에 위임하여 이미지를 생성합니다. 엄격 모드(기본값)에서는
  로컬 SVG 대체를 사용하지 않고 오류를 반환합니다.
  """
  # 엄격 모드(기본 True): AI 가용성 문제나 실패 시 SVG 대체 없이 오류를 반환합니다.
  # AI 서버와 동일한 플래그를 재사용합니다.
  strict = os.getenv("AI_REQUIRE_MODEL", "true").lower() in {"1", "true", "yes", "y"}

  # AI 서비스 URL이 설정된 경우 해당 서비스로 위임합니다.
  ai_url = os.getenv("AI_SERVICE_URL")
  if ai_url:
    try:
      async with httpx.AsyncClient(timeout=30.0) as client:
        body = payload.model_dump()
        log.info("Delegating image generation to AI: %s", body)
        r = await client.post(f"{ai_url.rstrip('/')}/predict", json=body)
      if r.status_code == 200:
        data = r.json()
        if data.get("ok") and data.get("image"):
          # media 폴더에 파일로 저장 후 프론트에 제공할 URL 반환
          data_uri = data["image"]
          try:
            if data_uri.startswith("data:") and "," in data_uri:
              header, b64 = data_uri.split(",", 1)
              mime = header.split(";")[0].split(":",1)[1] if ":" in header else "image/png"
              ext = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/webp": ".webp",
              }.get(mime, ".bin")
              raw = base64.b64decode(b64)
              # MEDIA_ROOT 환경변수 사용, 없으면 app/media 로 저장(app.main 과 동일)
              # __file__ = .../backend/app/api/routes/images.py
              # 실제 경로 목표: .../backend/app/media
              base_app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
              media_root = os.getenv("MEDIA_ROOT") or os.path.join(base_app_dir, "media")
              os.makedirs(media_root, exist_ok=True)
              ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
              safe_name = f"gen_{ts}{ext}"
              out_path = os.path.join(media_root, safe_name)
              with open(out_path, "wb") as f:
                f.write(raw)
              # /media 마운트로 제공되는 URL 경로
              media_url_path = f"/media/{safe_name}"
              return {"ok": True, "image": data_uri, "url": media_url_path}
          except Exception as se:
            log.warning("failed to save media: %s", se)
            # 저장 실패 시 데이터 URI만 반환
            return {"ok": True, "image": data_uri}
        if strict:
          raise HTTPException(status_code=502, detail=f"ai_failed: {data}")
    except Exception as e:
      if strict:
        raise HTTPException(status_code=502, detail=f"ai_delegate_error: {e}")
      # 비엄격 모드: 아래 로컬 대체로 진행

  if strict:
    raise HTTPException(status_code=503, detail="ai_unavailable")

  # 로컬 대체: 간단한 SVG (비엄격 모드에서만 사용)
  try:
    name = html.escape(payload.name)
    gender = html.escape(payload.gender)
    feature = html.escape(payload.feature or "-")
    options = ", ".join([html.escape(o) for o in payload.options]) or "(none)"

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
  <text x='40' y='250' font-size='18'>특징: {feature}</text>
  <text x='40' y='285' font-size='18'>옵션: {options}</text>
  </g>
</svg>
""".strip()

    data_url = "data:image/svg+xml;utf8," + svg.replace("\n", "").replace("  ", " ")
    return {"ok": True, "image": data_url}
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"generation_failed: {e}")
