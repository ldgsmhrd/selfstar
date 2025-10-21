# Backend (FastAPI)

> Docker로 실행 중이라면 루트 `README.md`의 "Docker로 실행 (권장)" 섹션을 우선 참고하세요. 이 문서는 로컬(vENV) 개발 대안을 포함합니다.

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
- POST /api/images → { ok, image: dataURI, url?: /media/xxx.png }
	- AI로 위임 성공 시 data URI를 디코드해 파일 저장 후 url도 함께 반환
- 정적 /media → 이미지 파일 제공
 - GET /auth/me → 세션 사용자(동의 필요 여부 포함: needs_consent)
 - PUT /users/me/profile → 세션 사용자의 성별+생년월일 동시 저장
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
`backend/.env` 파일을 만들어 아래 예시를 채워주세요. 예시는 `backend/.env.example`을 참고하세요. (서비스별 분리: 루트 `.env`는 더 이상 사용하지 않습니다)
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

# Instagram Graph API (개발용)
IG_LONG_LIVED_USER_TOKEN=

# Meta App (Instagram OAuth)
META_APP_ID=
META_APP_SECRET=
# 로컬 개발 시 http://localhost:8000/oauth/instagram/callback 을 사용하세요.
META_REDIRECT_URI=http://localhost:8000/oauth/instagram/callback
# 기본 스코프: 페이지/IG 조회에 필요한 최소 권한
META_SCOPES=pages_show_list,instagram_basic
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
- `POST /api/images`
  - 요청: `{ name, gender, feature?, options[] }`
  - 동작: `.env`의 `AI_SERVICE_URL`이 설정되면 AI 서버의 `/predict`로 위임하여 data URL을 반환합니다.
  - 미설정/장애 시: 로컬 SVG data URL을 생성하여 반환하는 안전한 폴백을 수행합니다.

주의: `/health` 엔드포인트는 현재 기본 앱에 포함되어 있지 않습니다. 필요하면 `app/main.py`에 간단히 추가하세요.
→ 현재 저장소에는 `/health`가 구현되어 있어 테스트가 통과합니다.

### 사용자 프로필 API
- `PUT /users/me/profile`
	- 요청: `{ birthday: "YYYY-MM-DD", gender: "남성" | "여성" }`
	- 응답: `{ ok: true, user: { id, birthday, gender } }`
	- 세션 쿠키 필요(Vite 프록시 `/users` 권장)

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
- DB 풀은 `app.api.core.mysql.get_mysql_pool()`를 사용합니다(비동기 aiomysql).
- SQLAlchemy를 사용할 경우 `app/api/core/database.py`의 `AsyncSessionLocal`을 활용하세요.


### Instagram 연동(설계/초안)
- `GET /oauth/instagram/start` → Meta OAuth 시작(redirect)
- `GET /oauth/instagram/callback` → 코드 교환/장기 토큰 저장
- `GET /oauth/instagram/accounts` → 페르소나 전용 Page/IG 비즈니스 계정 목록 반환 (persona_num 또는 persona_id 필수)
- `POST /oauth/instagram/link` → 특정 persona_id와 IG 계정 매핑
- `POST /oauth/instagram/unlink` → 매핑 제거

DB 권장 구조(요약)
- ss_instagram_connector(user_id, long_lived_user_token, expires_at) [개발 편의/레거시]
	Instagram 연동은 ss_persona 테이블에서 관리합니다.
	- 컬럼: ig_user_id, ig_username, fb_page_id, ig_linked_at
	- 또한 persona_parameters JSON 내 instagram 섹션에도 동기화하여 하위 호환/확장에 대비합니다.

개발용 환경 변수(테스트 토큰)
- `IG_LONG_LIVED_USER_TOKEN`: 장기 사용자 토큰(서버 환경변수로만 사용, 로그에 출력 금지)

## Instagram 연동 가이드(실전)

1) Meta 개발자 앱 만들기
- https://developers.facebook.com → 내 앱 → 새 앱 만들기 → 앱 유형(업무/기타) 선택 → 앱 이름/이메일 기입
- 앱 대시보드에서 제품 추가 → “Facebook 로그인” + “Instagram Graph API” 추가

2) OAuth 설정(필수)
- Facebook 로그인 → 설정 → 유효한 OAuth 리디렉션 URI에 백엔드 콜백 주소 추가
	- 예) 개발용: http://localhost:8000/oauth/instagram/callback
- 앱 ID/앱 시크릿을 복사해 `backend/.env`의 `META_APP_ID`, `META_APP_SECRET`에 채웁니다.
- `META_REDIRECT_URI`에 동일한 콜백 URL을 넣습니다.
- 권한(스코프): `pages_show_list, instagram_basic`부터 시작하세요. 추가 권한은 게시/댓글 자동화 시 필요합니다.

3) 로컬 개발 콜백/리디렉션 설정
- 로컬 개발은 ngrok 없이 진행합니다. 아래 URL을 사용하세요:
	- BACKEND_URL=http://localhost:8000
	- META_REDIRECT_URI=http://localhost:8000/oauth/instagram/callback
- Meta 앱 콘솔의 OAuth 리디렉션 URI에도 동일 콜백을 등록하세요.

4) 로그인/연결 흐름
- 백엔드가 실행 중이어야 합니다(uvicorn 또는 Docker).
- 프론트 마이페이지 → “연동관리” → “다시 인증”을 클릭하면 `/oauth/instagram/start`로 이동합니다.
- Meta 로그인 → 권한 승인 → 콜백 `/oauth/instagram/callback` → 서버가 Long-Lived User Token 저장 → 프론트 `/mypage?ig=connected`로 리다이렉트
- 같은 사용자가 `/oauth/instagram/accounts`로 페이지/IG 비즈니스 계정 목록을 조회할 수 있습니다. 이때 반드시 페르소나를 지정해야 하며 해당 페르소나의 OAuth 토큰이 사용됩니다.
- 선택한 계정은 `/oauth/instagram/link`로 persona와 매핑하세요.

5) 권한/검수(프로덕션)
- 개발 모드에서 테스트 역할(관리자/개발자/테스터)만 로그인 허용됩니다.
- 실제 사용자 대상 출시 시, 앱 모드를 Live로 전환하고 필요한 권한에 대해 검수를 받아야 합니다.
- 게시 자동화까지 필요하면 ‘instagram_content_publish’, ‘pages_manage_posts’ 등 추가 권한이 요구됩니다. 권한 신청 사유/동영상/테스트계정 제공 필요.

트러블슈팅
- redirect_uri mismatch: 백엔드 .env의 META_REDIRECT_URI와 Meta 콘솔 등록 값이 정확히 일치하는지 확인
- code exchange 실패: 앱 시크릿/앱 ID/redirect_uri 값 점검. 개발 환경에서는 http://localhost:8000 콜백을 사용합니다.
- accounts API 500: 서버에 사용자 토큰이 없으면 IG_LONG_LIVED_USER_TOKEN로 폴백합니다. 둘 다 없으면 500(server_token_missing)

## Instagram 토큰 저장 정책(중요)

- 이제 Instagram OAuth 토큰은 페르소나 단위로만 저장·사용합니다.
- `/oauth/instagram/callback`은 서명된 state에서 해석된 persona가 없으면 400(persona_required)을 반환합니다.
- `/oauth/instagram/accounts` 호출 시에도 persona 지정이 필수입니다. 지정된 페르소나의 토큰이 없으면 401(persona_oauth_required).
- 과거 사용자 단위 토큰 테이블(`ss_instagram_connector`)은 개발 중 디버그/마이그레이션용으로만 유지합니다. 실제 런타임 경로는 `ss_instagram_connector_persona(user_id, user_persona_num, ...)`에만 의존합니다.


