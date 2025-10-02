## Frontend

### 개요
이 디렉토리는 FastAPI 백엔드(`/backend`)와 통신하는 React(Vite) 기반 프론트엔드입니다. 초기 버전은 백엔드 헬스 체크(`/health`) 호출 예제를 포함합니다.

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
```
cd frontend
cp .env.example .env              # 필요 시 수정
npm install
npm run dev
```
브라우저: http://localhost:5173

백엔드도 실행 중이어야 헬스 호출이 성공합니다 (기본: http://localhost:8000).

### 환경변수
`.env` (Vite 규칙: `VITE_` prefix 필요)
```
VITE_API_BASE_URL=http://localhost:8000
```

### 헬스 호출 로직
`src/api/client.js` → `getHealth()` → `/health` GET 요청
`src/hooks/useHealth.js` → 로딩/에러/데이터 상태 관리
`src/components/HealthStatus.jsx` → UI 표시 & 새로고침 버튼

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
초기 React 프론트엔드 스캐폴드 완료.