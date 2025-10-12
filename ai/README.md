# AI

최소 골격만 포함한 AI 디렉토리입니다. 추후 실험/서빙 확장 예정.

## 구조
```
ai/
	.gitignore
	training/
		train.py          # 학습 엔트리 포인트 (placeholder)
	models/
		.gitkeep          # 모델/아티팩트 저장 예정
	serving/
		fastapi_app/
			main.py         # 간단 health 엔드포인트
		vllm_server/
			start_vllm.sh   # vLLM 실행 스크립트 플레이스홀더
	notebooks/
		00_mlflow_init.ipynb   # MLflow 초기 확인 노트북
```

## 이미지 생성 서빙 (Gemini)
`serving/fastapi_app/main.py`는 동적 임포트를 통해 이미지 생성 함수를 호출합니다. 기본 구현은 `ai.models.imagemodel_gemini.generate_image`입니다.

### 환경 변수
- `GOOGLE_API_KEY` (필수)
- `AI_MODEL_MODULE` (기본값: `ai.models.imagemodel_gemini`)
- `AI_MODEL_FUNC` (기본값: `generate_image`)
- `GEMINI_IMAGE_MODEL` (기본값: `gemini-2.5-flash-image-preview`)

Windows PowerShell에서 일시 설정 예:
```powershell
$env:GOOGLE_API_KEY = "<YOUR_KEY>"
$env:AI_MODEL_MODULE = "ai.models.imagemodel_gemini"; $env:AI_MODEL_FUNC = "generate_image"
```

### 실행
```powershell
pip install -r ai/requirements.txt
python -m uvicorn ai.serving.fastapi_app.main:app --host 0.0.0.0 --port 8600 --reload
```

### API
- `GET /health` → 서비스 상태
- `POST /predict` → 입력(name, gender, feature, options)으로 PNG data URL 반환

요청 바디 예시:
```json
{ "name": "홍길동", "gender": "남성", "feature": "짧은머리", "options": ["안경"] }
```

응답 예시:
```json
{ "ok": true, "image": "data:image/png;base64,..." }
```

## MLflow 최소 사용법
1. 의존성 설치 (루트에서):
```
pip install -r ai/requirements.txt
```
2. 로컬 추적 디렉토리(기본): `./ai/mlruns` (이미 .gitignore 처리)
3. 테스트 실행:
```
python ai/training/train.py
```
4. UI 띄우기 (선택):
```
mlflow ui --backend-store-uri ./ai/mlruns --port 5500
```
브라우저: http://localhost:5500

노트북 `notebooks/00_mlflow_init.ipynb` 에서도 동일한 방식으로 run/metric 로깅 예제를 확인할 수 있습니다.
