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
import json
import hmac
import hashlib
import base64

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

# 서명용 시크릿 (세션 없이 콜백 처리할 때 state 검증에 사용)
SESSION_SECRET = os.getenv("SESSION_SECRET", "selfstar-secret")

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_dec(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode())

def _sign_state(payload: dict) -> str:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    sig = hmac.new(SESSION_SECRET.encode(), body, hashlib.sha256).digest()
    return f"{_b64url(body)}.{_b64url(sig)}"

def _verify_state(state: str) -> Optional[dict]:
    try:
        body_b64, sig_b64 = state.split(".", 1)
        body = _b64url_dec(body_b64)
        expected = hmac.new(SESSION_SECRET.encode(), body, hashlib.sha256).digest()
        actual = _b64url_dec(sig_b64)
        if not hmac.compare_digest(expected, actual):
            return None
        data = json.loads(body.decode())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


async def _ensure_persona_instagram_columns():
    """ss_persona에 ig_user_id, ig_username, fb_page_id, ig_linked_at 컬럼이 없으면 추가"""
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ss_persona'
                """
            )
            cols = {r["COLUMN_NAME"].lower() for r in (await cur.fetchall() or [])}
        alters = []
        if "ig_user_id" not in cols:
            alters.append("ADD COLUMN ig_user_id VARCHAR(64) NULL")
        if "ig_username" not in cols:
            alters.append("ADD COLUMN ig_username VARCHAR(150) NULL")
        if "fb_page_id" not in cols:
            alters.append("ADD COLUMN fb_page_id VARCHAR(64) NULL")
        if "ig_linked_at" not in cols:
            alters.append("ADD COLUMN ig_linked_at DATETIME NULL")
        if alters:
            sql = "ALTER TABLE ss_persona " + ", ".join(alters)
            async with conn.cursor() as cur2:
                await cur2.execute(sql)
                try:
                    await conn.commit()
                except Exception:
                    pass

async def _resolve_persona_num_by_id(user_id: int, persona_id: int) -> Optional[int]:
    """사용자 소유의 persona_id로 user_persona_num을 구한다."""
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        # 테이블 컬럼 확인 후 안전하게 WHERE 절 구성
        has_id_col = False
        async with conn.cursor(aiomysql.DictCursor) as curcols:
            await curcols.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ss_persona'
                """
            )
            cols = {r.get("COLUMN_NAME", "").lower() for r in (await curcols.fetchall() or [])}
            has_id_col = "id" in cols

        where = "user_id=%s AND persona_id=%s"
        params = (user_id, int(persona_id))
        if has_id_col:
            where = "user_id=%s AND (id=%s OR persona_id=%s)"
            params = (user_id, int(persona_id), int(persona_id))

        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT user_persona_num
                FROM ss_persona
                WHERE {where}
                LIMIT 1
                """,
                params,
            )
            row = await cur.fetchone()
            if not row:
                return None
            try:
                return int(row.get("user_persona_num"))
            except Exception:
                return None

async def _update_persona_instagram_mapping(user_id: int, persona_num: int, ig_user_id: str, ig_username: Optional[str], fb_page_id: str):
    """ss_persona에 instagram 매핑을 저장 (컬럼 + JSON 동기화)"""
    await _ensure_persona_instagram_columns()
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
                (user_id, int(persona_num)),
            )
            row = await cur.fetchone()
            params = {}
            if row and row.get("persona_parameters"):
                try:
                    params = json.loads(row["persona_parameters"]) or {}
                except Exception:
                    params = {}
            # 업데이트
            params = params if isinstance(params, dict) else {}
            params["instagram"] = {
                "ig_user_id": ig_user_id,
                "ig_username": ig_username,
                "fb_page_id": fb_page_id,
            }
        async with conn.cursor() as cur2:
            await cur2.execute(
                """
                UPDATE ss_persona
                SET persona_parameters=%s,
                    ig_user_id=%s,
                    ig_username=%s,
                    fb_page_id=%s,
                    ig_linked_at=NOW()
                WHERE user_id=%s AND user_persona_num=%s
                """,
                (json.dumps(params, ensure_ascii=False), ig_user_id, ig_username, fb_page_id, user_id, int(persona_num)),
            )
            try:
                await conn.commit()
            except Exception:
                pass

async def _clear_persona_instagram_mapping(user_id: int, persona_num: int):
    """ss_persona에서 instagram 매핑 제거(컬럼 + JSON 동기화)."""
    await _ensure_persona_instagram_columns()
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        # 기존 JSON 로드
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT persona_parameters
                FROM ss_persona
                WHERE user_id=%s AND user_persona_num=%s
                LIMIT 1
                """,
                (user_id, int(persona_num)),
            )
            row = await cur.fetchone()
            params = {}
            if row and row.get("persona_parameters"):
                try:
                    params = json.loads(row["persona_parameters"]) or {}
                except Exception:
                    params = {}
            if isinstance(params, dict) and "instagram" in params:
                params.pop("instagram", None)
        async with conn.cursor() as cur2:
            await cur2.execute(
                """
                UPDATE ss_persona
                SET persona_parameters=%s,
                    ig_user_id=NULL,
                    ig_username=NULL,
                    fb_page_id=NULL,
                    ig_linked_at=NULL
                WHERE user_id=%s AND user_persona_num=%s
                """,
                (json.dumps(params, ensure_ascii=False), user_id, int(persona_num)),
            )
            try:
                await conn.commit()
            except Exception:
                pass

async def _get_persona_instagram_mapping(user_id: int, persona_num: int) -> Optional[Dict[str, Any]]:
    await _ensure_persona_instagram_columns()
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        # 1) 컬럼 우선 조회
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT ig_user_id, ig_username, fb_page_id, persona_parameters
                FROM ss_persona
                WHERE user_id=%s AND user_persona_num=%s
                LIMIT 1
                """,
                (user_id, int(persona_num)),
            )
            row = await cur.fetchone()
            if not row:
                return None
            if row.get("ig_user_id") and row.get("fb_page_id"):
                return {
                    "user_id": user_id,
                    "user_persona_num": int(persona_num),
                    "ig_user_id": row.get("ig_user_id"),
                    "ig_username": row.get("ig_username"),
                    "fb_page_id": row.get("fb_page_id"),
                }
            # 2) 컬럼이 비어있으면 JSON에서 시도(과거 데이터 호환)
            try:
                params = json.loads(row.get("persona_parameters") or "{}") or {}
            except Exception:
                params = {}
            ig = params.get("instagram")
            if isinstance(ig, dict) and ig.get("ig_user_id") and ig.get("fb_page_id"):
                return {
                    "user_id": user_id,
                    "user_persona_num": int(persona_num),
                    "ig_user_id": ig.get("ig_user_id"),
                    "ig_username": ig.get("ig_username"),
                    "fb_page_id": ig.get("fb_page_id"),
                }
            return None



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


async def _ensure_connector_persona_table():
    """Persona별 OAuth 토큰 저장 테이블 생성"""
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ss_instagram_connector_persona (
                  user_id INT NOT NULL,
                  user_persona_num INT NOT NULL,
                  long_lived_user_token TEXT NOT NULL,
                  expires_at DATETIME NULL,
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


async def _store_persona_token(user_id: int, persona_num: int, token: str, expires_in: Optional[int] = None):
    await _ensure_connector_persona_table()
    expires_at: Optional[datetime] = None
    if isinstance(expires_in, int) and expires_in > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO ss_instagram_connector_persona (user_id, user_persona_num, long_lived_user_token, expires_at)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  long_lived_user_token=VALUES(long_lived_user_token),
                  expires_at=VALUES(expires_at)
                """,
                (user_id, int(persona_num), token, expires_at.replace(tzinfo=None) if expires_at else None),
            )
            try:
                await conn.commit()
            except Exception:
                pass


async def _get_persona_token(user_id: int, persona_num: int) -> Optional[str]:
    await _ensure_connector_persona_table()
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT long_lived_user_token, expires_at
                FROM ss_instagram_connector_persona
                WHERE user_id=%s AND user_persona_num=%s
                """,
                (user_id, int(persona_num)),
            )
            row = await cur.fetchone()
            if not row:
                return None
            return row.get("long_lived_user_token")


async def _get_effective_token(user_id: int, persona_num: Optional[int]) -> Optional[str]:
    """persona에 연결된 토큰 우선, 없으면 사용자 레벨 토큰, 마지막으로 ENV 토큰"""
    token: Optional[str] = None
    if persona_num is not None:
        token = await _get_persona_token(user_id, persona_num)
    if not token:
        token = await _get_user_token(user_id)
    if not token:
        token = ENV_USER_TOKEN
    return token


def _require_login(request: Request) -> int:
    uid = request.session.get("user_id") if hasattr(request, "session") else None
    if not uid:
        raise HTTPException(status_code=401, detail="login_required")
    return int(uid)


@router.get("/start")
async def start_oauth(
    request: Request,
    persona_num: Optional[int] = None,
    persona_id: Optional[int] = None,
    fresh: Optional[int] = None,
    logout: Optional[int] = None,
    revoke: Optional[int] = None,
    picker: Optional[int] = None,
):
    """
    Meta OAuth 시작. 사용자 로그인 필요.
    """
    uid = _require_login(request)
    if not META_APP_ID:
        raise HTTPException(status_code=500, detail="META_APP_ID not configured")
    # 세션 없이 콜백에서 사용자 식별/검증을 할 수 있도록 서명된 state 발급
    # persona_id가 전달되면 persona_num으로 해석
    eff_persona_num: Optional[int] = None
    if persona_id is not None:
        eff_persona_num = await _resolve_persona_num_by_id(uid, int(persona_id))
    if eff_persona_num is None and persona_num is not None:
        eff_persona_num = int(persona_num)

    state_payload = {
        "uid": uid,
        "nonce": secrets.token_urlsafe(8),
        "ts": int(datetime.now(timezone.utc).timestamp()),
    }
    if eff_persona_num is not None:
        state_payload["persona_num"] = eff_persona_num
    if persona_id is not None:
        state_payload["persona_id"] = int(persona_id)
    state = _sign_state(state_payload)
    # 스코프 문자열 정리(공백 제거)
    scope = ",".join([s.strip() for s in (META_SCOPES or "").split(",") if s.strip()])
    params = {
        "client_id": META_APP_ID,
        "redirect_uri": META_REDIRECT_URI,
        "response_type": "code",
        "scope": scope,
        "state": state,
        # 기본: 권한/선택 화면 재요청
        "auth_type": "rerequest",
        "display": "page",
        "prompt": "consent",
    }
    # fresh=1 이면 계정 재인증 유도(계정 선택 화면으로 진입 가능성이 커짐)
    if fresh:
        params["auth_type"] = "reauthorize"
        params["display"] = "popup"
    auth_url = f"{FACEBOOK_DIALOG}/dialog/oauth?{httpx.QueryParams(params)}"

    # revoke=1 이면 기존 앱 권한을 제거하여 진짜 '처음부터' 동의/선택 플로우를 강제
    if revoke:
        # 가능한 한 persona 토큰을 우선 사용
        token_to_revoke: Optional[str] = None
        if eff_persona_num is not None:
            token_to_revoke = await _get_persona_token(uid, eff_persona_num)
        if not token_to_revoke:
            token_to_revoke = await _get_user_token(uid)
        try:
            if token_to_revoke:
                async with httpx.AsyncClient(timeout=15) as client:
                    # DELETE /me/permissions → 사용자와 앱의 연결 권한 제거
                    await client.delete(f"{GRAPH}/me/permissions", params={"access_token": token_to_revoke})
        except Exception:
            # 실패해도 로그인/동의 플로우는 계속 진행
            pass
    # 계정 선택 화면부터 강제 진입: login.php 래핑
    final_url = auth_url
    if picker:
        login_params = {
            "skip_api_login": 1,
            "api_key": META_APP_ID,
            "signed_next": 1,
            "next": auth_url,
        }
        final_url = f"https://www.facebook.com/login.php?{httpx.QueryParams(login_params)}"

    if logout:
        # 사용자 요청 시 페이스북 글로벌 로그아웃을 먼저 수행 후, OAuth로 리다이렉트
        # 주의: 이 동작은 브라우저 전체의 facebook.com 세션을 종료합니다.
        logout_url = f"https://www.facebook.com/logout.php?{httpx.QueryParams({'next': final_url, 'confirm': 1})}"
        return RedirectResponse(url=logout_url, status_code=302)
    return RedirectResponse(url=final_url, status_code=302)


@router.get("/_debug-token")
async def debug_token(request: Request):
    """현재 사용자에 저장된 Long-Lived User Token의 유효성/주체를 확인"""
    uid = _require_login(request)
    token = await _get_user_token(uid) or ENV_USER_TOKEN
    if not token:
        raise HTTPException(status_code=404, detail="no_token")
    if not (META_APP_ID and META_APP_SECRET):
        raise HTTPException(status_code=500, detail="meta_app_not_configured")
    app_token = f"{META_APP_ID}|{META_APP_SECRET}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{GRAPH}/debug_token", params={"input_token": token, "access_token": app_token})
    return {"ok": r.status_code == 200, "status": r.status_code, "json": r.json()}


@router.get("/_raw-accounts")
async def raw_accounts(request: Request):
    """/me/accounts의 원시 응답(필드 포함)을 반환해 연결/권한 문제를 진단"""
    uid = _require_login(request)
    token = await _get_user_token(uid) or ENV_USER_TOKEN
    if not token:
        raise HTTPException(status_code=404, detail="no_token")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{GRAPH}/me/accounts",
            params={
                "access_token": token,
                "fields": "id,name,perms,instagram_business_account{id,username},access_token",
            },
        )
    return {"ok": r.status_code == 200, "status": r.status_code, "json": r.json()}


@router.get("/_permissions")
async def list_permissions(request: Request):
    """현재 사용자 토큰이 가진 권한 목록 검사"""
    uid = _require_login(request)
    token = await _get_user_token(uid) or ENV_USER_TOKEN
    if not token:
        raise HTTPException(status_code=404, detail="no_token")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{GRAPH}/me/permissions", params={"access_token": token})
    return {"ok": r.status_code == 200, "status": r.status_code, "json": r.json()}


@router.get("/callback")
async def oauth_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    if error:
        raise HTTPException(status_code=400, detail=f"oauth_error:{error}")
    if not code:
        raise HTTPException(status_code=400, detail="code_missing")
    # state 검증(세션 대신 서명으로 무결성 보장)
    data = _verify_state(state or "")
    if not data or "uid" not in data:
        raise HTTPException(status_code=400, detail="state_invalid")
    user_id = int(data["uid"])  # 세션 없이도 사용자 식별
    persona_num: Optional[int] = None
    if isinstance(data.get("persona_num"), int):
        persona_num = int(data["persona_num"]) if data["persona_num"] >= 0 else None
    # state에 persona_id만 있고 persona_num이 없다면 콜백에서 해석
    if persona_num is None and isinstance(data.get("persona_id"), int):
        persona_num = await _resolve_persona_num_by_id(user_id, int(data["persona_id"]))
    if not META_APP_ID or not META_APP_SECRET:
        raise HTTPException(status_code=500, detail="meta_app_not_configured")
    # 페르소나 전용 정책: 반드시 persona가 지정되어야 함
    if persona_num is None:
        raise HTTPException(status_code=400, detail="persona_required")

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
        # 장기 토큰 교환 실패
        raise HTTPException(status_code=502, detail=f"long_token_failed:{ll_res.text}")
    ll_json = ll_res.json()
    long_token = ll_json.get("access_token") or short_token
    expires_in = ll_json.get("expires_in") or token_json.get("expires_in")

    # 페르소나 전용 저장
    await _store_persona_token(user_id, persona_num, long_token, expires_in if isinstance(expires_in, int) else None)

    # 프론트로 리다이렉트 유도(성공 표시)
    frontend = (os.getenv("FRONTEND_URL") or "http://localhost:5174").rstrip("/")
    return RedirectResponse(url=f"{frontend}/mypage?ig=connected", status_code=302)


@router.get("/accounts")
async def list_ig_accounts(request: Request, persona_num: Optional[int] = None, persona_id: Optional[int] = None):
    user_id = _require_login(request)
    # persona_id 우선 해석
    if persona_id is not None and persona_num is None:
        persona_num = await _resolve_persona_num_by_id(user_id, int(persona_id))
        if persona_num is None:
            raise HTTPException(status_code=404, detail="persona_not_found")
    # 페르소나 분리 강제: persona는 필수, 해당 페르소나 토큰만 허용
    if persona_num is None:
        raise HTTPException(status_code=400, detail="persona_num_required")
    token: Optional[str] = await _get_persona_token(user_id, int(persona_num))
    if not token:
        raise HTTPException(status_code=401, detail="persona_oauth_required")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{GRAPH}/me/accounts",
            params={
                "access_token": token,
                "fields": "id,name,instagram_business_account{id,username}",
            },
        )
    # 원 요청 실패 시에도 granular_scopes 폴백을 시도해 사용자 경험을 개선
    initial_error_text: Optional[str] = None
    if r.status_code != 200:
        # 토큰 오류(190) 등은 즉시 재인증 유도로 반환
        try:
            errj = r.json() or {}
            e = (errj.get("error") or {})
            code = e.get("code")
            sub = e.get("error_subcode")
            if code == 190 or str(code) == "190" or (e.get("type") == "OAuthException"):
                # 만료/권한 없음/앱 미승인(458/463/467 등) → 재인증 필요
                raise HTTPException(status_code=401, detail="persona_oauth_required")
        except HTTPException:
            raise
        except Exception:
            pass
        try:
            initial_error_text = r.text
        except Exception:
            initial_error_text = None
        # 아래 폴백 로직으로 계속 진행 (items가 비면 오류 메시지 포함하여 반환)

    items: List[Dict[str, Any]] = []
    data = []
    try:
        data = (r.json().get("data") or []) if r.status_code == 200 else []
    except Exception:
        data = []
    for p in data:
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

    # Fallback: 일부 환경에서 /me/accounts 가 빈 배열을 반환하는 경우가 있어,
    # debug_token의 granular_scopes 에 포함된 Page ID들을 조회해 IG 연결을 확인한다.
    if not items:
        if not (META_APP_ID and META_APP_SECRET):
            # 앱 설정이 없으면 폴백 불가
            # 실패 메시지 포함
            return {"ok": True, "items": items, "warning": initial_error_text}
        app_token = f"{META_APP_ID}|{META_APP_SECRET}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                dbg = await client.get(
                    f"{GRAPH}/debug_token",
                    params={"input_token": token, "access_token": app_token},
                )
            if dbg.status_code == 200:
                dbg_json = dbg.json() or {}
                gscopes = ((dbg_json.get("data") or {}).get("granular_scopes") or [])
                page_ids: List[str] = []
                for gs in gscopes:
                    if gs.get("scope") == "pages_show_list":
                        for pid in (gs.get("target_ids") or []):
                            if isinstance(pid, str):
                                page_ids.append(pid)
                # 각 페이지에 대해 IG 연결 조회
                async with httpx.AsyncClient(timeout=30) as client:
                    for pid in page_ids:
                        pr = await client.get(
                            f"{GRAPH}/{pid}",
                            params={
                                "access_token": token,
                                "fields": "name,instagram_business_account{id,username}",
                            },
                        )
                        if pr.status_code == 200:
                            pj = pr.json() or {}
                            iga = (pj.get("instagram_business_account") or {})
                            if iga.get("id"):
                                items.append(
                                    {
                                        "page_id": pid,
                                        "page_name": pj.get("name"),
                                        "ig_user_id": iga.get("id"),
                                        "ig_username": iga.get("username"),
                                    }
                                )
        except Exception:
            # 폴백 실패는 조용히 무시하고 빈 목록 유지
            pass
    # 폴백 후에도 비어있다면 최초 오류 메시지를 함께 전달
    if not items and initial_error_text:
        return {"ok": True, "items": items, "warning": initial_error_text}
    return {"ok": True, "items": items}


@router.post("/unlink")
async def unlink_persona_account(
    request: Request,
    persona_num: Optional[int] = None,
    persona_id: Optional[int] = None,
):
    """페르소나에서 IG 연결 및 토큰을 제거(안전한 재연동을 위해)."""
    user_id = _require_login(request)
    # persona_id 우선 해석
    if persona_id is not None and persona_num is None:
        persona_num = await _resolve_persona_num_by_id(user_id, int(persona_id))
        if persona_num is None:
            raise HTTPException(status_code=404, detail="persona_not_found")
    if persona_num is None:
        raise HTTPException(status_code=400, detail="persona_num_required")

    await _ensure_connector_persona_table()
    pool = await get_mysql_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM ss_instagram_connector_persona WHERE user_id=%s AND user_persona_num=%s",
                (user_id, int(persona_num)),
            )
            try:
                await conn.commit()
            except Exception:
                pass
    # ss_persona의 매핑도 정리
    await _clear_persona_instagram_mapping(user_id, int(persona_num))
    return {"ok": True}


@router.post("/link")
async def link_persona_account(
    request: Request,
    ig_user_id: str,
    fb_page_id: str,
    ig_username: str | None = None,
    persona_num: Optional[int] = None,
    persona_id: Optional[int] = None,
):
    user_id = _require_login(request)
    # persona_id 우선 해석
    if persona_id is not None and persona_num is None:
        persona_num = await _resolve_persona_num_by_id(user_id, int(persona_id))
        if persona_num is None:
            raise HTTPException(status_code=404, detail="persona_not_found")
    if persona_num is None:
        raise HTTPException(status_code=400, detail="persona_num_required")
    # 링크 전, 해당 페르소나가 OAuth 완료하여 자체 토큰을 보유했는지 확인
    persona_token = await _get_persona_token(user_id, int(persona_num))
    if not persona_token:
        raise HTTPException(status_code=401, detail="persona_oauth_required")
    # ss_persona.persona_parameters에만 저장 (단일 소스)
    await _update_persona_instagram_mapping(user_id, int(persona_num), ig_user_id, ig_username, fb_page_id)
    return {"ok": True}


@router.get("/mapping")
async def get_persona_mapping(request: Request, persona_num: Optional[int] = None, persona_id: Optional[int] = None):
    user_id = _require_login(request)
    # persona_id 우선 해석
    if persona_id is not None and persona_num is None:
        persona_num = await _resolve_persona_num_by_id(user_id, int(persona_id))
        if persona_num is None:
            raise HTTPException(status_code=404, detail="persona_not_found")
    if persona_num is None:
        raise HTTPException(status_code=400, detail="persona_num_required")
    # ss_persona.persona_parameters.instagram에서 조회
    mapping = await _get_persona_instagram_mapping(user_id, int(persona_num))
    if mapping:
        return {"ok": True, "linked": True, "mapping": mapping}
    return {"ok": True, "linked": False}
