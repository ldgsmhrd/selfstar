from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import Settings, get_settings
from .api.routes.health import router as health_router


def create_app() -> FastAPI:
    settings: Settings = get_settings()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        summary="Backend service"
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router)

    @app.get("/", tags=["root"])  # simple root endpoint
    async def root():
        return {"message": f"{settings.PROJECT_NAME} API"}

    return app


app = create_app()
