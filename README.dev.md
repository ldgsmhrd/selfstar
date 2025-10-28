# Dev mode with hot reload

Run all services with live reload and bind mounts for faster iteration on Windows.

## Start (dev override)

```powershell
# From project root
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

- backend: uvicorn --reload (watchfiles; polling enabled for Windows)
- frontend: Vite dev server (chokidar polling)
- ai: uvicorn --reload

Volumes
- backend: mounts `backend/app` and persists `backend/app/storage` → served at `/files`
- frontend: mounts `frontend/`
- ai: mounts `ai/`

## Stop

```powershell
docker compose down
```

## Troubleshooting
- Code changes not reflected: start compose from repo root so bind mounts apply.
- Backend not reloading: check logs for "Detected change... reloading".
- Frontend not reloading: hard refresh (Ctrl+F5). On Windows, polling is enabled (CHOKIDAR_USEPOLLING).
- Instagram uploads fail in dev: ensure BACKEND_URL is public HTTPS (use ngrok) so Graph API can fetch files.
