# AI 서버 (Gemini 이미지 생성)

FastAPI 기반 최소 서빙으로, Google Gemini 이미지 모델을 호출해 PNG를 반환합니다.

구성 요약
```
serving/fastapi_app/main.py    # FastAPI 엔트리 (/health, /predict)
models/imagemodel_gemini.py    # Gemini 호출 및 PNG 표준화
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
$env:AI_MODEL_MODULE = "ai.models.imagemodel_gemini"
$env:AI_MODEL_FUNC   = "generate_image"
$env:AI_REQUIRE_MODEL = "true"
```

실행
```powershell
python -m uvicorn ai.serving.fastapi_app.main:app --host 0.0.0.0 --port 8600 --reload
# Health: http://localhost:8600/health
```
또는 루트 스크립트 사용
```powershell
& ..\scripts\start-ai.ps1
```

API
- POST /predict
  - body: { name, gender, feature?, options: string[] }
  - resp: { ok: true, image: "data:image/png;base64,..." }

비고
- 응답 이미지는 Pillow로 검증·재인코딩되어 브라우저에서 바로 표시 가능한 PNG입니다.
 - Pillow 미설치 시 /predict는 1x1 PNG placeholder로 안전하게 응답합니다. 텍스트 렌더링이 필요하면 Pillow 설치 권장.
 - .env 파일은 리포지토리 루트에 위치하면 자동으로 로드됩니다.
 - 백엔드가 `AI_SERVICE_URL`로 이 서버를 호출하여 `/api/image/generate`를 제공합니다.
