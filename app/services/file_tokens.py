"""Signed, expiring URLs for tenant-scoped file artifacts.

Static file mounts cannot enforce authorization, and <img>/<iframe> elements
cannot send an Authorization header. So the API hands out short-lived
HMAC-signed URLs for artifacts it has already authorized, instead of serving
those artifacts unauthenticated or putting the session token in a query string.

Expiry is snapped to a fixed grid so a given artifact keeps the same URL
between API polls; a per-request expiry would change the URL every few seconds
and defeat browser caching.
"""

import hashlib
import hmac
import time

from app.config import settings

SCOPE_THUMBNAIL = "thumb"
SCOPE_FILE = "file"

_GRID_SECONDS = 3600


def _signing_key() -> bytes:
    # Derived from the master key so rotating that key revokes outstanding URLs.
    seed = f"docstore-file-url::{settings.integration_master_key}"
    return hashlib.sha256(seed.encode("utf-8")).digest()


def _signature(scope: str, resource_id: str, variant: str, expires_at: int) -> str:
    message = f"{scope}:{resource_id}:{variant}:{expires_at}".encode("utf-8")
    return hmac.new(_signing_key(), message, hashlib.sha256).hexdigest()[:32]


def _expires_at() -> int:
    ttl = max(_GRID_SECONDS, int(getattr(settings, "file_url_ttl_seconds", 86400) or 86400))
    now = int(time.time())
    return ((now // _GRID_SECONDS) * _GRID_SECONDS) + ttl


def signed_query(scope: str, resource_id: str, variant: str = "") -> str:
    expires_at = _expires_at()
    return f"exp={expires_at}&sig={_signature(scope, resource_id, variant, expires_at)}"


def verify(scope: str, resource_id: str, variant: str, expires_at_raw, signature_raw) -> bool:
    try:
        expires_at = int(str(expires_at_raw or "").strip())
    except (TypeError, ValueError):
        return False
    if expires_at < int(time.time()):
        return False
    supplied = str(signature_raw or "").strip()
    if not supplied:
        return False
    return hmac.compare_digest(supplied, _signature(scope, resource_id, variant, expires_at))
