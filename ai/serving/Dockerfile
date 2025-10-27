FROM python:3.11-slim

WORKDIR /app

# Install build deps for Pillow if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-serving.txt .
RUN pip install --upgrade pip && pip install -r requirements-serving.txt

COPY serving/fastapi_app ./ai/serving/fastapi_app

EXPOSE 8600

CMD ["uvicorn", "ai.serving.fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8600"]
