from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from serving.config import ServingSettings
from serving.observability.middleware import AuditMiddleware
from serving.observability.migrate import run_migrations
from serving.observability.repository import AuditRepository
from serving.routes import forecast, predict_tsa, release, scenario
from serving.routes import static as static_routes


def create_app(settings: ServingSettings | None = None) -> FastAPI:
    cfg = settings or ServingSettings.from_yaml()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if cfg.audit_enabled:
            run_migrations(cfg.repo_root, cfg.audit_db_path_resolved)
        yield

    app = FastAPI(title="GIFI Serving", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if cfg.audit_enabled:
        audit_repo = AuditRepository(cfg.audit_db_path_resolved)
        app.add_middleware(
            AuditMiddleware,
            repository=audit_repo,
            enabled=True,
            max_body_bytes=cfg.audit_max_body_bytes,
        )

    app.include_router(scenario.router)
    app.include_router(forecast.router)
    app.include_router(predict_tsa.router)
    app.include_router(release.router)
    app.include_router(static_routes.router)

    if cfg.static_path.is_dir():
        app.mount("/", StaticFiles(directory=str(cfg.static_path), html=True), name="spa")

    return app


app = create_app()
