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

## 다음 확장 아이디어
- MLflow 추적/모델 레지스트리
- vLLM 실제 실행 커맨드 & Dockerfile
- features / data / config 디렉토리 추가
- 모델 추론 API (/predict, /llm/chat)

필요 시 확장 요청 주세요.

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
