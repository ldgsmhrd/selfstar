from __future__ import annotations
import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.core.s3 import s3_enabled, put_data_uri, presign_get_url

# 파트: 파일/URL 유틸리티 — 공개 URL 보장(S3 우선)
router = APIRouter(prefix="/files", tags=["files"]) 


class EnsurePublicBody(BaseModel):
    # image: http(s) URL | /files/상대경로 | data:image/*;base64,...
    image: str
    persona_num: Optional[int] = None  # 선택: 키 경로 구성에 사용(chat/{user_id}/{persona_num})


@router.post("/ensure_public")
async def ensure_public(request: Request, body: EnsurePublicBody):
    """공개 URL 보장 엔드포인트

    - http(s) URL: 그대로 반환(pass-through)
    - /files/...: BACKEND_URL 기반 절대 URL로 승격(이전 호환)
    - data:image/*;base64,...: S3에 업로드 후 프리사인 URL 반환

    참고: 버킷은 비공개여도 됩니다. 프리사인 URL을 게시/업로드에 사용하세요.
    """
    img = (body.image or "").strip()
    if not img:
        raise HTTPException(status_code=400, detail="image_required")

    # 이미 절대 URL인 경우는 그대로 사용
    if img.lower().startswith("http://") or img.lower().startswith("https://"):
        return {"ok": True, "url": img}

    backend_url = (os.getenv("BACKEND_URL") or "http://localhost:8000").rstrip("/")

    # 과거 /files 경로 호환: 절대 URL로만 승격
    if img.startswith("/files/"):
        return {"ok": True, "url": f"{backend_url}{img}", "path": img.removeprefix("/files/")}

    # data URI → S3 업로드
    if img.startswith("data:"):
        if not s3_enabled():
            raise HTTPException(status_code=400, detail="s3_not_configured")
        user_id = request.session.get("user_id") if hasattr(request, "session") else None
        if not user_id and os.getenv("DEV_ALLOW_DEBUG_USER", "0") in ("1", "true", "yes"):
            try:
                debug_uid = request.headers.get("X-Debug-User-Id")
                if debug_uid and debug_uid.isdigit():
                    user_id = int(debug_uid)
            except Exception:
                pass
        if not user_id:
            raise HTTPException(status_code=401, detail="not_authenticated")

        # 경로: chat/{user_id}/{persona_num} 또는 uploads/{user_id}
        key_prefix = (
            f"chat/{int(user_id)}/{int(body.persona_num)}" if body.persona_num is not None else f"uploads/{int(user_id)}"
        )
        key = put_data_uri(
            img,
            model=None,
            key_prefix=key_prefix,
            base_prefix="",
            include_model=False,
            include_date=False,
        )
        url = presign_get_url(key)
        return {"ok": True, "url": url, "key": key}

    raise HTTPException(status_code=400, detail="unsupported_image_format")
