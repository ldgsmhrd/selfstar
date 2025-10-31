from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
import os
import json
import httpx
import aiomysql

from app.api.core.mysql import get_mysql_pool

router = APIRouter(prefix="/api/instagram", tags=["instagram"])


class CaptionDraftBody(BaseModel):
    persona_num: int = Field(..., ge=0)
    image: str = Field(..., min_length=10, description="Preview image (data URI or URL)")
    tone: Optional[str] = Field(None, description="Optional tone, e.g., insta|editorial|playful")


def _require_login(request: Request) -> int:
    uid = request.session.get("user_id") if hasattr(request, "session") else None
    if not uid:
        # 개발 모드에서만 허용: DEV_ALLOW_DEBUG_USER=1이면 X-Debug-User-Id 헤더로 대체
        try:
            if os.getenv("DEV_ALLOW_DEBUG_USER", "0").lower() in ("1", "true", "yes"):
                dbg = request.headers.get("X-Debug-User-Id")
                if dbg and dbg.isdigit():
                    uid = int(dbg)
        except Exception:
            pass
    if not uid:
        raise HTTPException(status_code=401, detail="not_logged_in")
    return int(uid)


@router.post("/caption/draft")
async def caption_draft(request: Request, body: CaptionDraftBody):
    """Generate an Instagram caption draft using persona personality and preview image.

    Delegates to the AI service /caption/generate.
    """
    uid = _require_login(request)

    # Load persona parameters to extract personality
    personality: str = ""  # MBTI 타입(ex: ISTJ)
    try:
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT persona_parameters
                    FROM ss_persona
                    WHERE user_id=%s AND user_persona_num=%s
                    LIMIT 1
                    """,
                    (int(uid), int(body.persona_num)),
                )
                row = await cur.fetchone()
                if row:
                    pp_raw = row.get("persona_parameters")
                    try:
                        pp = json.loads(pp_raw) if isinstance(pp_raw, str) else (pp_raw or {})
                    except Exception:
                        pp = {}
                    # 우선순위: MBTI 전용 키
                    for key in ("mbti", "MBTI", "mbti_type", "personality_mbti"):
                        val = pp.get(key) if isinstance(pp, dict) else None
                        if isinstance(val, str) and val.strip():
                            personality = val.strip()
                            break
                    # 보조: 기존 personality/tone/style/voice 중 MBTI 패턴(예: INFP)
                    if not personality and isinstance(pp, dict):
                        import re as _re
                        for key in ("personality", "tone", "style", "voice"):
                            val = pp.get(key)
                            if isinstance(val, str) and val.strip():
                                s = val.strip().upper()
                                if _re.match(r"^[E|I][N|S][F|T][P|J]$", s):
                                    personality = s
                                    break
                    if not personality:
                        igp = (pp.get("instagram") or {}) if isinstance(pp, dict) else {}
                        val = igp.get("personality") or igp.get("tone")
                        if isinstance(val, str) and val.strip():
                            personality = val.strip()
    except Exception:
        # Non-fatal: continue with empty personality
        pass

    # Delegate to AI service
    ai_url = (os.getenv("AI_SERVICE_URL") or "http://ai:8600").rstrip("/")
    payload = {
        "image": body.image,
        "personality": personality or "",
        "tone": (body.tone or "").strip() or None,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{ai_url}/caption/generate", json=payload)
        if r.status_code != 200:
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise HTTPException(status_code=502, detail={"ai_failed": True, "status": r.status_code, "body": detail})
        data = r.json() or {}
        cap = (data.get("caption") or "").strip()
        if not cap:
            raise HTTPException(status_code=502, detail="ai_empty_caption")
        return {"ok": True, "caption": cap}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ai_delegate_error: {e}")
