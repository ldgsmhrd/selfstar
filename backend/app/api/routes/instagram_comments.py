from __future__ import annotations
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
import httpx

# 내부 OAuth/연동 유틸 재사용
from .oauth_instagram import (
    GRAPH as IG_GRAPH,
    _require_login,               # 세션에서 user_id 확인
    _get_persona_token,           # 페르소나별 long-lived user token 조회
    _get_persona_instagram_mapping,  # ss_persona에 저장된 IG 매핑(ig_user_id/fb_page_id)
)
from app.api.models.persona import get_user_personas as _get_user_personas
from app.core.s3 import s3_enabled, presign_get_url


router = APIRouter(prefix="/instagram", tags=["instagram"])


async def _fetch_recent_media_and_comments(
    client: httpx.AsyncClient,
    ig_user_id: str,
    access_token: str,
    media_limit: int = 5,
    comments_limit: int = 10,
) -> List[Dict[str, Any]]:
    """지정 IG 사용자에 대한 최근 미디어와 각 미디어의 최신 댓글 수집.

    반환 items 요소:
    {
      "media_id", "caption", "permalink", "media_type", "media_url", "thumbnail_url", "timestamp",
      "comments": [ { "id", "text", "username", "timestamp", "like_count" } ]
    }
    """
    # 1) 최근 미디어 조회
    media_items: List[Dict[str, Any]] = []
    r = await client.get(
        f"{IG_GRAPH}/{ig_user_id}/media",
        params={
            "access_token": access_token,
            "fields": "id,caption,permalink,media_type,media_url,thumbnail_url,timestamp",
            "limit": max(1, int(media_limit)),
        },
    )
    if r.status_code != 200:
        # 미디어 접근 불가 시 빈 배열
        return []
    data = (r.json() or {}).get("data") or []

    for m in data:
        mid = m.get("id")
        if not mid:
            continue
        item = {
            "media_id": mid,
            "caption": m.get("caption"),
            "permalink": m.get("permalink"),
            "media_type": m.get("media_type"),
            "media_url": m.get("media_url"),
            "thumbnail_url": m.get("thumbnail_url"),
            "timestamp": m.get("timestamp"),
            "comments": [],
        }
        # 2) 각 미디어의 댓글 조회
        cr = await client.get(
            f"{IG_GRAPH}/{mid}/comments",
            params={
                "access_token": access_token,
                # username/text/timestamp/like_count 정도만 사용 (일반 코멘터의 프로필 이미지/ID는 제공되지 않음)
                "fields": "id,text,username,timestamp,like_count",
                "limit": max(1, int(comments_limit)),
            },
        )
        comments: List[Dict[str, Any]] = []
        if cr.status_code == 200:
            comments = (cr.json() or {}).get("data") or []
        # 정규화해서 담기
        item["comments"] = [
            {
                "id": c.get("id"),
                "text": c.get("text"),
                "username": c.get("username"),
                "timestamp": c.get("timestamp"),
                "like_count": c.get("like_count"),
            }
            for c in comments
            if c.get("id")
        ]
        media_items.append(item)
    return media_items


# ===== Instagram posts endpoints for MyPage =====
@router.get("/posts")
async def list_posts(request: Request, persona_num: Optional[int] = None, limit: int = 18):
    """Return recent Instagram posts for the given persona.

    This is a lightweight passthrough to Meta Graph; results are not persisted.
    """
    uid = _require_login(request)
    if persona_num is None:
        raise HTTPException(status_code=400, detail="persona_num_required")

    mapping = await _get_persona_instagram_mapping(int(uid), int(persona_num))
    if not mapping or not mapping.get("ig_user_id"):
        # Not linked yet
        return {"ok": True, "items": []}
    token = await _get_persona_token(int(uid), int(persona_num))
    if not token:
        # Persona OAuth not completed
        raise HTTPException(status_code=401, detail="persona_oauth_required")

    items: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{IG_GRAPH}/{mapping['ig_user_id']}/media",
                params={
                    "access_token": token,
                    "fields": "id,media_type,media_url,thumbnail_url,permalink,timestamp,caption",
                    "limit": max(1, int(limit)),
                },
            )
        if r.status_code != 200:
            # surface as HTTP error to UI
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = (r.json() or {}).get("data") or []
        for m in data:
            if not m.get("id"):
                continue
            items.append(
                {
                    "id": m.get("id"),
                    "media_type": m.get("media_type"),
                    "media_url": m.get("media_url"),
                    "thumbnail_url": m.get("thumbnail_url"),
                    "permalink": m.get("permalink"),
                    "timestamp": m.get("timestamp"),
                    # counts are optional; default to 0 for UI
                    "like_count": 0,
                    "comments_count": 0,
                }
            )
        return {"ok": True, "items": items}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"posts_failed:{e}")


@router.post("/posts/sync")
async def sync_posts(request: Request, persona_num: Optional[int] = None, limit: int = 18, days: Optional[int] = None):
    """Trigger a refresh of posts.

    For now, this just hits the Graph and returns count; persistence can be added later.
    """
    # Reuse list_posts logic
    res = await list_posts(request, persona_num=persona_num, limit=limit)
    try:
        count = len(res.get("items") or [])  # type: ignore
    except Exception:
        count = 0
    return {"ok": True, "synced": count}


@router.get("/comments/overview")
async def comments_overview(
    request: Request,
    media_limit: int = 5,
    comments_limit: int = 10,
):
    """현재 로그인 사용자의 '연동된' 페르소나별 최근 댓글 개요를 반환.

    - 각 페르소나에 대해 최근 N개의 미디어와 각 미디어의 최근 M개의 댓글을 포함
    - 토큰 또는 매핑이 없는 페르소나는 생략
    """
    user_id = _require_login(request)

    # 사용자 페르소나 조회
    personas = await _get_user_personas(int(user_id))
    if not personas:
        return {"ok": True, "personas": []}

    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        for p in personas:
            num = p.get("user_persona_num")
            if num is None:
                continue
            # IG 매핑/토큰 검사
            mapping = await _get_persona_instagram_mapping(int(user_id), int(num))
            if not mapping or not mapping.get("ig_user_id"):
                continue
            token = await _get_persona_token(int(user_id), int(num))
            if not token:
                continue

            media = await _fetch_recent_media_and_comments(
                client,
                mapping["ig_user_id"],
                token,
                media_limit=media_limit,
                comments_limit=comments_limit,
            )

            # 표시용 이름/이미지
            params = p.get("persona_parameters") or {}
            disp_name = params.get("name") or f"프로필 {num}"
            persona_img = p.get("persona_img")
            # Normalize persona_img for browser use: presign S3 keys
            try:
                if persona_img and not str(persona_img).lower().startswith("http") and not str(persona_img).startswith("data:") and not str(persona_img).startswith("/"):
                    if s3_enabled():
                        persona_img = presign_get_url(str(persona_img))
            except Exception:
                pass

            results.append(
                {
                    "persona_num": num,
                    "persona_name": disp_name,
                    "persona_img": persona_img,
                    "ig_user_id": mapping.get("ig_user_id"),
                    "ig_username": mapping.get("ig_username"),
                    "items": media,
                }
            )

    return {"ok": True, "personas": results}
