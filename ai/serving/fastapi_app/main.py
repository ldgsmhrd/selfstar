from fastapi import FastAPI

app = FastAPI(title="AI Serving Minimal", version="0.0.1")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-serving"}

# Future endpoints:
# - /predict
# - /llm/chat
