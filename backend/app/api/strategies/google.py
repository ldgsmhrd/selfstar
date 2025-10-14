"""
[파트 개요] Google OAuth 전략 설정
- 프론트 통신: /auth/google/* 엔드포인트를 통해 로그인/콜백 처리(라우터는 auth.py)
- 외부 통신: Google OAuth 서버와 Authorization Code 교환 및 사용자 정보 조회에 사용
"""
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BACK_URL = os.getenv("BACK_URL", "http://localhost:8000")

# Google OAuth 설정
GOOGLE_CALLBACK_URL = f"{BACK_URL}/auth/google/callback"

# Google OAuth는 FastAPI의 엔드포인트에서 처리됩니다.