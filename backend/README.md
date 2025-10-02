# backend

### 구조
```
backend/
	requirements.txt
	app/
		main.py            # FastAPI 앱 팩토리 및 엔트리
		core/              # 설정, 로깅 등 코어 유틸
		api/routes/        # 라우트 모음 (health 등)
		models/            # ORM 모델 (향후 확장)
		schemas/           # Pydantic 스키마
	tests/               # Pytest 테스트
	.env.example         # 환경변수 예시
```

### 설치 & 실행
Python 3.11+ 권장.

#### 0. (항상) 가상환경 생성 및 활성화
운영체제 별로 명령을 구분했습니다. (프로젝트 루트: `backend/`)

리눅스 / macOS (bash/zsh):
```
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows (PowerShell):
```
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Windows (CMD):
```
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
```

비활성화: `deactivate`

환경 재현(클린 재설치) 예:
```
rm -rf .venv  # Windows: rmdir /s /q .venv
python -m venv .venv
source .venv/bin/activate  # (Windows는 위 구분 참고)
pip install -r requirements.txt
```

IDE 통합 (VS Code): `.venv` 생성 후 하단 인터프리터 선택 → `.venv/bin/python` 지정.
`requirements.txt` 변경 시 동료는 `pip install -r requirements.txt` 한 번으로 동기화.
패키지 추가 정책(권장):
1) `pip install <pkg>`
2) 테스트
3) `pip freeze | grep -i <pkg>` 결과를 `requirements.txt`에 적절히 반영(이미 있으면 버전만 갱신 고려)
4) 커밋 메시지 예: `chore(backend): add <pkg> dependency`
5) 필요 시 `pytest -q` 로 회귀 확인

활성화된 상태에서만 애플리케이션/pytest를 실행하세요.

#### 1. 의존성 설치
```
pip install -r requirements.txt
```
새 패키지 추가 시: `pip install <pkg>` 후 `pip freeze | grep <pkg>` 로 버전 확인, 필요 시 `requirements.txt`에 고정.

#### 2. 로컬 실행 (자동 리로드)
```
uvicorn app.main:app --reload --port 8000
```
브라우저로 http://127.0.0.1:8000/docs 확인 (Swagger UI)

#### 3. 헬스체크
```
curl http://localhost:8000/health
```

### 환경변수
`.env` 파일을 루트(`backend/`)에 만들고 아래 예시 사용:
```
cp .env.example .env
```

### 테스트
```
pytest -q
```

### 다음 확장 아이디어
- 데이터베이스(SQLAlchemy) 연결 및 `models/` 구현
- 인증 / JWT
- OpenAPI 보안 스키마 추가
- CI 파이프라인에서 테스트 자동화

---
초기 FastAPI 백엔드 스캐폴드가 준비되었습니다.

### 진행된 초기 세팅 요약
- FastAPI 기본 앱 팩토리 (`app/main.py`) 및 CORS 설정
- 환경설정 로딩 (`app/core/config.py`, `.env.example`)
- 로깅 유틸 (`app/core/logging.py`)
- 헬스 체크 라우터 (`/health`) + 테스트 (`tests/test_health.py`)
- Pydantic 스키마 폴더 (`app/schemas/`) 및 `HealthResponse` 예시
- 모델/ORM 확장용 베이스 파일 자리 마련 (`app/models/base.py`)
- 패키지 종속성 명시 (`requirements.txt`)
- README 설치/실행/테스트 가이드 정리 및 가상환경 사용 정책 명시

추가 요구나 확장 사항이 생기면 이 섹션에 계속 누적 정리하세요.

