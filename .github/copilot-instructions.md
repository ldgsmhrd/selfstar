# Copilot Instructions for selfstar

This repository is a monorepo with three main components:
- **AI Service** (`ai/`): FastAPI server for Gemini image generation, ML model training, and serving.
- **Backend** (`backend/`): FastAPI REST API for authentication, image generation requests, media storage, and business logic.
- **Frontend** (`frontend/`): React (Vite) web UI for user interaction, image display, and API calls.

## Architecture & Data Flow
- **Frontend** sends image generation requests to `/api/image/generate` (Backend).
- **Backend** proxies requests to AI server `/predict`, receives image data URI, decodes and stores as PNG in `/media`, and returns the URL to Frontend.
- **AI** generates images using Gemini API, returns PNG as data URI.
- All services run independently: AI (8600), Backend (8000), Frontend (5174).

## Developer Workflows
- **Windows PowerShell is the default shell.**
- Use provided PowerShell scripts in `scripts/` for starting services.
- Always create and activate a Python virtual environment (`.venv`) before installing dependencies for AI/Backend.
- Set environment variables using `$env:VAR = "value"` for session or `setx VAR "value"` for persistent.
- For Frontend, use `npm ci` and `npm run dev -- --port 5174`.
- Health endpoints: `/health` for AI and Backend, `/api/image/generate` for image requests.
- Test Backend with `pytest -q` (see `backend/app/tests/test_health.py`).

## Project-Specific Conventions
- **Environment variables** are critical for service configuration (see `.env.example` in each service).
- **AI model selection** via `AI_MODEL_MODULE`, `AI_MODEL_FUNC`, and `GEMINI_IMAGE_MODEL` env vars.
- **Media storage** defaults to `backend/app/media`, override with `MEDIA_ROOT`.
- **Frontend API base URL** must use `VITE_` prefix in `.env`.
- **Kakao OAuth**: Remove `account_email` from `KAKAO_SCOPE` to avoid email consent popup.
- **CORS**: Set `STRICT_CORS=1` to restrict to `FRONTEND_URL`.

## Integration Points
- **AI ↔ Backend**: Backend uses `AI_SERVICE_URL` to call AI `/predict`.
- **Backend ↔ Frontend**: Frontend proxies `/auth`, `/api`, `/media` to Backend via Vite config.
- **Database**: Backend uses MySQL via `aiomysql` and/or SQLAlchemy (see `backend/app/api/core/mysql.py`, `database.py`).

## Key Files & Examples
- `ai/models/imagemodel_gemini.py`: Gemini image model logic.
- `ai/serving/fastapi_app/main.py`: AI FastAPI server.
- `backend/app/main.py`: Backend FastAPI app, CORS, session, media mounting.
- `backend/app/api/routes/images.py`: Image generation and media storage.
- `frontend/src/api/client.js`: API client for health and image requests.
- `frontend/vite.config.js`: Proxy config for API routes.

## Troubleshooting
- Port conflicts: Use `Get-NetTCPConnection -LocalPort 8000,8600,5174 -State Listen` and `Stop-Process -Id <PID> -Force`.
- Missing images: Check if `/media/xxx.png` returns 200, verify Backend media mount and storage path.
- OAuth issues: Ensure redirect URIs and scopes match service settings.

---
For further details, see each service's `README.md` and `.env.example`. Update this file as project conventions evolve.
