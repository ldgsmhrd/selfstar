# selfstar 프로젝트 통합 안내

본 프로젝트는 AI, 백엔드(FastAPI), 프론트엔드(React+Vite)로 구성된 풀스택 서비스입니다. 각 서비스별 폴더 구조, 실행 방법, 환경설정, 주요 포트, 개발 체크리스트를 아래에 상세히 안내합니다.

## 전체 폴더 구조

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

---

## 개발 체크리스트 및 참고

- 프론트엔드는 반드시 `5174` 포트로 실행 (Vite 기본값은 5173이므로 반드시 `npm run dev -- --port 5174` 사용)
- 카카오 OAuth 이메일 동의창이 뜨지 않도록 `.env`의 `KAKAO_SCOPE`에 `account_email`이 포함되지 않도록 설정
- 백엔드/프론트엔드 모두 환경변수 예시 파일 제공 (`.env.example`)
- 각 서비스별 README에 상세 실행법, 환경설정, 폴더 구조 예시 포함
- AI 폴더는 추후 모델/서빙/MLflow/vLLM 등 확장 예정

---

## 문의 및 기여

이슈/PR/문의는 GitHub 저장소를 통해 남겨주세요.