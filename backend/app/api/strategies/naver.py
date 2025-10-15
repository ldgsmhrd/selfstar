"""
[파트 개요] Naver OAuth 전략 설정
- 프론트 통신: /auth/naver/* 엔드포인트를 통해 로그인/콜백 처리(라우터는 auth.py)
- 외부 통신: Naver OAuth 서버와 Authorization Code 교환 및 사용자 정보 조회에 사용
"""
import os

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
BACK_URL = os.getenv("BACK_URL", "http://localhost:8000")

# Naver OAuth 설정
NAVER_CALLBACK_URL = f"{BACK_URL}/auth/naver/callback"

# Naver OAuth는 FastAPI의 엔드포인트에서 처리됩니다.