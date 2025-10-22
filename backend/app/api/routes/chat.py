from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import os
from urllib.parse import urlparse, urlunparse
import httpx
import logging
import aiomysql
from app.api.core.mysql import get_mysql_pool

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger("chat")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    # Allow any positive persona_num; do not cap at 4 to support growing persona lists
    persona_num: Optional[int] = Field(None, ge=1)
    messages: List[ChatMessage] = Field(default_factory=list)


@router.post("/send")
async def send(req: ChatRequest, request: Request):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages_required")
    user_id = request.session.get("user_id") if hasattr(request, "session") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="not_logged_in")

    persona_img: Optional[str] = None
    if req.persona_num is not None:
        try:
            pool = await get_mysql_pool()
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(
                        """
                        SELECT persona_img
                        FROM ss_persona
                        WHERE user_id = %s AND user_persona_num = %s
                        LIMIT 1
                        """,
                        (int(user_id), int(req.persona_num)),
                    )
                    row = await cur.fetchone()
                    if row and row.get("persona_img"):
                        persona_img = row["persona_img"]
        except Exception as e:
            log.warning("persona lookup failed: %s", e)

    ai_url = (os.getenv("AI_SERVICE_URL") or "http://localhost:8600").rstrip("/")
    payload = {"persona_img": persona_img, "messages": [m.model_dump() for m in req.messages]}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{ai_url}/chat", json=payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ai_delegate_error: {e}")

    if r.status_code != 200:
        detail = None
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise HTTPException(status_code=502, detail={"ai_failed": True, "status": r.status_code, "body": detail})
    return r.json()


@router.get("/send")
async def send_usage():
    """
    Convenience endpoint so a direct GET to /chat/send in the browser doesn't 405.
    Explains how to use the POST variant expected by the chat UI.
    """
    return {
        "ok": True,
        "method": "POST only for chat",
        "usage": {
            "url": "/chat/send",
            "headers": {"Content-Type": "application/json"},
            "body": {
                "persona_num": 1,
                "messages": [{"role": "user", "content": "안녕"}],
            },
        },
        "note": "이 엔드포인트는 세션 로그인이 필요합니다. 프론트엔드에서 버튼을 눌러 호출하세요.",
    }


class ChatImageRequest(BaseModel):
    # Allow any positive persona_num; previously capped at 4 which blocked new personas (e.g., 5+)
    persona_num: int = Field(..., ge=1)
    user_text: str = Field(..., min_length=1)
    ls_session_id: Optional[str] = None
    # Optional style reference image (data URI or URL). Used to transfer clothing/outfit.
    style_img: Optional[str] = None


@router.post("/image")
async def image(req: ChatImageRequest, request: Request):
    user_id = request.session.get("user_id") if hasattr(request, "session") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="not_logged_in")

    # Lookup persona image and parameters for persona_num
    persona_img: Optional[str] = None
    persona_params_json: Optional[str] = None
    try:
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT persona_img, persona_parameters
                    FROM ss_persona
                    WHERE user_id = %s AND user_persona_num = %s
                    LIMIT 1
                    """,
                    (int(user_id), int(req.persona_num)),
                )
                row = await cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="persona_not_found")
                persona_img = row.get("persona_img")
                # persona_parameters는 JSON 문자열 또는 dict일 수 있음 → 문자열로 보냄
                pp = row.get("persona_parameters")
                if isinstance(pp, (dict, list)):
                    import json as _json
                    persona_params_json = _json.dumps(pp, ensure_ascii=False)
                else:
                    persona_params_json = pp
    except HTTPException:
        raise
    except Exception as e:
        log.exception("persona lookup failed: %s", e)
        raise HTTPException(status_code=500, detail="persona_lookup_failed")

    if not persona_img:
        raise HTTPException(status_code=400, detail="persona_img_missing")

    # [중요] AI 컨테이너에서 접근 가능한 절대 URL로 정규화
    # - data: URI면 그대로 사용
    # - /media/... 같은 상대경로면 내부용 백엔드 URL로 프리픽스
    # - http://localhost:8000, http://127.0.0.1:8000 형태는 컨테이너 내부에서 접근 불가 → backend:8000 으로 교체
    def _normalize_persona_img(raw: str) -> str:
        try:
            if raw.startswith("data:"):
                return raw
            if raw.startswith("/"):
                base = (os.getenv("BACKEND_INTERNAL_URL") or "http://backend:8000").rstrip("/")
                return f"{base}{raw}"
            if raw.startswith("http://localhost") or raw.startswith("http://127.0.0.1"):
                # 호스트만 backend로 교체
                p = urlparse(raw)
                repl = p._replace(netloc="backend:8000")
                return urlunparse(repl)
            return raw
        except Exception:
            return raw

    persona_img_norm = _normalize_persona_img(persona_img)
    if persona_img_norm != persona_img:
        log.info("persona_img normalized: %s -> %s", persona_img, persona_img_norm)

    ai_url = (os.getenv("AI_SERVICE_URL") or "http://localhost:8600").rstrip("/")
    payload = {
        "user_text": req.user_text,
        "persona_img": persona_img_norm,
        "persona": persona_params_json or "",
        "ls_session_id": req.ls_session_id,
        "style_img": req.style_img,
    }
    log.info("/chat/image forwarding -> user_id=%s persona_num=%s", user_id, req.persona_num)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ai_url}/chat/image", json=payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ai_delegate_error: {e}")

    if r.status_code != 200:
        # return AI body for easier debugging in frontend
        detail = None
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise HTTPException(status_code=502, detail={"ai_failed": True, "status": r.status_code, "body": detail})
    return r.json()


@router.get("/image")
async def image_usage():
    """
    Prevent 405 by providing a usage helper for browser GET requests.
    The actual endpoint is POST /chat/image.
    """
    return {
        "ok": True,
        "method": "POST only for image generation",
        "usage": {
            "url": "/chat/image",
            "headers": {"Content-Type": "application/json"},
            "body": {"persona_num": 1, "user_text": "패션쇼 무드의 블랙 드레스", "ls_session_id": "<optional>", "style_img": "<optional data-uri or url>"},
        },
        "note": "세션 로그인이 필요합니다. 프론트엔드에서 '이미지 생성' 버튼을 눌러 호출하세요.",
    }


@router.post("/session/start")
async def start_chat_session(request: Request):
    """채팅 진입 시 LangSmith 세션을 구분하기 위한 임시 세션 ID 발급."""
    import uuid, time
    sid = str(uuid.uuid4())
    try:
        if hasattr(request, "session"):
            request.session["ls_session_id"] = sid
    except Exception:
        pass
    # Fire-and-forget heartbeat to AI so LangSmith project appears immediately (if enabled)
    try:
        ai_url = (os.getenv("AI_SERVICE_URL") or "http://ai:8600").rstrip("/")
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{ai_url}/chat/trace/heartbeat", json={"ls_session_id": sid})
    except Exception:
        # Non-fatal: just ignore if AI is not reachable
        pass
    return {"ok": True, "ls_session_id": sid, "started_at": int(time.time())}


@router.post("/session/end")
async def end_chat_session(request: Request, body: dict = Body(default={})): 
    """채팅 종료 시 세션 정리."""
    sid = None
    try:
        sid = body.get("ls_session_id") if isinstance(body, dict) else None
        if not sid and hasattr(request, "session"):
            sid = request.session.pop("ls_session_id", None)
    except Exception:
        pass
    return {"ok": True, "ls_session_id": sid}
