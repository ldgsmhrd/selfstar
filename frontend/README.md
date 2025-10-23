# Frontend (React + Vite)

역할
- Chat Studio(이미지 생성/프리뷰/인스타 업로드)
- 개발 중 Vite dev server(5174) 사용, API는 백엔드(8000)로 프록시

필수 요구사항
- Node.js 18+

설치/실행
```powershell
cd frontend
npm ci
npm run dev -- --port 5174
# http://localhost:5174
```

환경 변수
- `frontend/.env` (Vite 규칙: VITE_ prefix)
	```ini
	VITE_API_BASE=http://localhost:8000
	```

프록시 설정
- `vite.config.js`에 `/auth`, `/api`, `/media`, `/files`, `/users` → `http://localhost:8000` 프록시가 설정되어 있습니다.

주요 화면 (Chat Studio)
- 이미지 생성: `POST /chat/image` (페르소나 번호와 프롬프트, 스타일 이미지 선택 포함)
- 프리뷰: 여러 장 관리, 드래그/더블클릭 추가, 좌우 내비게이션, 삭제
- 업로드: `POST /instagram/publish` (필요 시 선행 `POST /files/ensure_public`로 데이터 URI → 절대 URL 변환)

주의(Instagram 로컬 테스트)
- `BACKEND_URL`이 공개 HTTPS여야 합니다. ngrok 등으로 백엔드를 노출하고 업로드 시 생성되는 절대 URL이 접근 가능해야 합니다.

### 구조
```
frontend/
	package.json
	vite.config.js
	index.html
	.env.example
	src/
		main.jsx
		App.jsx
		api/client.js
		hooks/useHealth.js
		components/HealthStatus.jsx
		page/Chat.jsx

		> Docker로 실행 중이라면 루트 `README.md`의 "Docker로 실행 (권장)" 섹션을 먼저 참고하세요. 이 문서는 로컬(dev server) 대안을 포함합니다.

		역할
		- Chat Studio: 이미지 생성/프리뷰/인스타 업로드

		필수 요구사항
		- Node.js 18+

		설치/실행
		```powershell
		cd frontend
		npm ci
		npm run dev -- --port 5174
		# http://localhost:5174
		```

		프록시 설정
		- `vite.config.js`에 `/auth`, `/api`, `/media`, `/files`, `/users` → `http://localhost:8000` 프록시가 설정되어 있습니다.

		주요 화면
		- `page/Chat.jsx`에서 /chat/image, /files/ensure_public, /instagram/publish 호출

		온보딩(Consent → UserSetup)
		- 로그인/회원가입 후 백엔드 `/auth/me`의 `needs_consent`가 true면 `/consent` → `/setup`으로 진행합니다.
		- `UserSetup.jsx`에서 성별과 생년월일을 수집하고 `PUT /users/me/profile`로 동시 저장합니다.
		- 저장이 성공하면 `/imgcreate`로 이동합니다.

		### 구조
		```
		frontend/
			package.json
			vite.config.js
			index.html
			.env.example
			src/
				main.jsx
				App.jsx
				api/client.js          # fetch 래퍼 (헬스 엔드포인트)
				hooks/useHealth.js     # 헬스 상태 호출 커스텀 훅
				components/HealthStatus.jsx
		```

		### 요구사항
		- Node.js 18+ (LTS 권장)

		### 설치 & 실행
		```bash
		cd frontend
		cp .env.example .env              # 필요 시 수정
		npm install
		npm run dev -- --port 5174        # 반드시 5174 포트로 실행(프록시와 일치)
		```
		브라우저: http://localhost:5174

		백엔드도 실행 중이어야 헬스 호출이 성공합니다 (기본: http://localhost:8000).

		### 환경변수
		`.env` (Vite 규칙: `VITE_` prefix 필수)
		```
		VITE_API_BASE=http://localhost:8000
		```

		### 헬스 호출 로직
		`src/api/client.js` → `getHealth()` → `/health` GET 요청
		`src/hooks/useHealth.js` → 로딩/에러/데이터 상태 관리
		`src/components/HealthStatus.jsx` → UI 표시 & 새로고침 버튼

		### 개발 체크리스트
		- 반드시 5174 포트로 실행 (Vite 기본값 5173 아님)
		- `.env`의 API 주소/카카오 설정 확인
		- 백엔드가 실행 중이어야 정상 동작
		- 카카오 OAuth 이메일 동의창이 뜨지 않도록 `KAKAO_SCOPE`에 `account_email` 미포함
		- 구글 로그인은 `/auth/google/login`으로 이동 → 콜백 후 프론트로 `/?login=success`

		### 빌드 & 미리보기
		```
		npm run build
		npm run preview
		```

		### 추후 확장 아이디어
		- 전역 상태 (Zustand, Recoil, Redux Toolkit 등)
		- 다국어(i18n)
		- 오류 경계(Error Boundary)
		- 라우팅 (React Router)
		- 인증 흐름 (로그인, 토큰 저장)
		- 테스트 (Jest + React Testing Library)

		---
		초기 스캐폴드 + Chat Studio가 포함되어 있으며, 백엔드 /chat 및 /instagram 라우트와 연동됩니다.