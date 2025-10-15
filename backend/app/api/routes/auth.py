
"""
[파트 개요] 인증(OAuth) 라우터
- 프론트 통신: /auth/* 엔드포인트로 로그인/콜백/세션 관리
- 외부 통신: Kakao/Google/Naver OAuth 서버와 토큰 교환 및 사용자 정보 조회
"""
# FastAPI 인증 라우터
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import os
import logging
from urllib.parse import urlencode

from app.api.models.users import upsert_user_from_oauth, find_user_by_id


logger = logging.getLogger("auth")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter(prefix="/auth", tags=["auth"])


# ----- 환경 변수(기본값 포함) -----
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5174")
KAKAO_SCOPE = os.getenv("KAKAO_SCOPE", "profile_nickname,profile_image")  # 기본값에서 이메일 요청 제거
KAKAO_ADMIN_KEY = os.getenv("KAKAO_ADMIN_KEY")
GOOGLE_SCOPE = os.getenv("GOOGLE_SCOPE", "openid email profile")


# ----- Me (세션 기반 본인 확인) -----
@router.get("/me")
async def me(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"ok": True, "authenticated": False, "user": None}

    user = await find_user_by_id(int(user_id))
    if not user:
        # 세션은 있는데 DB에 없으면 세션 정리
        request.session.clear()
        return {"ok": True, "authenticated": False, "user": None}

    # 프론트에서 필요한 최소 정보만 반환

    return {
        "ok": True,
        "authenticated": True,
        "user": {
            "id": user["user_id"],
            "nick": user.get("user_nick"),
            "img": user.get("user_img"),
            "platform": user.get("user_platform"),
        },
    }

    # 3) upsert & 세션 저장
    user_row = await upsert_user_from_oauth(
        provider="kakao", inherent=inherent, nick=nick, img=img
    )
    request.session["user_id"] = int(user_row["user_id"])  # 쿠키 세션 저장

    # 4) 프론트로 리다이렉트 (로그인 완료)
    return RedirectResponse(url=f"{FRONTEND_URL}/?login=success")


# ----- 로그아웃 -----
@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse({"ok": True})


# ----- 카카오 연결 해제(관리자키 필요) -----
@router.post("/kakao/unlink")
async def kakao_unlink(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    if not KAKAO_ADMIN_KEY:
        raise HTTPException(status_code=500, detail="KAKAO_ADMIN_KEY not configured on server")

    # 유저 정보 조회
    user = await find_user_by_id(int(user_id))
    if not user or user.get("user_platform") != "kakao":
        raise HTTPException(status_code=400, detail="Not a Kakao-linked user")

    inherent = user.get("user_inherent")  # 카카오 고유 사용자 ID
    if not inherent:
        raise HTTPException(status_code=400, detail="Kakao user id missing")

    unlink_url = "https://kapi.kakao.com/v1/user/unlink"
    headers = {"Authorization": f"KakaoAK {KAKAO_ADMIN_KEY}"}
    data = {"target_id_type": "user_id", "target_id": inherent}

    async with httpx.AsyncClient() as client:
        resp = await client.post(unlink_url, headers=headers, data=data)
        if resp.status_code != 200:
            logger.error("Kakao unlink error [%s]: %s", resp.status_code, resp.text)
            raise HTTPException(status_code=400, detail="Failed to unlink Kakao user")

    # 세션 정리(선택)
    request.session.clear()
    return {"ok": True, "unlinked": True}


# ----- 구글 로그인 -----
@router.get("/google/login")
async def google_login():
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", f"{BACKEND_URL}/auth/google/callback")

    params = {
        "response_type": "code",
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "scope": GOOGLE_SCOPE,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


# 과거 프론트에서 /auth/google 로 접근하는 호환 경로 지원
@router.get("/google")
async def google_login_alias():
    return await google_login()


# ----- 구글 콜백 -----
@router.get("/google/callback")
async def google_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", f"{BACKEND_URL}/auth/google/callback")

    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "grant_type": "authorization_code",
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(token_url, data=token_payload, headers={"Accept": "application/json"})
        if token_resp.status_code != 200:
            logger.error("Google token error [%s]: %s", token_resp.status_code, token_resp.text)
            raise HTTPException(status_code=400, detail="Failed to retrieve Google token")

        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token missing")

    # 사용자 정보 조회
        userinfo_resp = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            logger.error("Google userinfo error [%s]: %s", userinfo_resp.status_code, userinfo_resp.text)
            raise HTTPException(status_code=400, detail="Failed to retrieve Google user info")

        info = userinfo_resp.json()
        sub = str(info.get("sub"))
        name = info.get("name") or info.get("given_name") or info.get("email")
        picture = info.get("picture")

    user_row = await upsert_user_from_oauth(provider="google", inherent=sub, nick=name, img=picture)
    request.session["user_id"] = int(user_row["user_id"])  # 쿠키 세션 저장

    return RedirectResponse(url=f"{FRONTEND_URL}/?login=success")
