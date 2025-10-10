# selfstar

## 카카오 이메일 요청 차단 요약
카카오 OAuth 로그인 시 이메일 동의가 계속 뜬다면 아래를 확인하세요.

- 환경변수에서 이메일 scope 제거
	- `backend/.env` 또는 `backend/.env.example`: `KAKAO_SCOPE=profile_nickname,profile_image`
	- `frontend/.env`(있는 경우): `KAKAO_SCOPE=profile_nickname,profile_image`
- 백엔드 안전장치
	- `backend/app/api/routes/auth.py`에서 scope에 `email` 문자열이 있으면 자동 필터링하여 카카오에 전달하지 않습니다.
- 카카오 개발자 콘솔 설정
	- 동의 항목에서 “이메일”을 미사용으로 설정해야 동의창에서 완전히 사라집니다.

체크리스트
- [ ] `.env`의 `KAKAO_SCOPE`에 `account_email`이 없음
- [ ] 백엔드 재시작 후 로그인 시 이메일 동의 미노출
- [ ] 카카오 콘솔에서 이메일 동의 항목 비활성화