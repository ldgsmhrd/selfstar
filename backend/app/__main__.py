from app.main import app

if __name__ == "__main__":
    import uvicorn
    # 개발용 로컬 실행 진입점
    uvicorn.run(app, host="0.0.0.0", port=8000)
