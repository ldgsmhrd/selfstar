from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
import httpx
import aiomysql
from app.api.core.mysql import get_mysql_pool

from .oauth_instagram import (
    GRAPH as IG_GRAPH,
    _require_login,
    _get_persona_token,
    _get_persona_instagram_mapping,
)

router = APIRouter(prefix="/instagram", tags=["instagram"])

async def _ensure_instagram_post_table():
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ss_instagram_post (
                  ig_media_id        VARCHAR(64) PRIMARY KEY,
                  user_id            INT           NOT NULL,
                  user_persona_num   INT           NOT NULL,
                  ig_user_id         VARCHAR(64)   NOT NULL,
                  media_type         VARCHAR(32)   NULL,
                  media_product_type VARCHAR(32)   NULL,
                  media_url          TEXT          NULL,
                  thumbnail_url      TEXT          NULL,
                  permalink          TEXT          NULL,
                  caption            TEXT          NULL,
                  timestamp          DATETIME      NULL,
                  like_count         INT           NULL,
                  comments_count     INT           NULL,
                  created_at         TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at         TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                  KEY idx_persona_ts (user_id, user_persona_num, timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
            try:
                await conn.commit()
            except Exception:
                pass


async def _ensure_dashboard_table():
    """Create ss_dashboard if it does not exist. Ignore CREATE privilege errors."""
    try:
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ss_dashboard (
                      user_id INT NOT NULL,
                      user_persona_num INT NOT NULL,
                      ig_user_id VARCHAR(100) NOT NULL,
                      date DATE NOT NULL,
                      followers_count INT DEFAULT 0,
                      total_likes INT DEFAULT 0,
                      profile_views INT DEFAULT 0,
                      reach INT DEFAULT 0,
                      impressions INT DEFAULT 0,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                      UNIQUE KEY uq_dash_day (user_id, user_persona_num, date),
                      KEY idx_dash_ig (ig_user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                try:
                    await conn.commit()
                except Exception:
                    pass
    except Exception:
        # no create privilege or connection error — ignore
        pass


def _iso_date(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


@router.get("/insights/overview")
async def insights_overview(
    request: Request,
    persona_num: int,
    days: int = 30,
):
    """지정 페르소나의 인스타 사용자/미디어 인사이트 요약.

    반환:
    {
      followers_count,
      ig_username,
      series: {
        follows: [{date, value}],
        unfollows: [{date, value}],
        reach: [{date, value}],
        impressions: [{date, value}],
        profile_views: [{date, value}],
      },
      recent_media: [{ id, timestamp, like_count, comments_count, permalink, media_type, media_url }]
    }
    """
    user_id = _require_login(request)
    if days <= 0 or days > 30:
        days = 30

    mapping = await _get_persona_instagram_mapping(int(user_id), int(persona_num))
    if not mapping or not mapping.get("ig_user_id"):
        raise HTTPException(status_code=400, detail="persona_instagram_not_linked")
    token = await _get_persona_token(int(user_id), int(persona_num))
    if not token:
        raise HTTPException(status_code=401, detail="persona_oauth_required")

    ig_user_id = mapping["ig_user_id"]
    since = datetime.now(timezone.utc) - timedelta(days=days)
    until = datetime.now(timezone.utc)

    async with httpx.AsyncClient(timeout=30) as client:
        # 현재 팔로워 수 및 사용자명
        usr = await client.get(
            f"{IG_GRAPH}/{ig_user_id}",
            params={
                "access_token": token,
                "fields": "username,followers_count",
            },
        )
        followers_count = None
        username = None
        if usr.status_code == 200:
            uj = usr.json() or {}
            followers_count = uj.get("followers_count")
            username = uj.get("username")

        # 사용자 인사이트(일별)
        # impressions는 API v22+에서 views로 대체 예정이므로 둘 다 시도
        metrics = "follower_count,follows,unfollows,reach,impressions,profile_views,views"
        ins = await client.get(
            f"{IG_GRAPH}/{ig_user_id}/insights",
            params={
                "metric": metrics,
                "period": "day",
                "since": _iso_date(since),
                "until": _iso_date(until),
                "access_token": token,
            },
        )
        series: Dict[str, List[Dict[str, Any]]] = {
            "follower_count": [],
            "follows": [],
            "unfollows": [],
            "reach": [],
            "impressions": [],
            "profile_views": [],
        }
        if ins.status_code == 200:
            ij = (ins.json() or {}).get("data") or []
            for m in ij:
                name = m.get("name")
                values = m.get("values") or []
                # views가 오면 기존 'impressions'로 매핑해 UI 호환 유지
                if name == "views":
                    name_key = "impressions"
                else:
                    name_key = name
                if name_key in series:
                    out: List[Dict[str, Any]] = []
                    for v in values:
                        t = v.get("end_time") or v.get("time") or v.get("date")
                        # end_time이 ISO timestamp인 경우 날짜만 잘라냄
                        dstr = None
                        if isinstance(t, str) and len(t) >= 10:
                            dstr = t[:10]
                        elif isinstance(t, (int, float)):
                            try:
                                dstr = datetime.fromtimestamp(float(t), tz=timezone.utc).strftime("%Y-%m-%d")
                            except Exception:
                                dstr = None
                        if not dstr:
                            continue
                        out.append({"date": dstr, "value": v.get("value")})
                    series[name_key] = out

        # 최근 미디어(좋아요/댓글 수 포함) + 게시일 기준 좋아요 합계(approx)
        med = await client.get(
            f"{IG_GRAPH}/{ig_user_id}/media",
            params={
                "access_token": token,
                "fields": "id,timestamp,like_count,comments_count,permalink,media_type,media_url,thumbnail_url,caption",
                "limit": 50,
                "since": _iso_date(since),
            },
        )
        recent_media: List[Dict[str, Any]] = []
        approx_likes_by_post_day: Dict[str, int] = {}
        if med.status_code == 200:
            for m in (med.json() or {}).get("data", []):
                # 게시일 기준 좋아요 합계(정확한 증가분이 아닌 보정 지표)
                ts = (m.get("timestamp") or "")[:10]
                try:
                    lc = int(m.get("like_count") or 0)
                except Exception:
                    lc = 0
                if ts:
                    approx_likes_by_post_day[ts] = approx_likes_by_post_day.get(ts, 0) + lc
                recent_media.append(
                    {
                        "id": m.get("id"),
                        "timestamp": m.get("timestamp"),
                        "like_count": m.get("like_count"),
                        "comments_count": m.get("comments_count"),
                        "permalink": m.get("permalink"),
                        "media_type": m.get("media_type"),
                        "media_url": m.get("media_url"),
                        "thumbnail_url": m.get("thumbnail_url"),
                        "caption": m.get("caption"),
                    }
                )

    # approx 시계열 정렬
    approx_sorted: List[Dict[str, Any]] = []
    if 'approx_likes_by_post_day' in locals():
        approx_sorted = [
            {"date": k, "value": v} for k, v in sorted(approx_likes_by_post_day.items(), key=lambda x: x[0])
        ]

    # 오늘(가장 최신) 팔로워 순증가 = follower_count(오늘) - follower_count(어제)
    today_delta_followers: Optional[int] = None
    latest_date_str: Optional[str] = None
    baseline_date_str: Optional[str] = None
    try:
        fc = series.get("follower_count") or []
        # 날짜 기준 오름차순 정렬 보장
        fc_sorted = sorted(
            [x for x in fc if isinstance(x, dict) and x.get("date")],
            key=lambda x: x.get("date")
        )
        if len(fc_sorted) >= 2:
            last = fc_sorted[-1]
            prev = fc_sorted[-2]
            last_val = int(last.get("value") or 0)
            prev_val = int(prev.get("value") or 0)
            today_delta_followers = last_val - prev_val
            latest_date_str = last.get("date")
            baseline_date_str = prev.get("date")
    except Exception:
        pass

    return {
        "ok": True,
        "ig_username": username or mapping.get("ig_username"),
        "followers_count": followers_count,
        "series": {**series, "approx_likes_by_post_day": approx_sorted},
        "today_followers_delta": today_delta_followers,
        "today_followers_date": latest_date_str,
        "today_followers_baseline_date": baseline_date_str,
        "recent_media": recent_media,
    }


# ====== Media (post) insights per item ======

REEL_METRICS = "plays,reach,likes,comments,shares,saves,total_interactions"
FEED_METRICS = "impressions,reach,saved,engagement,video_views"


async def _media_insights(client: httpx.AsyncClient, media_id: str, product_type: str | None, token: str) -> Dict[str, Any]:
    """Fetch insights for a single media. Maps 'views' to 'impressions' when present.

    Note: Reels and Feed have different metric sets; request the set depending on product type.
    """
    pt = (product_type or "").upper()
    metrics = REEL_METRICS if pt in ("REEL", "REELS") else FEED_METRICS
    r = await client.get(f"{IG_GRAPH}/{media_id}/insights", params={"metric": metrics, "access_token": token})
    out: Dict[str, Any] = {}
    if r.status_code == 200:
        try:
            for m in (r.json() or {}).get("data", []):
                name = (m.get("name") or "").lower()
                key = "impressions" if name == "views" else name
                vals = m.get("values") or []
                val = (vals[-1] or {}).get("value") if vals else None
                # Some responses return dicts; normalize to a number when possible
                if isinstance(val, dict):
                    val = val.get("value") or val.get("count") or 0
                out[key] = val
        except Exception:
            pass
    return out


@router.get("/insights/media_overview")
async def media_overview(request: Request, persona_num: int, limit: int = 12, days: int = 30):
    """최근 N개 게시글(피드/릴스)별 인사이트 요약을 반환합니다."""
    user_id = _require_login(request)
    if limit <= 0 or limit > 30:
        limit = 12
    if days <= 0 or days > 30:
        days = 30

    mapping = await _get_persona_instagram_mapping(int(user_id), int(persona_num))
    if not mapping or not mapping.get("ig_user_id"):
        raise HTTPException(status_code=400, detail="persona_instagram_not_linked")
    token = await _get_persona_token(int(user_id), int(persona_num))
    if not token:
        raise HTTPException(status_code=401, detail="persona_oauth_required")

    ig_user_id = str(mapping["ig_user_id"]) 
    since = _iso_date(datetime.now(timezone.utc) - timedelta(days=days))

    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{IG_GRAPH}/{ig_user_id}/media",
            params={
                "access_token": token,
                "fields": "id,timestamp,caption,permalink,media_type,media_product_type,media_url,thumbnail_url,like_count,comments_count",
                "limit": limit,
                "since": since,
            },
        )
        data = []
        if r.status_code == 200:
            data = (r.json() or {}).get("data", [])

        sem = asyncio.Semaphore(5)

        async def process(m: Dict[str, Any]):
            async with sem:
                prod = m.get("media_product_type") or m.get("media_type")
                ins = await _media_insights(client, str(m.get("id")), prod, token)
                return {
                    "id": m.get("id"),
                    "timestamp": m.get("timestamp"),
                    "caption": m.get("caption"),
                    "permalink": m.get("permalink"),
                    "media_type": m.get("media_type"),
                    "media_product_type": m.get("media_product_type"),
                    "preview_url": m.get("thumbnail_url") or m.get("media_url"),
                    "like_count": m.get("like_count"),
                    "comments_count": m.get("comments_count"),
                    "insights": ins,
                }

        tasks = [process(m) for m in data if m.get("id")]
        if tasks:
            items = await asyncio.gather(*tasks)

    return {"ok": True, "items": items}


@router.get("/insights/media_detail")
async def media_detail(request: Request, persona_num: int, media_id: str):
    """단일 게시글 상세(미디어 필드 + 인사이트)."""
    user_id = _require_login(request)
    mapping = await _get_persona_instagram_mapping(int(user_id), int(persona_num))
    if not mapping or not mapping.get("ig_user_id"):
        raise HTTPException(status_code=400, detail="persona_instagram_not_linked")
    token = await _get_persona_token(int(user_id), int(persona_num))
    if not token:
        raise HTTPException(status_code=401, detail="persona_oauth_required")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{IG_GRAPH}/{media_id}",
            params={
                "access_token": token,
                "fields": "id,timestamp,caption,permalink,media_type,media_product_type,media_url,thumbnail_url,owner,like_count,comments_count",
            },
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="media_not_found")
        m = r.json() or {}
        prod = m.get("media_product_type") or m.get("media_type")
        ins = await _media_insights(client, str(m.get("id")), prod, token)
        return {
            "ok": True,
            "item": {
                "id": m.get("id"),
                "timestamp": m.get("timestamp"),
                "caption": m.get("caption"),
                "permalink": m.get("permalink"),
                "media_type": m.get("media_type"),
                "media_product_type": m.get("media_product_type"),
                "media_url": m.get("media_url"),
                "thumbnail_url": m.get("thumbnail_url"),
                "like_count": m.get("like_count"),
                "comments_count": m.get("comments_count"),
                "insights": ins,
            }
        }


# ====== Daily snapshot storage and delta endpoints ======



async def _paginate_media(client: httpx.AsyncClient, ig_user_id: str, token: str, limit_total: int = 200):
    total = 0
    url = f"{IG_GRAPH}/{ig_user_id}/media"
    params = {
        "access_token": token,
        "fields": "id,timestamp,like_count",
        "limit": 50,
    }
    likes_sum = 0
    while True:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            break
        body = r.json() or {}
        for it in body.get("data", []):
            try:
                likes_sum += int(it.get("like_count") or 0)
            except Exception:
                pass
            total += 1
            if total >= limit_total:
                break
        if total >= limit_total:
            break
        paging = (body or {}).get("paging") or {}
        next_url = paging.get("next")
        if not next_url:
            break
        # next_url already contains everything
        url = next_url
        params = {}
    return likes_sum


async def perform_snapshot(user_id: int, persona_num: int) -> dict:
    """Core snapshot logic reusable by API and scheduler."""

    mapping = await _get_persona_instagram_mapping(int(user_id), int(persona_num))
    if not mapping or not mapping.get("ig_user_id"):
        raise HTTPException(status_code=400, detail="persona_instagram_not_linked")
    token = await _get_persona_token(int(user_id), int(persona_num))
    if not token:
        raise HTTPException(status_code=401, detail="persona_oauth_required")
    ig_user_id = str(mapping["ig_user_id"])
    today = datetime.now(timezone.utc).date()
    async with httpx.AsyncClient(timeout=30) as client:
        usr = await client.get(f"{IG_GRAPH}/{ig_user_id}", params={"access_token": token, "fields": "followers_count"})
        followers_count = None
        if usr.status_code == 200:
            try:
                followers_count = (usr.json() or {}).get("followers_count")
            except Exception:
                followers_count = None
        since = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        ins = await client.get(
            f"{IG_GRAPH}/{ig_user_id}/insights",
            params={
                "metric": "profile_views,reach,impressions,views",
                "period": "day",
                "since": since,
                "access_token": token,
            },
        )
        profile_views = reach = impressions = None
        if ins.status_code == 200:
            try:
                for m in (ins.json() or {}).get("data", []):
                    name = m.get("name"); vals = m.get("values") or []
                    if not vals:
                        continue
                    val = (vals[-1] or {}).get("value")
                    if name == "profile_views":
                        profile_views = val
                    elif name == "reach":
                        reach = val
                    elif name == "impressions":
                        impressions = val
                    elif name == "views":
                        # map views -> impressions for compatibility
                        impressions = val
            except Exception:
                pass
        # If API returns empty datasets (common for no-activity), normalize to 0 instead of NULL
        if profile_views is None:
            profile_views = 0
        if reach is None:
            reach = 0
        if impressions is None:
            impressions = 0
        total_likes = await _paginate_media(client, ig_user_id, token, limit_total=200)
    # upsert to ss_dashboard
    await _ensure_dashboard_table()
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO ss_dashboard
                    (user_id, user_persona_num, ig_user_id, date, followers_count, total_likes, profile_views, reach, impressions)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    followers_count=VALUES(followers_count),
                    total_likes=VALUES(total_likes),
                    profile_views=VALUES(profile_views),
                    reach=VALUES(reach),
                    impressions=VALUES(impressions)
                """,
                (int(user_id), int(persona_num), ig_user_id, today, followers_count, total_likes, profile_views, reach, impressions),
            )
            try:
                await conn.commit()
            except Exception:
                pass
    return {"date": today.strftime("%Y-%m-%d"), "followers_count": followers_count, "total_likes": total_likes, "profile_views": profile_views, "reach": reach, "impressions": impressions}


@router.post("/insights/snapshot")
async def insights_snapshot(request: Request, persona_num: int):
    """Store today's snapshot for follower_count and total_likes (sum over recent media)."""
    user_id = _require_login(request)
    saved = await perform_snapshot(int(user_id), int(persona_num))
    return {"ok": True, "saved": saved}


@router.get("/insights/daily")
async def insights_daily(request: Request, persona_num: int, days: int = 30):
    """Return daily deltas for followers and likes from stored snapshots.

    Fallback: if no snapshot data, try computing followers delta from API timeseries.
    """
    user_id = _require_login(request)
    if days <= 1 or days > 60:
        days = 30

    today = datetime.now(timezone.utc).date()
    since_date = (today - timedelta(days=days - 1))

    rows = []
    try:
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # ensure table exists before querying
                try:
                    await _ensure_dashboard_table()
                except Exception:
                    pass
                await cur.execute(
                    """
                    SELECT date, followers_count, total_likes
                    FROM ss_dashboard
                    WHERE user_id=%s AND user_persona_num=%s AND date >= %s
                    ORDER BY date ASC
                    """,
                    (int(user_id), int(persona_num), since_date),
                )
                rows = await cur.fetchall() or []
    except Exception:
        rows = []

    followers_delta: list[dict] = []
    likes_delta: list[dict] = []
    if len(rows) >= 2:
        prev_f = None
        prev_l = None
        for r in rows:
            d = r.get("date")
            dstr = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
            f = r.get("followers_count")
            l = r.get("total_likes")
            if prev_f is not None and f is not None:
                followers_delta.append({"date": dstr, "value": int(f) - int(prev_f)})
            prev_f = f
            if prev_l is not None and l is not None:
                likes_delta.append({"date": dstr, "value": int(l) - int(prev_l)})
            prev_l = l
    else:
        # fallback for followers: use API series and compute diffs
        try:
            mapping = await _get_persona_instagram_mapping(int(user_id), int(persona_num))
            token = await _get_persona_token(int(user_id), int(persona_num))
            if mapping and mapping.get("ig_user_id") and token:
                ig_user_id = str(mapping["ig_user_id"])
                async with httpx.AsyncClient(timeout=20) as client:
                    ins = await client.get(
                        f"{IG_GRAPH}/{ig_user_id}/insights",
                        params={
                            "metric": "follower_count",
                            "period": "day",
                            "since": (since_date.strftime("%Y-%m-%d")),
                            "until": (today.strftime("%Y-%m-%d")),
                            "access_token": token,
                        },
                    )
                if ins.status_code == 200:
                    vals = ((ins.json() or {}).get("data") or [{}])[0].get("values", [])
                    prev = None
                    for v in vals:
                        t = v.get("end_time") or v.get("date") or ""
                        dstr = t[:10] if isinstance(t, str) else None
                        cur = v.get("value")
                        if prev is not None and cur is not None and dstr:
                            followers_delta.append({"date": dstr, "value": int(cur) - int(prev)})
                        prev = cur
        except Exception:
            pass

    return {"ok": True, "days": days, "followers_delta": followers_delta, "likes_delta": likes_delta}
