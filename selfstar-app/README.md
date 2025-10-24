# SelfStar 프로젝트 통합 안내 (AI · Backend · Frontend)

Windows(PowerShell) 기준 가이드입니다. Docker 사용을 권장합니다. 이 문서는 최신 챗/이미지/인스타 게시 플로우 기준으로 정리되어 있습니다.

## 구성 개요
- AI 서버: Gemini 이미지 생성 FastAPI 서빙 (`ai/`)
- 백엔드 API: 인증, 챗 이미지 생성 위임, 정적 파일(`/files`) 서빙, Instagram 게시 (`backend/`)
- 프론트엔드: React + Vite UI (Chat Studio 포함) (`frontend/`)

포트
- AI: 8600
- Backend: 8000
- Frontend: 5174

주요 기능(요약)
- Chat Studio에서 페르소나로 이미지 생성 → 프리뷰 관리(여러 장) → Instagram 업로드
- 생성 이미지는 로컬 `backend/app/storage`에 저장되고 `/files`로 정적 서빙(날짜/UUID 파일명)
- 데이터 URI도 `/files/ensure_public`로 저장/승격 후 절대 URL을 획득하여 IG 게시에 사용
- Instagram Graph 게시: 페르소나 단위 OAuth/계정 매핑 완료 후 `/instagram/publish` 호출

---

## 빠른 시작 (Docker 권장)

사전 준비
- Docker Desktop 설치 (WSL2 필요 시 관리자 PowerShell: `wsl --install; wsl --update`)

1) 환경 변수 준비(서비스별)
- `backend/.env` 예시
  ```ini
  SESSION_SECRET=change-me
  BACKEND_URL=http://localhost:8000
  FRONTEND_URL=http://localhost:5174
  AI_SERVICE_URL=http://ai:8600

  # Meta/Instagram OAuth
  META_APP_ID=
  META_APP_SECRET=
  META_REDIRECT_URI=http://localhost:8000/oauth/instagram/callback
  META_SCOPES=pages_show_list,instagram_basic,instagram_content_publish

  # Kakao OAuth (필요 시)
  KAKAO_CLIENT_ID=
  KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
  KAKAO_SCOPE=profile_nickname,profile_image
  KAKAO_ADMIN_KEY=
  ```
- `frontend/.env` 예시
  ```ini
  VITE_API_BASE=http://localhost:8000
  ```
- `ai/.env` 예시
  ```ini
  GOOGLE_API_KEY=<YOUR_GOOGLE_GENAI_KEY>
  AI_REQUIRE_MODEL=1
  GEMINI_IMAGE_MODEL=gemini-2.5-flash-image-preview
  ```

2) 실행
```powershell
docker compose up -d
```

개발용 핫리로드
```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

3) 접속
- 프론트: http://localhost:5174
- 백엔드: http://localhost:8000 (health: `/health`)
- AI: http://localhost:8600 (health: `/health`)

4) IG 로컬 테스트(중요)
- Instagram Graph는 공개 HTTPS URL만 허용합니다. 로컬 개발 시 ngrok 등으로 백엔드를 노출하고 `BACKEND_URL`을 해당 https로 설정하세요.
  - 예: `BACKEND_URL=https://abcd-1234.ngrok-free.app`
  - 프론트는 여전히 http://localhost:5174 에서 개발 가능하나, 업로드 시 백엔드가 만든 절대 URL이 공개여야 합니다.

---

## 아키텍처와 흐름

1) 이미지 생성
- 프론트(`/src/page/Chat.jsx`) → `POST /chat/image`
- 백엔드가 AI로 위임(기본 `AI_SERVICE_URL`) → AI가 data:image/*;base64 응답
- 백엔드는 data URI를 `backend/app/storage/YYYYMMDD/uuid.ext`로 저장하고 DB 기록(선택) 후 `{ path, url }` 포함 응답

2) 프리뷰/게시
- 프리뷰는 데이터 URI/URL 혼재 가능
- 인스타 업로드 시 데이터 URI면 `POST /files/ensure_public`로 파일 저장 후 `BACKEND_URL/files/...` 절대 URL 획득 → `POST /instagram/publish`

3) 정적 서빙
- `/files` → `backend/app/storage`를 정적 서빙 (미디어 `/media`와 분리)

주요 엔드포인트(Backend)
- `POST /chat/image`: { persona_num, user_text, ls_session_id?, style_img? } → { ok, image, stored? }
- `POST /chat/session/start|end`: LangSmith 등 세션 구분용(선택)
- `POST /files/ensure_public`: { image }(data URI | /files/상대경로 | http URL) → { ok, url, path? }
- `POST /instagram/publish`: { persona_num, image_url(절대), caption } → IG 게시

AI 서비스(기본)
- `GET /health`
- `POST /predict` (레거시) 또는 `POST /chat/image` (권장)
  - 현재 리포에는 /predict가 기본 포함되어 있습니다. /chat/image를 사용하는 경우 AI에 해당 라우트가 있어야 합니다.

프론트엔드
- Chat Studio(프리뷰/드래그/다중 저장, Instagram 업로드 버튼)
- API 호출: `/chat/image`, `/files/ensure_public`, `/instagram/publish`

---

## 수동 실행 (Docker 미사용)

1) AI
```powershell
cd ai; python -m venv .venv; . .venv/Scripts/Activate.ps1; pip install -r requirements.txt
$env:GOOGLE_API_KEY = "<YOUR_KEY>"; $env:AI_REQUIRE_MODEL = "1"
python -m uvicorn ai.serving.fastapi_app.main:app --host 0.0.0.0 --port 8600 --reload
```

2) Backend
```powershell
cd backend; python -m venv .venv; . .venv/Scripts/Activate.ps1; pip install -r requirements.txt
$env:AI_SERVICE_URL = "http://localhost:8600"; $env:BACKEND_URL = "http://localhost:8000"; $env:FRONTEND_URL = "http://localhost:5174"; $env:SESSION_SECRET = "selfstar-secret"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3) Frontend
```powershell
cd frontend; npm ci; npm run dev -- --port 5174
```

---

## 환경 변수 요약
- 공통
  - `BACKEND_URL`, `FRONTEND_URL`
- Backend
  - `SESSION_SECRET`, `AI_SERVICE_URL`, `FILES_ROOT`(선택), `MEDIA_ROOT`(선택)
  - Instagram: `META_APP_ID`, `META_APP_SECRET`, `META_REDIRECT_URI`, `META_SCOPES=pages_show_list,instagram_basic,instagram_content_publish`
- AI
  - `GOOGLE_API_KEY`, `GEMINI_IMAGE_MODEL`, `AI_REQUIRE_MODEL`
- Frontend
  - `VITE_API_BASE`

트러블슈팅
- 포트 충돌(WinError 10048)
  ```powershell
  Get-NetTCPConnection -LocalPort 5174,8000,8600 -State Listen
  Stop-Process -Id <PID> -Force
  ```
- Instagram 업로드 400/403
  - `META_SCOPES`에 `instagram_content_publish` 포함 여부, 페르소나 OAuth/링크 완료 여부 확인
  - `image_url`이 공개 HTTPS URL인지 확인(`/files/ensure_public`을 통해 승격 필요)
- 프리뷰는 있는데 업로드 버튼 비활성화
  - Chat 프리뷰가 비어있지 않으면 버튼이 활성화됩니다. 데이터 URI여도 업로드 시 자동 변환됩니다.

---

## 리포 구조 요약
```
ai/
  serving/fastapi_app/main.py           # FastAPI 앱 엔트리
  serving/fastapi_app/routes/image_model.py    # /health, /predict (Gemini)
backend/
  app/main.py                           # 백엔드 엔트리, /files 정적 서빙 포함
  app/api/routes/chat.py                # /chat/image 등
  app/api/routes/files.py               # /files/ensure_public
  app/api/routes/instagram_publish.py   # /instagram/publish
frontend/
  src/page/Chat.jsx                     # Chat Studio(UI/업로드)
```

문의/기여: 이슈/PR로 제안해주세요.