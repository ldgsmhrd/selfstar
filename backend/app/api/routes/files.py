from __future__ import annotations
import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

# 파트: 파일/URL 유틸리티 — 공개 URL 보장
router = APIRouter(prefix="/files", tags=["files"]) 


class EnsurePublicBody(BaseModel):
    # image: http(s) URL | /files/상대경로 | data:image/*;base64,...
    image: str
    persona_num: Optional[int] = None  # optional, for auditing


@router.post("/ensure_public")
async def ensure_public(request: Request, body: EnsurePublicBody):
    """공개 URL 보장 엔드포인트

    - http(s) URL: 그대로 반환(pass-through)
    - /files/...: BACKEND_URL 기반 절대 URL로 승격
    - data:image/*;base64,...: 파일 저장(FILES_ROOT/yyyyMMdd/uuid.ext) 후 절대 URL 반환

    참고: Instagram Graph API 사용 시 BACKEND_URL은 외부에서 접근 가능한 HTTPS여야 함(ngrok 등).
    """
    img = (body.image or "").strip()
    if not img:
        raise HTTPException(status_code=400, detail="image_required")

    # Already a full URL
    if img.lower().startswith("http://") or img.lower().startswith("https://"):
        return {"ok": True, "url": img}

    backend_url = (os.getenv("BACKEND_URL") or "http://localhost:8000").rstrip("/")

    # Relative served file
    if img.startswith("/files/"):
        return {"ok": True, "url": f"{backend_url}{img}", "path": img.removeprefix("/files/")}

    # data URI -> persist
    if img.startswith("data:"):
        import base64, uuid, datetime, re
        files_root = os.getenv("FILES_ROOT") or os.path.join(os.path.dirname(__file__), "..", "..", "storage")
        m = re.match(r"^data([\w\/:;+\-=]*);base64,", img)
        mime = (m.group(1).split(":",1)[1] if m and ":" in m.group(1) else "image/png") if m else "image/png"
        ext = {
            "image/png": "png",
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/webp": "webp",
        }.get(mime, "png")
        date_dir = datetime.datetime.utcnow().strftime("%Y%m%d")
        abs_dir = os.path.abspath(os.path.join(files_root, date_dir))
        os.makedirs(abs_dir, exist_ok=True)
        fname = f"{uuid.uuid4().hex[:12]}.{ext}"
        abs_path = os.path.join(abs_dir, fname)
        rel_path = f"{date_dir}/{fname}"
        b64 = img.split(",", 1)[1]
        with open(abs_path, "wb") as f:
            f.write(base64.b64decode(b64))
        return {"ok": True, "url": f"{backend_url}/files/{rel_path}", "path": rel_path}

    raise HTTPException(status_code=400, detail="unsupported_image_format")
