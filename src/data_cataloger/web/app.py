"""FastAPI application factory for Data Cataloger web interface."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from data_cataloger.web.routes import graph_router, progress_router, tables_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application with CORS, static files, and routes.
    """
    app = FastAPI(
        title="Data Cataloger",
        description="Web interface for exploring database catalog",
        version="0.1.0",
    )

    # CORS middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    # Register API routes
    app.include_router(tables_router)
    app.include_router(graph_router)
    app.include_router(progress_router)

    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    return app


# Application instance for uvicorn
app = create_app()
