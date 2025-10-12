from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import html
import os
import httpx

router = APIRouter(prefix="/api", tags=["images"])


class GenerateImageRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., min_length=1, max_length=10)
    feature: Optional[str] = Field(None, max_length=200)
    options: List[str] = Field(default_factory=list)


@router.post("/image/generate")
async def generate_image(payload: GenerateImageRequest):
    """
    Delegates to AI service for image generation when configured.
    Falls back to a local SVG data URL for resilience in dev.
    """
    ai_url = os.getenv("AI_SERVICE_URL")
    if ai_url:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(f"{ai_url.rstrip('/')}/predict", json=payload.model_dump())
            if r.status_code == 200:
                data = r.json()
                if data.get("ok") and data.get("image"):
                    return {"ok": True, "image": data["image"]}
                # else fall through to fallback
        except Exception:
            pass

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
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import html
import os
import httpx

router = APIRouter(prefix="/api", tags=["images"])


class GenerateImageRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., min_length=1, max_length=10)
    feature: Optional[str] = Field(None, max_length=200)
    options: List[str] = Field(default_factory=list)


@router.post("/image/generate")
async def generate_image(payload: GenerateImageRequest):
    """
    Temporary image generator endpoint.
    Returns a data URL with an SVG preview including requested attributes.
    This is a stub to be swapped with the real AI service.
    """
    # If AI service URL is configured, delegate to it
    ai_url = os.getenv("AI_SERVICE_URL")
    if ai_url:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(f"{ai_url.rstrip('/')}/predict", json=payload.model_dump())
            if r.status_code == 200:
                data = r.json()
                if data.get("ok") and data.get("image"):
                    return {"ok": True, "image": data["image"]}
                # else fall back
        except Exception:
            # Log could be added here if a logger exists; for now, silently fall back.
            pass

    # fallback: local SVG stub
    try:
        # Sanitize inputs for embedding in XML
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
