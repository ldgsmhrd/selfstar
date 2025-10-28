# AI 서버 (Gemini 이미지 생성)

FastAPI 기반 서빙으로 Google Gemini 이미지 모델을 호출해 이미지를 생성합니다. 기본으로 `/predict` 엔드포인트가 제공되며, 백엔드 최신 플로우에서는 `/chat/image` 엔드포인트가 있는 AI 서비스를 권장합니다.

구성 요약
```
serving/fastapi_app/main.py           # FastAPI 앱 엔트리 (라우터 장착)
serving/fastapi_app/routes/image_model.py    # 이미지 생성 라우터 (/health, /predict)
requirements.txt               # 서빙 의존성
```

필수 요구사항
- Python 3.12+
- GOOGLE_API_KEY (ai/.env 또는 환경변수로 주입)

설치
```powershell
cd ai
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

환경 변수(예시)
```powershell
# 방법 1) ai/.env 파일 사용 (권장)
#  - ai/.env.example을 복사한 후 값 채우기
#    AI_REQUIRE_MODEL=1
#    GOOGLE_API_KEY=<YOUR_API_KEY>

# 방법 2) 현재 셸에 직접 주입
$env:GOOGLE_API_KEY = "<YOUR_API_KEY>"
$env:AI_REQUIRE_MODEL = "1"
```

실행
```powershell
python -m uvicorn ai.serving.fastapi_app.main:app --host 0.0.0.0 --port 8600 --reload
# Health: http://localhost:8600/health
```

API
- `GET /health` → `{ status: "ok" }`
- `POST /predict` (레거시)
  - body: `{ name, gender, feature?, options: string[] }`
  - resp: `{ ok: true, image: "data:image/png;base64,..." }`
- `POST /chat/image` (권장, 구현되어 있다면)
  - body(예시): `{ user_text, persona_img, persona, ls_session_id?, style_img? }`
  - resp: `{ ok: true, image: "data:image/png;base64,..." }`

비고
- 응답 이미지는 브라우저에서 바로 사용할 수 있는 data URI입니다.
- 백엔드는 `AI_SERVICE_URL`을 이 서비스로 설정하고, 최신 플로우에서는 `/chat/image` 호출을 기대합니다(미구현 시 백엔드가 레거시 경로를 사용할 수 있도록 조정 필요).
