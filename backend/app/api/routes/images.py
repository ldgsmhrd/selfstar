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
  # Core fields used by frontend today
  name: str = Field(..., min_length=1, max_length=100)
  gender: str = Field(..., min_length=1, max_length=10)
  feature: Optional[str] = Field(None, max_length=2000)
  options: List[str] = Field(default_factory=list)

  # Optional detailed fields (frontend may or may not send these)
  featureCombined: Optional[str] = Field(None, max_length=2000)
  faceShape: Optional[str] = None
  skinTone: Optional[str] = None
  hair: Optional[str] = None
  eyes: Optional[str] = None
  nose: Optional[str] = None
  lips: Optional[str] = None
  personalities: Optional[List[str]] = None


@router.post("/image/generate")
async def generate_image(payload: GenerateImageRequest):
  """
  Generate image by delegating to AI service. Aligns with frontend payload,
  builds a robust feature string, normalizes gender, and saves media locally.
  """
  # Strict mode: require AI by default. This enforces using Gemini via AI service.
  strict = os.getenv("AI_REQUIRE_MODEL", "true").lower() in {"1", "true", "yes", "y"}

  # Map Korean gender values to English for downstream AI service
  def _gender_std(g: str) -> str:
    g = (g or "").strip().lower()
    mapping = {
      "여": "female", "여자": "female", "f": "female", "female": "female",
      "남": "male", "남자": "male", "m": "male", "male": "male",
    }
    return mapping.get(g, g or "unknown")

  # Build final feature string using provided fields
  parts: List[str] = []
  if payload.feature:
    parts.append(str(payload.feature))
  if payload.featureCombined and payload.featureCombined not in parts:
    parts.append(str(payload.featureCombined))

  detail_bits: List[str] = []
  if payload.faceShape: detail_bits.append(f"얼굴형:{payload.faceShape}")
  if payload.skinTone:  detail_bits.append(f"피부톤:{payload.skinTone}")
  if payload.hair:      detail_bits.append(f"헤어:{payload.hair}")
  if payload.eyes:      detail_bits.append(f"눈:{payload.eyes}")
  if payload.nose:      detail_bits.append(f"코:{payload.nose}")
  if payload.lips:      detail_bits.append(f"입:{payload.lips}")
  if detail_bits:
    parts.append(", ".join(detail_bits))
  if payload.personalities:
    try:
      parts.append("성격:" + "/".join([str(p) for p in payload.personalities]))
    except Exception:
      pass

  feature_final = " | ".join([p for p in parts if p]).strip()
  if len(feature_final) > 1800:
    feature_final = feature_final[:1800]

  gender_std = _gender_std(payload.gender)

  # Delegate to AI service (default to local 8600 if env not provided)
  ai_url = os.getenv("AI_SERVICE_URL") or "http://localhost:8600"

  # Safe, compact logging (avoid huge payloads)
  try:
    log.info(
      "img.generate req: keys=%s feature_len=%s options=%s",
      sorted(list(payload.model_dump(exclude_none=True).keys())),
      len(feature_final or (payload.feature or "")),
      len(payload.options or []),
    )
  except Exception:
    pass

  if ai_url:
    try:
      async with httpx.AsyncClient(timeout=30.0) as client:
        body = {
          "name": payload.name,
          "gender": gender_std,
          "feature": feature_final or (payload.feature or ""),
          "options": payload.options or [],
          # pass through detailed fields as-is so AI can parse the same structure as frontend
          "featureCombined": payload.featureCombined,
          "faceShape": payload.faceShape,
          "skinTone": payload.skinTone,
          "hair": payload.hair,
          "eyes": payload.eyes,
          "nose": payload.nose,
          "lips": payload.lips,
          "personalities": payload.personalities,
        }
        # compact log: avoid dumping huge feature text
        _log_body = {k: (v if k not in {"feature", "featureCombined"} else f"<len {len(v) if v else 0}>") for k, v in body.items() if v is not None}
        log.info("Delegating image generation to AI: %s", _log_body)
        r = await client.post(f"{ai_url.rstrip('/')}/predict", json=body)
      if r.status_code == 200:
        data = r.json()
        if data.get("ok") and data.get("image"):
          # Save to media folder as file and return a URL for frontend
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
              # 간혹 응답이 너무 작은 경우(손상) 저장을 생략
              if not raw or len(raw) < 64:
                log.warning("image bytes too small: %s bytes", len(raw) if raw else 0)
                return {"ok": True, "image": data_uri}
              # Align save path with backend/app/main.py StaticFiles mount (/media -> backend/app/media)
              app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # -> backend/app
              media_root = os.getenv("MEDIA_ROOT") or os.path.join(app_dir, "media")
              os.makedirs(media_root, exist_ok=True)
              ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
              safe_name = f"gen_{ts}{ext}"
              out_path = os.path.join(media_root, safe_name)
              with open(out_path, "wb") as f:
                f.write(raw)
              media_url_path = f"/media/{safe_name}"
              return {"ok": True, "image": data_uri, "url": media_url_path}
          except Exception as se:
            log.warning("failed to save media: %s", se)
            return {"ok": True, "image": data_uri}
        if strict:
          raise HTTPException(status_code=502, detail=f"ai_failed: {data}")
    except Exception as e:
      if strict:
        raise HTTPException(status_code=502, detail=f"ai_delegate_error: {e}")
      # non-strict: continue to fallback

  if strict:
    raise HTTPException(status_code=503, detail="ai_unavailable")

  # Fallback: local SVG stub (only when not strict)
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

    # Save SVG to media folder so frontend can load via /media URL
    try:
      app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # -> backend/app
      media_root = os.getenv("MEDIA_ROOT") or os.path.join(app_dir, "media")
      os.makedirs(media_root, exist_ok=True)
      ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
      safe_name = f"gen_{ts}.svg"
      out_path = os.path.join(media_root, safe_name)
      with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
      media_url_path = f"/media/{safe_name}"
      return {"ok": True, "image": data_url, "url": media_url_path}
    except Exception as se:
      log.warning("fallback save media failed: %s", se)
      return {"ok": True, "image": data_url}
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"generation_failed: {e}")
