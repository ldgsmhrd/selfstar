from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import os
from urllib.parse import urlparse, urlunparse
import httpx
import logging
import aiomysql
from app.api.core.mysql import get_mysql_pool

# 파트: 채팅/이미지 생성 API
router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger("chat")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    # 페르소나 번호(선택)
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
    # 전송: POST {ai}/chat
    # payload: { persona_img: str|None, messages: [{role,content}] }
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
    """간단한 사용 가이드(브라우저 GET 보호)"""
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
    # 이미지 생성 요청 바디
    persona_num: int = Field(..., ge=1)
    user_text: str = Field(..., min_length=1)
    ls_session_id: Optional[str] = None
    # style_img: data URI 또는 URL(선택) — 의상 유지 참고 이미지
    style_img: Optional[str] = None


@router.post("/image")
async def image(req: ChatImageRequest, request: Request):
    user_id = request.session.get("user_id") if hasattr(request, "session") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="not_logged_in")

    # 1) 페르소나 이미지/파라미터 조회
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

    # 2) AI에서 접근 가능한 URL로 정규화
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
    # 전송: POST {ai}/chat/image
    # payload: { user_text, persona_img, persona(JSON str), ls_session_id?, style_img? }
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
    ai_json = r.json()

    # 3) 이미지 파일 저장(+ DB 기록)
    stored = None
    try:
        img_str = ai_json.get("image") if isinstance(ai_json, dict) else None
        if isinstance(img_str, str) and img_str.startswith("data:"):
            import base64, uuid, datetime, re
            files_root = os.getenv("FILES_ROOT") or os.path.join(os.path.dirname(__file__), "..", "..", "storage")
            # 확장자 결정
            m = re.match(r"^data:([\w\-/]+);base64,", img_str)
            mime = m.group(1) if m else "image/png"
            ext = {
                "image/png": "png",
                "image/jpeg": "jpg",
                "image/jpg": "jpg",
                "image/webp": "webp",
            }.get(mime, "png")
            # yyyyMMdd 디렉터리 생성
            date_dir = datetime.datetime.utcnow().strftime("%Y%m%d")
            abs_dir = os.path.abspath(os.path.join(files_root, date_dir))
            os.makedirs(abs_dir, exist_ok=True)
            fname = f"{uuid.uuid4().hex[:12]}.{ext}"
            abs_path = os.path.join(abs_dir, fname)
            rel_path = f"{date_dir}/{fname}"
            # base64 -> 파일 쓰기
            b64 = img_str.split(",", 1)[1]
            with open(abs_path, "wb") as f:
                f.write(base64.b64decode(b64))

            # DB 기록: ss_img(user_id, img_img, ss_persona_id)
            ss_persona_id: Optional[int] = None
            try:
                pool = await get_mysql_pool()
                async with pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cur:
                        await cur.execute(
                            """
                            SELECT id
                            FROM ss_persona
                            WHERE user_id=%s AND user_persona_num=%s
                            LIMIT 1
                            """,
                            (int(user_id), int(req.persona_num)),
                        )
                        prow = await cur.fetchone()
                        if prow and prow.get("id") is not None:
                            ss_persona_id = int(prow["id"])
                async with pool.acquire() as conn2:
                    async with conn2.cursor() as cur2:
                        await cur2.execute(
                            """
                            INSERT INTO ss_img (user_id, img_img, ss_persona_id)
                            VALUES (%s, %s, %s)
                            """,
                            (int(user_id), rel_path, ss_persona_id),
                        )
                        try:
                            await conn2.commit()
                        except Exception:
                            pass
                        try:
                            ss_img_id = cur2.lastrowid
                        except Exception:
                            ss_img_id = None
            except Exception as _e:
                log.warning("ss_img insert failed: %s", _e)
                ss_img_id = None

            stored = {
                "path": rel_path,
                "url": f"/files/{rel_path}",
                "id": ss_img_id,
            }
    except Exception as e:
        log.warning("image store failed: %s", e)

    if isinstance(ai_json, dict):
        if stored:
            ai_json["stored"] = stored
        return ai_json
    return {"ok": True, "image": ai_json, "stored": stored}


@router.get("/image")
async def image_usage():
    """간단한 사용 가이드(브라우저 GET 보호) — 실제 엔드포인트는 POST /chat/image"""
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
    """파트: 세션 시작 — LangSmith 세션 ID 발급"""
    import uuid, time
    sid = str(uuid.uuid4())
    try:
        if hasattr(request, "session"):
            request.session["ls_session_id"] = sid
    except Exception:
        pass
    # LangSmith 가시화 하트비트(선택)
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
    """파트: 세션 종료"""
    sid = None
    try:
        sid = body.get("ls_session_id") if isinstance(body, dict) else None
        if not sid and hasattr(request, "session"):
            sid = request.session.pop("ls_session_id", None)
    except Exception:
        pass
    return {"ok": True, "ls_session_id": sid}
