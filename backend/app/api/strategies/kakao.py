"""
[파트 개요] Kakao OAuth 전략 설정
- 프론트 통신: /auth/kakao/* 엔드포인트를 통해 로그인/콜백 처리(라우터는 auth.py)
- 외부 통신: Kakao OAuth 서버와 Authorization Code 교환 및 사용자 정보 조회에 사용
"""
import os

KAKAO_CLIENT_ID = "7cb111d7e80f4b6d021c1c7ad8f741ec"
BACK_URL = os.getenv("BACK_URL", "http://localhost:8000")

# Kakao OAuth 설정
KAKAO_CALLBACK_URL = f"{BACK_URL}/auth/kakao/callback"

# Kakao OAuth는 FastAPI의 엔드포인트에서 처리됩니다.