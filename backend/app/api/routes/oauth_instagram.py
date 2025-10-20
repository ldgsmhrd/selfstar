from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import aiomysql
from app.api.core.mysql import get_mysql_pool
from datetime import datetime, timedelta, timezone
import secrets

router = APIRouter(prefix="/oauth/instagram", tags=["instagram"])

GRAPH = (os.getenv("META_GRAPH") or "https://graph.facebook.com/v20.0").rstrip("/")
FACEBOOK_DIALOG = (os.getenv("META_FACEBOOK") or "https://www.facebook.com/v20.0").rstrip("/")

# Meta App OAuth 설정(.env)
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_REDIRECT_URI = (os.getenv("META_REDIRECT_URI") or f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/oauth/instagram/callback").rstrip("/")
META_SCOPES = os.getenv("META_SCOPES", "pages_show_list,instagram_basic")

# 사용자 제공 Long-Lived User Token (테스트/개발용): 절대 로그로 남기지 말 것
ENV_USER_TOKEN = os.getenv("IG_LONG_LIVED_USER_TOKEN") or os.getenv("META_USER_TOKEN")


async def _ensure_mapping_table():
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ss_persona_instagram (
                  user_id INT NOT NULL,
                  user_persona_num INT NOT NULL,
                  ig_user_id VARCHAR(64) NOT NULL,
                  ig_username VARCHAR(150) NULL,
                  fb_page_id VARCHAR(64) NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
                  PRIMARY KEY (user_id, user_persona_num)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
            try:
                await conn.commit()
            except Exception:
                pass


async def _ensure_connector_table():
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ss_instagram_connector (
                  user_id INT NOT NULL PRIMARY KEY,
                  long_lived_user_token TEXT NOT NULL,
                  expires_at DATETIME NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
            try:
                await conn.commit()
            except Exception:
                pass


async def _store_user_token(user_id: int, token: str, expires_in: Optional[int] = None):
    await _ensure_connector_table()
    expires_at: Optional[datetime] = None
    if isinstance(expires_in, int) and expires_in > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO ss_instagram_connector (user_id, long_lived_user_token, expires_at)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  long_lived_user_token=VALUES(long_lived_user_token),
                  expires_at=VALUES(expires_at)
                """,
                (user_id, token, expires_at.replace(tzinfo=None) if expires_at else None),
            )
            try:
                await conn.commit()
            except Exception:
                pass


async def _get_user_token(user_id: int) -> Optional[str]:
    await _ensure_connector_table()
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT long_lived_user_token, expires_at FROM ss_instagram_connector WHERE user_id=%s",
                (user_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            return row.get("long_lived_user_token")


def _require_login(request: Request) -> int:
    uid = request.session.get("user_id") if hasattr(request, "session") else None
    if not uid:
        raise HTTPException(status_code=401, detail="login_required")
    return int(uid)


@router.get("/start")
async def start_oauth(request: Request):
    """
    Meta OAuth 시작. 사용자 로그인 필요.
    """
    _ = _require_login(request)
    if not META_APP_ID:
        raise HTTPException(status_code=500, detail="META_APP_ID not configured")
    # CSRF 방지 state 생성 후 세션 저장
    state = secrets.token_urlsafe(16)
    try:
        request.session["ig_oauth_state"] = state
    except Exception:
        pass
    # 스코프 문자열 정리(공백 제거)
    scope = ",".join([s.strip() for s in (META_SCOPES or "").split(",") if s.strip()])
    params = {
        "client_id": META_APP_ID,
        "redirect_uri": META_REDIRECT_URI,
        "response_type": "code",
        "scope": scope,
        "state": state,
    }
    auth_url = f"{FACEBOOK_DIALOG}/dialog/oauth?{httpx.QueryParams(params)}"
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/callback")
async def oauth_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    user_id = _require_login(request)
    if error:
        raise HTTPException(status_code=400, detail=f"oauth_error:{error}")
    if not code:
        raise HTTPException(status_code=400, detail="code_missing")
    # state 검증
    sess_state = None
    try:
        sess_state = request.session.get("ig_oauth_state")
    except Exception:
        pass
    if not state or not sess_state or state != sess_state:
        raise HTTPException(status_code=400, detail="state_mismatch")
    if not META_APP_ID or not META_APP_SECRET:
        raise HTTPException(status_code=500, detail="meta_app_not_configured")

    # code -> short-lived user access token 교환
    async with httpx.AsyncClient(timeout=30) as client:
        token_res = await client.get(
            f"{GRAPH}/oauth/access_token",
            params={
                "client_id": META_APP_ID,
                "client_secret": META_APP_SECRET,
                "redirect_uri": META_REDIRECT_URI,
                "code": code,
            },
        )
    if token_res.status_code != 200:
        raise HTTPException(status_code=502, detail=f"token_failed:{token_res.text}")
    token_json = token_res.json()
    short_token = token_json.get("access_token")
    if not short_token:
        raise HTTPException(status_code=502, detail="short_token_missing")

    # long-lived user token 교환
    async with httpx.AsyncClient(timeout=30) as client:
        ll_res = await client.get(
            f"{GRAPH}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": META_APP_ID,
                "client_secret": META_APP_SECRET,
                "fb_exchange_token": short_token,
            },
        )
    if ll_res.status_code != 200:
        # 실패 시 일단 short_token 저장 시도(짧은 만료)
        await _store_user_token(user_id, short_token, token_json.get("expires_in"))
        raise HTTPException(status_code=502, detail=f"long_token_failed:{ll_res.text}")
    ll_json = ll_res.json()
    long_token = ll_json.get("access_token") or short_token
    expires_in = ll_json.get("expires_in") or token_json.get("expires_in")

    await _store_user_token(user_id, long_token, expires_in if isinstance(expires_in, int) else None)

    # 프론트로 리다이렉트 유도(성공 표시)
    frontend = (os.getenv("FRONTEND_URL") or "http://localhost:5174").rstrip("/")
    return RedirectResponse(url=f"{frontend}/mypage?ig=connected", status_code=302)


@router.get("/accounts")
async def list_ig_accounts(request: Request):
    user_id = _require_login(request)
    # 사용자 토큰 우선, 없으면 서버 토큰 폴백
    token = await _get_user_token(user_id)
    token = token or ENV_USER_TOKEN
    if not token:
        raise HTTPException(status_code=500, detail="server_token_missing")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{GRAPH}/me/accounts",
            params={
                "access_token": token,
                "fields": "id,name,instagram_business_account{id,username}",
            },
        )
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"accounts_failed: {r.text}")

    items: List[Dict[str, Any]] = []
    for p in (r.json().get("data") or []):
        iga = (p.get("instagram_business_account") or {})
        if iga.get("id"):
            items.append(
                {
                    "page_id": p.get("id"),
                    "page_name": p.get("name"),
                    "ig_user_id": iga.get("id"),
                    "ig_username": iga.get("username"),
                }
            )
    return {"ok": True, "items": items}


@router.post("/link")
async def link_persona_account(
    request: Request,
    persona_num: int,
    ig_user_id: str,
    fb_page_id: str,
    ig_username: str | None = None,
):
    user_id = _require_login(request)
    await _ensure_mapping_table()
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # upsert
            await cur.execute(
                """
                INSERT INTO ss_persona_instagram (user_id, user_persona_num, ig_user_id, ig_username, fb_page_id)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  ig_user_id=VALUES(ig_user_id),
                  ig_username=VALUES(ig_username),
                  fb_page_id=VALUES(fb_page_id)
                """,
                (user_id, int(persona_num), ig_user_id, ig_username, fb_page_id),
            )
            try:
                await conn.commit()
            except Exception:
                pass
    return {"ok": True}


@router.get("/mapping")
async def get_persona_mapping(request: Request, persona_num: int):
    user_id = _require_login(request)
    await _ensure_mapping_table()
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT user_id, user_persona_num, ig_user_id, ig_username, fb_page_id
                FROM ss_persona_instagram
                WHERE user_id=%s AND user_persona_num=%s
                """,
                (user_id, int(persona_num)),
            )
            row = await cur.fetchone()
            if not row:
                return {"ok": True, "linked": False}
            return {"ok": True, "linked": True, "mapping": row}
