from fastapi import APIRouter, HTTPException
from typing import Optional, Tuple
import logging
import os
import base64
import httpx

from google import genai
from google.genai import types

from ai.serving.fastapi_app.schemas.caption import CaptionRequest, CaptionResponse

router = APIRouter()
log = logging.getLogger("ai-caption")

_client = None


def _get_client():
    global _client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client


GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
CAPTION_PROMPT_OVERRIDE = os.getenv("CAPTION_PROMPT")  # If set, use this exact prompt text from the notebook
# Align defaults to the notebook: temperature=0.9, top_p=0.95, no explicit max tokens
CAPTION_TEMPERATURE = float(os.getenv("CAPTION_TEMPERATURE", "0.9"))
CAPTION_TOP_P = float(os.getenv("CAPTION_TOP_P", "0.95"))
CAPTION_MAX_TOKENS_ENV = os.getenv("CAPTION_MAX_TOKENS", "")
CAPTION_MAX_TOKENS = int(CAPTION_MAX_TOKENS_ENV) if CAPTION_MAX_TOKENS_ENV.isdigit() else None


async def _fetch_image_bytes(uri_or_url: str) -> Tuple[bytes, str]:
    # data URI
    if uri_or_url.startswith("data:"):
        try:
            head, b64 = uri_or_url.split(",", 1)
            mime = "image/jpeg"
            try:
                prefix = head.split(";")[0]
                if prefix.startswith("data:"):
                    mime = prefix[len("data:"):]
            except Exception:
                pass
            return base64.b64decode(b64), mime
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"invalid_data_uri: {e}")
    # http(s)
    if uri_or_url.startswith("http://") or uri_or_url.startswith("https://"):
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(uri_or_url)
                r.raise_for_status()
                mime = r.headers.get("content-type", "image/jpeg").split(";")[0]
                return r.content, mime
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"failed_to_fetch_image: {e}")
    raise HTTPException(status_code=400, detail="image must be a data URI or http(s) URL")


def _build_caption_prompt(personality: Optional[str], tone: Optional[str]) -> str:
        """Build the exact notebook prompt (MBTI-driven caption prompt).

        NOTE: If CAPTION_PROMPT is provided, it will be used verbatim.
        """
        if isinstance(CAPTION_PROMPT_OVERRIDE, str) and CAPTION_PROMPT_OVERRIDE.strip():
                return CAPTION_PROMPT_OVERRIDE.strip()
        p = (personality or "ISTJ").strip()
        return (
                f"""
You are a Korean lifestyle influencer with the MBTI type "{p}".
Imagine that **you are the person in the uploaded photo**, and you are posting it on your own Instagram feed.
Write the **main caption** that expresses your genuine thoughts or feelings in that moment.

Requirements:
- Write **in Korean**.
- Express what someone with the {p} personality would *feel, think, or want to say* in that situation.
    Make it sound like you’re writing the caption yourself, not describing someone else.
- Reflect your MBTI’s personality traits naturally in tone and word choice:
    - ENFP → spontaneous, expressive, energetic, curious.
    - INFP → emotional, sincere, imaginative, introspective.
    - INFJ → calm, insightful, meaningful, empathetic.
    - INTJ → focused, analytical, composed, self-assured.
    - ISTJ → responsible, organized, practical, dependable.
    - ISFP → gentle, aesthetic, peaceful, emotionally aware.
    - ENTP → witty, confident, clever, playful.
    - ENTJ → ambitious, decisive, visionary, self-driven.
    - ESFP → lively, cheerful, warm, enjoying the moment.
    - etc.
- The writing should feel like a real Instagram caption —
    short (1–3 sentences), natural, and personal, as if you just posted it from your phone.
- Do not include hashtags, emojis, or formal expressions.
- Avoid diary-style writing or long reflections — keep it conversational and genuine.
- Focus on how *you feel in the photo*, not on describing the photo itself.
"""
        ).strip()


@router.post("/caption/generate", response_model=CaptionResponse)
async def generate_caption(req: CaptionRequest):
    try:
        client = _get_client()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"model_unavailable: {e}")

    # Fetch image bytes
    img_bytes, img_mime = await _fetch_image_bytes(req.image)

    prompt = _build_caption_prompt(req.personality, req.tone)

    try:
        parts = [
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=img_bytes, mime_type=img_mime or "image/jpeg"),
        ]
        # Build generation config aligned with the notebook
        gen_cfg = types.GenerateContentConfig(
            response_modalities=[types.Modality.TEXT],
            candidate_count=1,
            temperature=CAPTION_TEMPERATURE,
            top_p=CAPTION_TOP_P,
        )
        # Only set max_output_tokens if provided via env
        if CAPTION_MAX_TOKENS:
            gen_cfg.max_output_tokens = CAPTION_MAX_TOKENS

        resp = client.models.generate_content(
            model=GEMINI_TEXT_MODEL,
            contents=parts,
            config=gen_cfg,
        )
        # Prefer resp.text if available, else extract from candidates
        caption = (getattr(resp, "text", "") or "").strip()
        if not caption:
            buf = []
            for c in getattr(resp, "candidates", []) or []:
                content = getattr(c, "content", None)
                if not content:
                    continue
                for p in getattr(content, "parts", []) or []:
                    t = getattr(p, "text", "")
                    if t:
                        buf.append(t)
            caption = "\n".join(buf).strip()
        if not caption:
            raise RuntimeError("empty_caption")
        # Post-process: remove leading labels if any
        lowers = caption.lower()
        if lowers.startswith("output") or lowers.startswith("caption"):
            idx = caption.find("=")
            if idx != -1:
                caption = caption[idx+1:].strip().strip('"')
        return CaptionResponse(ok=True, caption=caption)
    except HTTPException:
        raise
    except Exception as e:
        log.error("/caption/generate failed: %s", e)
        raise HTTPException(status_code=500, detail={"error": "caption_failed", "message": str(e)})
