from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import httpx
from typing import Optional

from .oauth_instagram import (
    GRAPH as IG_GRAPH,
    _require_login,
    _get_persona_token,
    _get_persona_instagram_mapping,
)

router = APIRouter(prefix="/api/instagram", tags=["instagram"])


class ReplyBody(BaseModel):
    persona_num: int = Field(..., ge=0)
    comment_id: str = Field(..., min_length=5)
    message: str = Field(..., min_length=1, max_length=500)


@router.post("/comments/reply")
async def reply_to_comment(request: Request, body: ReplyBody):
    """Reply to a specific Instagram comment using Graph API.

    Requires the persona to be OAuth-linked. Uses the persona's long-lived token.
    """
    uid = _require_login(request)
    mapping = await _get_persona_instagram_mapping(int(uid), int(body.persona_num))
    if not mapping or not mapping.get("ig_user_id"):
        raise HTTPException(status_code=400, detail="persona_not_linked")
    token = await _get_persona_token(int(uid), int(body.persona_num))
    if not token:
        raise HTTPException(status_code=401, detail="persona_oauth_required")

    # Graph API endpoint: POST /{comment-id}/replies with message
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{IG_GRAPH}/{body.comment_id}/replies",
                data={
                    "message": body.message,
                    "access_token": token,
                },
            )
        if r.status_code != 200:
            # Try to bubble up known auth errors
            try:
                err = (r.json() or {}).get("error") or {}
                code = err.get("code")
                if code == 190:
                    raise HTTPException(status_code=401, detail="persona_oauth_required")
            except HTTPException:
                raise
            except Exception:
                pass
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json() or {}
        # Typical response: {"id": "<new_comment_id>"}
        return {"ok": True, "result": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"reply_failed:{e}")
