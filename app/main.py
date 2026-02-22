from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app import legacy_main
from app.config import settings
from app.routers import admin, audit, auth, bank, catalog, documents, health, jobs, search, views


def _split_csv_env(value: str) -> list[str]:
    return [p.strip() for p in (value or "").split(",") if p.strip()]


app = FastAPI(title=settings.app_name)

# Middleware (same behavior as before)
allowed_hosts = _split_csv_env(settings.allowed_hosts)
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

cors_origins = _split_csv_env(settings.cors_allow_origins)
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Dev-friendly default: allow all origins, but without credentials.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(catalog.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(views.router)
app.include_router(bank.router)
app.include_router(admin.router)
app.include_router(audit.router)


@app.on_event("startup")
def startup() -> None:
    # Keep legacy startup behavior intact (DB init, bootstrap admin, mail ingest thread, search index, etc.)
    legacy_main.startup()


@app.on_event("shutdown")
def shutdown() -> None:
    legacy_main.shutdown()


# Static mounts (same as before)
Path(settings.thumbnails_dir).mkdir(parents=True, exist_ok=True)
Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
Path(settings.avatars_dir).mkdir(parents=True, exist_ok=True)
app.mount("/thumbnails", StaticFiles(directory=settings.thumbnails_dir), name="thumbnails")
app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
app.mount("/avatars", StaticFiles(directory=settings.avatars_dir), name="avatars")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
