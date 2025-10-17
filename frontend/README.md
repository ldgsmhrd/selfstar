# Frontend (React + Vite)

역할
- 이미지 생성 UI 및 결과 표시
- 개발 중에는 Vite dev server(5174)로 동작하며 `/auth`, `/api`, `/media`는 백엔드(8000)로 프록시됨

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
- `vite.config.js`에 `/auth`, `/api`, `/media`, `/user` → `http://localhost:8000` 프록시가 설정되어 있습니다.
	- `/user`는 세션 쿠키가 실리는 동일 오리진 호출을 위해 필요합니다.

이미지 표시 로직
- 백엔드가 반환하는 `url`이 있으면 우선 사용: `<img src="/media/xxx.png" />`
- 없을 때는 data URI를 fallback으로 사용
이 디렉토리는 FastAPI 백엔드(`/backend`)와 통신하는 React(Vite) 기반 프론트엔드입니다. 초기 버전은 백엔드 헬스 체크(`/health`) 호출 예제를 포함합니다.

온보딩(Consent → UserSetup)
마이페이지 업데이트
- 상단 요약 카드에 현재 페르소나(이미지/이름) 표시, “프로필 교체하기” 모달에서 이미지/이름을 보고 선택 가능(`/personas/me` 기반)
- 연동 관리 모달에 “인스타 연동 하기” 버튼 추가(`/oauth/instagram/start`). 콜백 후 `/oauth/instagram/accounts`로 목록 조회하여 페르소나에 매핑하도록 확장 가능

- 로그인/회원가입 후 백엔드 `/auth/me`의 `needs_consent`가 true면 `/consent` → `/setup`으로 진행합니다.
- `UserSetup.jsx`에서 성별과 생년월일을 수집하고 `PATCH /user/me/profile`로 동시 저장합니다.
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
		# Frontend (React + Vite)

		> Docker로 실행 중이라면 루트 `README.md`의 "Docker로 실행 (권장)" 섹션을 먼저 참고하세요. 이 문서는 로컬(dev server) 대안을 포함합니다.

		역할
		- 이미지 생성 UI 및 결과 표시
		- 개발 중에는 Vite dev server(5174)로 동작하며 `/auth`, `/api`, `/media`는 백엔드(8000)로 프록시됨

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
		- `vite.config.js`에 `/auth`, `/api`, `/media`, `/users` → `http://localhost:8000` 프록시가 설정되어 있습니다.

		이미지 표시 로직
		- 백엔드가 반환하는 `url`이 있으면 우선 사용: `<img src="/media/xxx.png" />`
		- 없을 때는 data URI를 fallback으로 사용
		이 디렉토리는 FastAPI 백엔드(`/backend`)와 통신하는 React(Vite) 기반 프론트엔드입니다. 초기 버전에는 백엔드 헬스 체크(`/health`) 호출 예제를 포함합니다.

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

		# Kakao OAuth (프론트는 보통 백엔드 리다이렉트만 사용)
		KAKAO_CLIENT_ID=your-kakao-rest-api-key
		KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback
		KAKAO_SCOPE=profile_nickname,profile_image  # 이메일 요청 제외

		# Google OAuth (리다이렉트는 백엔드에서 처리)
		# 보통 프론트는 백엔드의 /auth/google/login 링크만 사용합니다.
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

		### 카카오 이메일 동의 차단
		- 이메일 권한을 사용하지 않으려면 `.env`의 `KAKAO_SCOPE`에서 `account_email`을 제거하세요.
		- 프론트는 백엔드의 `/auth/kakao`(또는 `/auth/kakao/login`)로만 이동하므로 추가 코드는 필요 없습니다.
		- 백엔드에서 scope 내 `email` 문자열은 안전장치로 필터링되어 카카오에 전달되지 않습니다.
		- 카카오 개발자 콘솔에서도 이메일 동의 항목을 미사용으로 설정해야 동의창에서 완전히 사라집니다.

		### 추후 확장 아이디어
		- 전역 상태 (Zustand, Recoil, Redux Toolkit 등)
		- 다국어(i18n)
		- 오류 경계(Error Boundary)
		- 라우팅 (React Router)
		- 인증 흐름 (로그인, 토큰 저장)
		- 테스트 (Jest + React Testing Library)

		---
		초기 React 프론트엔드 스캐폴드 완료. 현재 백엔드 `/auth` 및 `/api`와 연동되어 동작합니다.