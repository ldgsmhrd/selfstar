# selfstar 프로젝트 통합 안내

SelfStar.AI Mono‑Repo (AI · Backend · Frontend)

이 레포는 세 부분으로 구성된 모노레포입니다.
- AI 서버: 이미지 생성(제미나이) FastAPI 서빙 [`ai/`]
- 백엔드 API: 인증/이미지 생성 위임/정적 미디어 서빙 [`backend/`]
- 프론트엔드: React + Vite UI [`frontend/`]

아래 가이드는 Windows(PowerShell) 기준으로 작성되어 있습니다.

필수 요구사항
- Python 3.12+ (AI, Backend)
- Node.js 18+ (Frontend)
- Google API Key (Gemini 이미지 생성)

포트 사용
- AI: 8600
- Backend: 8000
- Frontend (Vite): 5174

빠른 시작(Windows PowerShell)
- 전체 실행: `scripts/start-all.ps1`
- 개별 실행: `scripts/start-backend.ps1`, `scripts/start-frontend.ps1`, `scripts/start-ai.ps1`
- 헬스 체크: `scripts/check-health.ps1`
- 이미지 생성 테스트: `scripts/test-generate.ps1`

예시
```powershell
& .\scripts\start-all.ps1
# 백엔드:8000, AI:8600, 프론트:5174 동시에 기동
```

레포 구조(요약)
```
ai/
  serving/fastapi_app/main.py    # AI FastAPI 서버 (uvicorn으로 8600)
  models/imagemodel_gemini.py    # Gemini 이미지 모델 호출
  requirements.txt               # AI 의존성
backend/
  app/main.py                    # Backend FastAPI 엔트리(8000)
  app/api/routes/images.py       # /api/image/generate -> AI에 위임 후 /media 저장
  app/api/routes/userdata.py     # /user/me/profile, /user/me/birthday (세션 사용자 정보 업데이트)
  requirements.txt               # Backend 의존성
frontend/
  src/page/App.jsx               # 메인 화면: 이미지 생성/표시
  vite.config.js                 # /auth, /api, /media, /user 프록시 → :8000 (세션 쿠키 유지)
```

설치 및 실행 (Windows, PowerShell)
1) AI 서버
```
cd ai
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt

# 환경 변수 (PowerShell):
$env:GOOGLE_API_KEY = "<YOUR_API_KEY>"
$env:AI_MODEL_MODULE = "ai.models.imagemodel_gemini"
$env:AI_MODEL_FUNC   = "generate_image"
$env:AI_REQUIRE_MODEL = "true"  # 제미나이 강제, 폴백 금지

python -m uvicorn ai.serving.fastapi_app.main:app --host 0.0.0.0 --port 8600 --reload
# Health: http://localhost:8600/health
# 생성:  POST http://localhost:8600/predict
```

2) Backend
```
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt

# .env 또는 환경 변수 설정
$env:AI_SERVICE_URL = "http://localhost:8600"
$env:BACKEND_URL    = "http://localhost:8000"
$env:FRONTEND_URL   = "http://localhost:5174"
$env:SESSION_SECRET = "selfstar-secret"
# 미디어 저장 경로(선택): 기본은 backend/app/media
# $env:MEDIA_ROOT = "C:\\path\\to\\media"

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Health: http://localhost:8000/health
# 이미지 생성(프록시): POST http://localhost:8000/api/image/generate
# 저장된 파일: http://localhost:8000/media/<파일명>
```

3) Frontend
```
cd frontend
npm ci
npm run dev
# http://localhost:5174
```

동작 원리 (이미지 생성 흐름)
1) 프론트: /api/image/generate 요청 → 백엔드
2) 백엔드: AI 서버(/predict)에 위임
3) AI: 제미나이 호출 → 이미지 바이트 확보 후 PNG로 표준화하여 data URI 반환
4) 백엔드: data URI를 디코드해 app/media에 저장하고 "url"(예: /media/xxx.png)과 함께 응답
5) 프론트: 응답의 url이 있으면 우선 사용하여 <img src="/media/...">로 표시

중요 환경 변수
- GOOGLE_API_KEY: Gemini API Key
- AI_MODEL_MODULE, AI_MODEL_FUNC: 동적 모델 로딩(기본: 제미나이)
- AI_REQUIRE_MODEL=true: 폴백 비활성화(모델 필수)
- AI_SERVICE_URL: 백엔드가 위임할 AI 서버 URL
- BACKEND_URL, FRONTEND_URL: CORS/리다이렉트 등에 사용
- MEDIA_ROOT: 백엔드에서 이미지 저장 디렉터리(기본: backend/app/media)

문제 해결 가이드
- 포트 충돌(WinError 10048):
  ```powershell
  Get-NetTCPConnection -LocalPort 8000,8600,5174 -State Listen
  # PID 확인 후 종료
  Stop-Process -Id <PID> -Force
  ```
- 제미나이 키 누락: AI 서버 로그에 GOOGLE_API_KEY 경고 → 환경 변수 확인
- 프론트에서 이미지가 안 보일 때:
  - /api/image/generate 응답에 "url" 포함 여부 확인
  - /media/xxx.png 요청이 200인지 확인
  - 백엔드 /media 마운트가 올바른지(backend/app/main.py)와 저장 경로 일치 여부(images.py)를 확인

테스트
```powershell
$body = '{"name":"이빛나","gender":"여","feature":"귀여운 이미지","options":["안경"]}'
Invoke-RestMethod -Uri http://localhost:8000/api/image/generate -Method POST -Headers @{'Content-Type'='application/json'} -Body $body | ConvertTo-Json -Depth 3
```

PR/커밋 규칙(예시)
- 브랜치: docs/readme-stack-setup
- 커밋 메시지: "docs: AI/Backend/Frontend 설치·실행 가이드 및 /media 서빙 문서화"
- PR 제목: "Docs: 모노레포 운영 가이드 정리(AI/BE/FE)"
- PR 본문: 변경 요약, 실행 방법, 검증 방법, 호환성 메모, 스크린샷(선택)

라이선스
- 프로젝트 내 표기된 라이선스를 따릅니다.

```
selfstar/
│
├── ai/           # AI 모델 학습, 서빙, MLflow 등
├── backend/      # FastAPI 기반 REST API 서버
├── frontend/     # React(Vite) 기반 웹 프론트엔드
└── README.md     # 통합 안내문서
```

---

## 1. 프론트엔드 (frontend)

- **기술스택:** React(Vite), TailwindCSS
- **실행 포트:** 반드시 `5174` (고정)
- **주요 경로:**
  - `src/` : 주요 컴포넌트, API 클라이언트, hooks 등
  - `public/` : 정적 파일
- **환경변수:** `.env` (VITE_ prefix 필수)

### 실행 방법
```bash
cd frontend
cp .env.example .env   # 필요시 환경변수 수정
npm install
npm run dev -- --port 5174
```
웹 브라우저에서 [http://localhost:5174](http://localhost:5174) 접속

### 환경변수 예시
```
VITE_API_BASE_URL=http://localhost:8000
KAKAO_CLIENT_ID=your-kakao-rest-api-key
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
KAKAO_SCOPE=profile_nickname,profile_image
```

---

## 2. 백엔드 (backend)

- **기술스택:** Python 3.12+, FastAPI, MySQL
- **실행 포트:** 8000
- **주요 경로:**
  - `app/` : FastAPI 앱, 라우트, DB, 모델, 스키마 등
  - `requirements.txt` : 의존성 목록
  - `.env.example` : 환경변수 예시

### 실행 방법
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API 서버 [http://localhost:8000](http://localhost:8000)

### 환경변수 예시
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=youruser
MYSQL_PASSWORD=yourpassword
MYSQL_DATABASE=yourdb
KAKAO_CLIENT_ID=your-kakao-rest-api-key
KAKAO_SCOPE=profile_nickname,profile_image
```

---

## 3. AI (ai)

- **기술스택:** Python, MLflow, vLLM
- **주요 경로:**
  - `training/` : 모델 학습 스크립트
  - `models/` : 모델/아티팩트 저장
  - `serving/` : FastAPI 앱, vLLM 서버 스크립트
  - `notebooks/` : MLflow 초기화 노트북

### AI FastAPI Serving (Gemini 이미지 생성)
Gemini 기반의 이미지 생성 모델을 FastAPI로 서빙합니다. 동적 임포트로 모델 함수를 선택합니다.

- 기본 엔드포인트:
  - `GET /health` → `{ status: "ok", service: "ai-serving" }`
  - `POST /predict` → 입력(name, gender, feature, options)으로 이미지 data URL 반환

- 환경변수
  - `GOOGLE_API_KEY` (필수): Google Generative AI API 키
  - `AI_MODEL_MODULE` (선택, 기본 `ai.models.imagemodel_gemini`)
  - `AI_MODEL_FUNC` (선택, 기본 `generate_image`)
  - `GEMINI_IMAGE_MODEL` (선택, 기본 `gemini-2.5-flash-image-preview`)

- 실행 방법 (권장 포트: 8600)
  - 의존성 설치
    ```powershell
    pip install -r ai/requirements.txt
    ```
  - Windows PowerShell에서 환경변수 설정
    - 현재 세션만: ` $env:GOOGLE_API_KEY = "<YOUR_KEY>" `
    - 영구(새 세션부터 적용): ` setx GOOGLE_API_KEY "<YOUR_KEY>" `
    - 선택적으로 동적 모델 지정:
      ```powershell
      $env:AI_MODEL_MODULE = "ai.models.imagemodel_gemini"; $env:AI_MODEL_FUNC = "generate_image"
      ```
  - 개발 서버 실행
    ```powershell
    python -m uvicorn ai.serving.fastapi_app.main:app --host 0.0.0.0 --port 8600 --reload
    ```

- 요청/응답 예시
  - Request (POST /predict)
    ```json
    { "name": "홍길동", "gender": "남성", "feature": "짧은머리", "options": ["안경"] }
    ```
  - Response
    ```json
    { "ok": true, "image": "data:image/png;base64,iVBORw0K..." }
    ```

### MLflow 실행 예시
```bash
pip install -r ai/requirements.txt
mlflow ui --backend-store-uri ./ai/mlruns --port 5500
```
MLflow UI: [http://localhost:5500](http://localhost:5500)

### vLLM 서버 실행 예시
```bash
cd ai/serving/vllm_server
bash start_vllm.sh
```

### 백엔드 연동 (프록시 역할)
백엔드는 `AI_SERVICE_URL`이 설정되면 `/api/image/generate` 요청을 AI 서버의 `/predict`로 위임합니다.

- 예: `AI_SERVICE_URL=http://localhost:8600`
- 엔드포인트: `POST /api/image/generate` → `{ ok: true, image: "data:..." }`

---

## E2E 점검 순서 체크리스트
1) AI 서버 기동
  - `GET http://localhost:8600/health` → 200, `{status:"ok"}`
  - `POST http://localhost:8600/predict` → 200, data URL 포함
2) 백엔드 기동 (`http://localhost:8000`)
  - `.env`에 `AI_SERVICE_URL=http://localhost:8600` 설정
  - `POST http://localhost:8000/api/image/generate` → 200, data URL 포함
3) 프론트엔드 기동 (`http://localhost:5174`)
  - 이미지 생성 UI/호출이 있다면 결과 표시 확인

---

## 개발 체크리스트 및 참고

- 프론트엔드는 반드시 `5174` 포트로 실행 (Vite 기본값은 5173이므로 반드시 `npm run dev -- --port 5174` 사용)
- 카카오 OAuth 이메일 동의창이 뜨지 않도록 `.env`의 `KAKAO_SCOPE`에 `account_email`이 포함되지 않도록 설정
- 백엔드/프론트엔드 모두 환경변수 예시 파일 제공 (`.env.example`)
- 각 서비스별 README에 상세 실행법, 환경설정, 폴더 구조 예시 포함
- AI 폴더는 추후 모델/서빙/MLflow/vLLM 등 확장 예정

### 인증 · 온보딩 흐름(Consent → UserSetup)
1) OAuth 로그인(카카오/구글/네이버) 완료 시 서버 세션에 `user_id` 저장
2) `GET /auth/me` 응답에 `needs_consent` 노출(생일 미설정 또는 신규 가입 등)
3) 프론트는 `/consent` → `/setup`으로 유도하여 프로필 정보 수집
4) `UserSetup`에서 성별+생년월일을 동시 저장: `PATCH /user/me/profile`
  - Vite 프록시 `/user` 경유로 세션 쿠키 포함 호출
  - 성공 시 `/imgcreate`로 이동

주요 엔드포인트(세션 필요)
- `GET /auth/me` → `{ ok, authenticated, user: { id, needs_consent, ... } }`
- `PATCH /user/me/profile` → `{ ok, user: { id, birthday, gender } }`
- `PATCH /user/me/birthday` → `{ ok, user: { id, birthday } }` (이전 버전 호환)

디버깅
- `GET /__routes` → 등록된 경로 문자열 배열(개발용 도우미)

---

## 문의 및 기여

이슈/PR/문의는 GitHub 저장소를 통해 남겨주세요.