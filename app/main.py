from pathlib import Path
import ipaddress

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.responses import PlainTextResponse

from app import legacy_main
from app.config import settings
from app.routers import admin, audit, auth, bank, catalog, documents, health, jobs, search, views


def _split_csv_env(value: str) -> list[str]:
    return [p.strip() for p in (value or "").split(",") if p.strip()]

def _parse_allowed_cidrs(cidrs_csv: str) -> list[ipaddress._BaseNetwork]:
    nets: list[ipaddress._BaseNetwork] = []
    for raw in _split_csv_env(cidrs_csv):
        try:
            nets.append(ipaddress.ip_network(raw, strict=False))
        except ValueError:
            continue
    return nets


def _host_without_port(host_header: str) -> str:
    host = str(host_header or "").strip()
    if not host:
        return ""
    if host.startswith("["):
        # IPv6 like [::1]:8000
        end = host.find("]")
        if end > 0:
            return host[1:end]
    if ":" in host:
        return host.split(":", 1)[0]
    return host


def _host_matches_allowlist(host: str, allow_hosts: list[str], allow_nets: list[ipaddress._BaseNetwork]) -> bool:
    h = str(host or "").strip().lower()
    if not h:
        return False
    for raw in allow_hosts:
        pattern = str(raw or "").strip().lower()
        if not pattern:
            continue
        if pattern == "*":
            return True
        if pattern.startswith("*."):
            suffix = pattern[1:]  # ".example.com"
            if h.endswith(suffix):
                return True
        elif h == pattern:
            return True
    try:
        ip = ipaddress.ip_address(h)
    except ValueError:
        return False
    return any(ip in net for net in allow_nets)


app = FastAPI(title=settings.app_name)

# Middleware (same behavior as before)
allowed_hosts = _split_csv_env(settings.allowed_hosts)
allowed_host_nets = _parse_allowed_cidrs(settings.allowed_host_cidrs)
if allowed_hosts or allowed_host_nets:
    @app.middleware("http")
    async def enforce_allowed_hosts(request: Request, call_next):
        host = _host_without_port(request.headers.get("host", ""))
        if not _host_matches_allowlist(host, allowed_hosts, allowed_host_nets):
            return PlainTextResponse("Invalid host header", status_code=400)
        return await call_next(request)

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


@app.get("/downloads/android-apk")
def download_android_apk() -> FileResponse:
    apk_meta = legacy_main.android_apk_meta()
    apk_path = Path("static/mobile/docstore-mobile-latest.apk")
    if not apk_meta.get("available") or not apk_path.exists():
        raise HTTPException(status_code=404, detail="Android APK niet beschikbaar")
    version = str(apk_meta.get("version") or settings.app_version or settings.version or "0.0.0")
    return FileResponse(
        apk_path,
        media_type="application/vnd.android.package-archive",
        filename=f"docstore-mobile-{version}.apk",
    )


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
