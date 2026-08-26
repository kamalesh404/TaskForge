"""FastAPI dashboard backend for TaskForge monitoring."""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    FastAPI = None  # type: ignore[assignment,misc]

from src.dashboard.routes import router


def create_app(backend_url: str = "redis://localhost:6379") -> Any:
    """Create and configure the FastAPI dashboard application."""
    if FastAPI is None:
        raise ImportError("Install dashboard deps: pip install 'taskforge[dashboard]'")

    app = FastAPI(
        title="TaskForge Dashboard",
        description="Real-time monitoring for TaskForge task queues",
        version="0.1.0",
    )
    app.include_router(router, prefix="/api")
    app.state.backend_url = backend_url

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def index() -> Dict[str, str]:
        return {"message": "TaskForge Dashboard", "docs": "/docs"}

    @app.on_event("startup")
    async def on_startup() -> None:
        from src.monitoring.metrics import MetricsCollector
        from src.monitoring.health import HealthChecker
        MetricsCollector()
        HealthChecker(worker_id="dashboard")

    return app


def run_dashboard(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the dashboard with uvicorn."""
    import uvicorn
    app = create_app()
    uvicorn.run(app, host=host, port=port)