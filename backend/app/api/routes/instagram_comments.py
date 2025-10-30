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
from app.api.core.mysql import get_mysql_pool
import aiomysql
from datetime import datetime


router = APIRouter(prefix="/api/instagram", tags=["instagram"])


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
    """Return recently stored posts for persona from DB.

    Use /api/instagram/posts/sync to refresh cache from Graph.
    """
    uid = _require_login(request)
    if persona_num is None:
        raise HTTPException(status_code=400, detail="persona_num_required")

    items: List[Dict[str, Any]] = []
    try:
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                rows = []
                try:
                    await cur.execute(
                        """
                        SELECT media_id, media_type, media_product_type, media_url, thumbnail_url,
                               permalink, caption, posted_at, like_count, comments_count
                        FROM ss_instagram_post
                        WHERE user_id=%s AND user_persona_num=%s
                        ORDER BY (posted_at IS NULL) ASC, posted_at DESC, updated_at DESC
                        LIMIT %s
                        """,
                        (int(uid), int(persona_num), int(limit)),
                    )
                    rows = await cur.fetchall() or []
                except Exception as _e:
                    # 테이블 미존재 또는 권한 문제 시 빈 배열 반환(프로덕션 안전)
                    rows = []
        for r in rows:
            ts = r.get("posted_at")
            if ts:
                try:
                    timestamp = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
                except Exception:
                    timestamp = None
            else:
                timestamp = None
            items.append(
                {
                    "id": r.get("media_id"),
                    "media_type": r.get("media_type"),
                    "media_url": r.get("media_url"),
                    "thumbnail_url": r.get("thumbnail_url"),
                    "permalink": r.get("permalink"),
                    "caption": r.get("caption"),
                    "timestamp": timestamp,
                    "like_count": r.get("like_count") or 0,
                    "comments_count": r.get("comments_count") or 0,
                }
            )
        return {"ok": True, "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"posts_list_failed:{e}")


@router.post("/posts/sync")
async def sync_posts(request: Request, persona_num: Optional[int] = None, limit: int = 18, days: Optional[int] = None):
    """Fetch recent posts from Graph and upsert into DB for this persona."""
    uid = _require_login(request)
    if persona_num is None:
        raise HTTPException(status_code=400, detail="persona_num_required")

    mapping = await _get_persona_instagram_mapping(int(uid), int(persona_num))
    if not mapping or not mapping.get("ig_user_id"):
        return {"ok": True, "synced": 0}
    token = await _get_persona_token(int(uid), int(persona_num))
    if not token:
        raise HTTPException(status_code=401, detail="persona_oauth_required")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{IG_GRAPH}/{mapping['ig_user_id']}/media",
                params={
                    "access_token": token,
                    "fields": "id,media_type,media_product_type,media_url,thumbnail_url,permalink,timestamp,caption,like_count,comments_count",
                    "limit": max(1, int(limit)),
                },
            )
        if r.status_code != 200:
            try:
                body = r.json()
                err = (body or {}).get("error") or {}
                if err.get("code") == 190:
                    raise HTTPException(status_code=401, detail="persona_oauth_required")
            except HTTPException:
                raise
            except Exception:
                pass
            if r.status_code == 404:
                return {"ok": True, "synced": 0}
            raise HTTPException(status_code=r.status_code, detail=r.text)

        data = (r.json() or {}).get("data") or []
        if not data:
            return {"ok": True, "synced": 0}

        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                upcnt = 0
                for m in data:
                    mid = m.get("id")
                    if not mid:
                        continue
                    media_type = m.get("media_type")
                    product_type = m.get("media_product_type")
                    media_url = m.get("media_url")
                    thumbnail_url = m.get("thumbnail_url")
                    permalink = m.get("permalink")
                    caption = m.get("caption")
                    timestamp = m.get("timestamp")
                    like_count = int(m.get("like_count") or 0)
                    comments_count = int(m.get("comments_count") or 0)
                    # Normalize timestamp to MySQL DATETIME string
                    posted_at = None
                    if isinstance(timestamp, str):
                        # IG returns ISO 8601; MySQL accepts 'YYYY-MM-DD HH:MM:SS'
                        try:
                            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                            posted_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            posted_at = None
                    try:
                        await cur.execute(
                            """
                            INSERT INTO ss_instagram_post (
                              media_id, user_id, user_persona_num, ig_user_id,
                              media_type, media_product_type, media_url, thumbnail_url,
                              permalink, caption, posted_at, like_count, comments_count
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON DUPLICATE KEY UPDATE
                              media_type=VALUES(media_type),
                              media_product_type=VALUES(media_product_type),
                              media_url=VALUES(media_url),
                              thumbnail_url=VALUES(thumbnail_url),
                              permalink=VALUES(permalink),
                              caption=VALUES(caption),
                              posted_at=VALUES(posted_at),
                              like_count=GREATEST(VALUES(like_count), like_count),
                              comments_count=GREATEST(VALUES(comments_count), comments_count),
                              updated_at=CURRENT_TIMESTAMP
                            """,
                            (
                                str(mid), int(uid), int(persona_num), str(mapping["ig_user_id"]),
                                media_type, product_type, media_url, thumbnail_url,
                                permalink, caption, posted_at, like_count, comments_count,
                            ),
                        )
                        upcnt += 1
                    except Exception:
                        # Continue on individual failure
                        pass
                try:
                    await conn.commit()
                except Exception:
                    pass
        return {"ok": True, "synced": upcnt}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"posts_sync_failed:{e}")


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
            # Normalize persona_img for browser use: presign S3 keys and fix legacy localhost URLs
            try:
                s = str(persona_img) if persona_img is not None else ""
                if s and not s.lower().startswith("http") and not s.startswith("data:") and not s.startswith("/"):
                    if s3_enabled():
                        persona_img = presign_get_url(s)
                elif s.lower().startswith("http://localhost") or s.lower().startswith("http://127.0.0.1"):
                    from urllib.parse import urlparse
                    purl = urlparse(s)
                    path = purl.path or ""
                    if path.startswith("/personas/") or path.startswith("/uploads/"):
                        if s3_enabled():
                            persona_img = presign_get_url(path.lstrip("/"))
                        else:
                            backend_url = (os.getenv("BACKEND_URL") or "http://localhost:8000").rstrip("/")
                            persona_img = f"{backend_url}{path}"
                    elif path.startswith("/media/"):
                        backend_url = (os.getenv("BACKEND_URL") or "http://localhost:8000").rstrip("/")
                        persona_img = f"{backend_url}{path}"
                    else:
                        backend_url = (os.getenv("BACKEND_URL") or "http://localhost:8000").rstrip("/")
                        persona_img = f"{backend_url}{path or '/'}"
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
