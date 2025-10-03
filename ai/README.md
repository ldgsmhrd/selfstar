# AI (Minimal Scaffold)

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
```

## 다음 확장 아이디어
- MLflow 추적/모델 레지스트리
- vLLM 실제 실행 커맨드 & Dockerfile
- features / data / config 디렉토리 추가
- 모델 추론 API (/predict, /llm/chat)

필요 시 확장 요청 주세요.
