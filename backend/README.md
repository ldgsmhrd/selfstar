# Backend (FastAPI)

이 문서는 백엔드의 유일한 문서입니다. `app/api/README.md`의 모든 내용은 여기에 통합되었으며, 서버는 항상 Python 가상환경(.venv)에서 실행하는 것을 기준으로 합니다.

## 폴더 구조 (정리됨)
```
backend/
	app/
		__init__.py
		main.py                 # FastAPI 앱 엔트리
		api/
			__init__.py
			routes/
				__init__.py      # 라우터 집계(하위 라우터 포함)
		core/
			__init__.py
			config.py
			logging.py
		models/
			__init__.py
			base.py
		schemas/
			__init__.py
			health.py
		tests/
	.env.example
	README.md
	requirements.txt
```

## 요구 사항

## 설치 (Windows PowerShell 기준)
프로젝트 루트는 `backend/` 입니다.

1) 가상환경 생성/활성화 — 항상 .venv를 활성화한 상태에서 서버/테스트를 실행하세요.
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

2) 의존성 설치
```powershell
pip install -r requirements.txt
```
Backend (FastAPI)

역할
- 인증(Kakao 등)과 세션 관리
- 이미지 생성 요청을 AI 서버로 위임 → data URI 수신 후 파일 저장(/media)
- 프론트 개발 서버 프록시 대상(/auth, /api, /media)

필수 요구사항
- Python 3.12+

설치
```powershell
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

환경 변수(예시)
```powershell
$env:AI_SERVICE_URL = "http://localhost:8600"
$env:BACKEND_URL    = "http://localhost:8000"
$env:FRONTEND_URL   = "http://localhost:5174"
$env:SESSION_SECRET = "selfstar-secret"
# 선택: $env:MEDIA_ROOT = "C:\\path\\to\\media"  # 기본: backend/app/media
```

실행
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Health: http://localhost:8000/health
```

주요 라우트
- GET /health
- POST /api/image/generate → { ok, image: dataURI, url?: /media/xxx.png }
	- AI로 위임 성공 시 data URI를 디코드해 파일 저장 후 url도 함께 반환
- 정적 /media → 이미지 파일 제공
 - GET /auth/me → 세션 사용자(동의 필요 여부 포함: needs_consent)
 - PATCH /user/me/profile → 세션 사용자의 성별+생년월일 동시 저장
 - PATCH /user/me/birthday → 세션 사용자의 생년월일 저장(호환성 유지)
 - GET /__routes → 등록된 경로 목록 문자열 배열(디버그)

참고
- `app/main.py`에서 /media를 StaticFiles로 마운트합니다.
- `app/api/routes/images.py`에서 저장 경로와 URL을 동기화했습니다.
 - `app/api/routes/userdata.py`에서 세션 사용자 프로필을 업데이트합니다.

참고: 현재 코드에서 aiomysql/SQLAlchemy를 사용합니다. 만약 실행 시 해당 모듈이 없다는 에러가 나면 아래로 설치 후, 필요 시 `requirements.txt`에 반영하세요.
```powershell
pip install aiomysql sqlalchemy
```

가상환경 비활성화: `deactivate`

VS Code에서 자동으로 .venv를 사용하려면(권장), 워크스페이스의 Python 인터프리터를 `backend/.venv`로 선택하세요. 이 저장소에는 `.vscode/settings.json`을 제공하여 기본 인터프리터가 `backend/.venv`로 지정됩니다.

## 환경 변수 (.env)
`backend/.env` 파일을 만들어 아래 예시를 채워주세요. `app/.env`도 읽히지만, 기본은 프로젝트 루트의 `.env`입니다.
```
# 기본 URL
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5174
STRICT_CORS=0                 # 1이면 FRONTEND_URL만 허용, 기본은 * 허용

# 세션
SESSION_SECRET=change-me
SESSION_COOKIE_NAME=sid       # 옵션

# AI 서비스 (선택)
# 별도의 AI FastAPI를 8600 포트로 띄운 경우, 백엔드가 이 URL로 위임합니다.
AI_SERVICE_URL=http://localhost:8600

# DB (프로젝트 DB 예시 값)
DB_HOST=project-db-cgi.smhrd.com
DB_PORT=3307
DB_USER=cgi_25IS_LI1_p3_3
DB_PASS=smhrd3
DB_NAME=cgi_25IS_LI1_p3_3

# 카카오 OAuth
KAKAO_CLIENT_ID=YOUR_REST_API_KEY
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
KAKAO_SCOPE=profile_nickname,profile_image  # 이메일 요청 제거(계정 이메일 제외)
KAKAO_ADMIN_KEY=YOUR_ADMIN_KEY

# 구글 OAuth (선택)
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

## 실행 (개발 모드)
항상 .venv 활성화 후 아래 둘 중 편한 방법을 사용하세요.

- uvicorn으로 직접 실행
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- 모듈 실행 (권장, 엔트리 고정)
```powershell
python -m app
```

실행 후:
- Swagger UI: http://127.0.0.1:8000/docs
- Redoc: http://127.0.0.1:8000/redoc

## 주요 라우트 요약
- `GET /` → 기본 웰컴 메시지
- `GET /__routes` → 등록된 경로(디버그)
- Auth(Kakao)
	- `GET /auth/kakao/login` → 카카오 로그인으로 리다이렉트
	- `GET /auth/kakao/callback` → 카카오 OAuth 콜백(upsert + 세션)
	- `GET /auth/me` → 세션 기반 사용자 정보
	- `POST /auth/logout` → 로그아웃(세션 clear)
	- `POST /auth/kakao/unlink` → 카카오 연결 해제(관리자 키 필요)
	- `GET /` (posts 라우터 기준) → posts 라우트 작동 확인

### 이미지 생성 위임 API
- `POST /api/image/generate`
  - 요청: `{ name, gender, feature?, options[] }`
  - 동작: `.env`의 `AI_SERVICE_URL`이 설정되면 AI 서버의 `/predict`로 위임하여 data URL을 반환합니다.
  - 미설정/장애 시: 로컬 SVG data URL을 생성하여 반환하는 안전한 폴백을 수행합니다.

주의: `/health` 엔드포인트는 현재 기본 앱에 포함되어 있지 않습니다. 필요하면 `app/main.py`에 간단히 추가하세요.
→ 현재 저장소에는 `/health`가 구현되어 있어 테스트가 통과합니다.

### 사용자 프로필 API
- `PATCH /user/me/profile`
	- 요청: `{ birthday: "YYYY-MM-DD", gender: "남성" | "여성" }`
	- 응답: `{ ok: true, user: { id, birthday, gender } }`
	- 세션 쿠키 필요(Vite 프록시 `/user` 권장)
- `PATCH /user/me/birthday`
	- 요청: `{ birthday: "YYYY-MM-DD" }`
	- 응답: `{ ok: true, user: { id, birthday } }`

검증/예외
- 생년월일은 미래 불가, 연도 1900 미만 불가
- 성별은 "남성" 또는 "여성"만 허용

## CORS/세션 동작
- CORS: `STRICT_CORS=1` 이면 `FRONTEND_URL`만 허용, 아니면 `*` 허용
- 쿠키 세션: `SESSION_SECRET` 필수. 프록시 없이 다른 포트에서 호출 시 SameSite 설정이 필요할 수 있습니다(로컬 개발 환경에 따라 조정).

## 테스트
```powershell
pytest -q
```

참고: `tests/test_health.py`가 포함되어 있습니다. `/health` 엔드포인트를 앱에 추가하지 않았다면 이 테스트는 실패할 수 있습니다.

## 주요 기술 스택
- FastAPI
- Uvicorn (ASGI 서버)
- Pydantic
- aiomysql (비동기 MySQL 커넥션 풀)
- SQLAlchemy (비동기 엔진/세션 선택 사용)
- httpx (외부 API 호출)
- python-dotenv (환경 변수 로딩)
- pytest/pytest-asyncio (테스트)

## 주요 파일 설명
- `app/main.py`: FastAPI 앱 생성, CORS/세션/라우터 등록, MySQL 풀 초기화, `/`, `/__routes`, `/health`
- `app/__main__.py`: `python -m app` 실행 진입점
- `app/api/routes/auth.py`: 인증/로그인/카카오 OAuth, 세션 기반 `/auth/me`, 로그아웃, 언링크
- `app/api/routes/posts.py`: 예시 라우트
- `app/api/models/users.py`: 사용자 upsert/조회 로직(aiomysql)
- `app/api/core/mysql.py`: aiomysql 풀 생성
- `app/api/core/database.py`: SQLAlchemy Async 엔진/세션 (선택 사용)

## 트러블슈팅
- DB 연결 오류: `.env`의 DB_HOST/PORT/USER/PASS/NAME 확인, 방화벽/보안그룹 확인
- OAuth 리다이렉트 오류: `KAKAO_REDIRECT_URI`가 카카오 앱 설정과 일치하는지 확인
- 카카오 이메일 동의가 계속 뜸: `.env`의 `KAKAO_SCOPE`에서 `account_email`을 제거하세요. 백엔드(`app/api/routes/auth.py`)는 안전장치로 scope에 `email` 문자열이 포함되면 자동 제거하여 카카오에 전달하지 않습니다. 또한 카카오 개발자 콘솔의 동의 항목에서 이메일을 미사용으로 설정해야 완전히 제거됩니다.
- 쿠키가 안 실릴 때: CORS 오리진, SameSite, 프론트 호출 방식(프록시 vs 절대경로) 점검
- 401/세션 누락: 브라우저 쿠키 차단 여부, `SESSION_SECRET` 설정 확인

## 기타
- `.env`는 루트(`backend/.env`)와 `app/.env`를 모두 시도해 로드합니다(루트 우선).
- DB 풀은 `app.api.core.mysql.get_mysql_pool()`를 사용합니다(비동기 aiomysql).
- SQLAlchemy를 사용할 경우 `app/api/core/database.py`의 `AsyncSessionLocal`을 활용하세요.

