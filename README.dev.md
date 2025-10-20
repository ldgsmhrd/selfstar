# Dev mode with hot reload

Run Docker services with live reload for backend, frontend, and AI.

## Start (dev override)

```powershell
# From project root
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

- backend: uvicorn --reload (watchfiles; polling enabled for Windows)
- frontend: Vite dev server (chokidar polling)
- ai: uvicorn --reload

## Stop

```powershell
docker compose down
```

## Troubleshooting
- Code changes not reflected: ensure you started from the repo root so bind volumes mount correctly.
- Backend not reloading: check logs for "Detected change... reloading".
- Frontend not reloading: hard refresh the browser (Ctrl+F5). On Windows, polling is enabled (CHOKIDAR_USEPOLLING).
