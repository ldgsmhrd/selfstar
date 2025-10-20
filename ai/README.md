# AI 서버 (Gemini 이미지 생성)

> Docker로 실행 중이라면 루트 `README.md`의 "Docker로 실행 (권장)" 섹션을 먼저 참고하세요. 이 문서는 로컬 실행 대안을 포함합니다.

FastAPI 기반 최소 서빙으로, Google Gemini 이미지 모델을 호출해 PNG를 반환합니다.

구성 요약
```
serving/fastapi_app/main.py           # FastAPI 앱 엔트리 (라우터 장착)
serving/fastapi_app/routes/image_model.py    # 이미지 생성 라우터 (/health, /predict, Gemini 고정)
requirements.txt               # 서빙 의존성
```

필수 요구사항
- Python 3.12+
- GOOGLE_API_KEY

설치
```powershell
cd ai
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

환경 변수(예시)
```powershell
$env:GOOGLE_API_KEY = "<YOUR_API_KEY>"
$env:AI_REQUIRE_MODEL = "true"
```

실행
```powershell
python -m uvicorn ai.serving.fastapi_app.main:app --host 0.0.0.0 --port 8600 --reload
# Health: http://localhost:8600/health
```

API
- POST /predict
  - body: { name, gender, feature?, options: string[] }
  - resp: { ok: true, image: "data:image/png;base64,..." }

비고
- 응답 이미지는 Pillow로 검증·재인코딩되어 브라우저에서 바로 표시 가능한 PNG입니다.
- .env는 루트 또는 컨테이너 환경변수로 주입 가능합니다.
- 백엔드가 `AI_SERVICE_URL`로 이 서버를 호출하여 `/api/images` 응답에 사용합니다.
