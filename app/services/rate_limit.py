"""In-process rate limiting for authentication and expensive endpoints.

Docstore runs as a single uvicorn process against a local SQLite database, so a
shared store would add a dependency without adding correctness. If it ever runs
more than one worker or replica, this has to move to a shared backend.

Limits are deliberately well above normal usage: the goal is to make credential
stuffing and repeated LLM-backed jobs expensive, not to police real users.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import deque

# (method, path, limit, window_seconds). Paths are matched exactly, so
# /analyze and /analyze/start get their own budgets.
AUTH_RATE_LIMITS: tuple[tuple[str, str, int, int], ...] = (
    ("POST", "/api/auth/login", 20, 300),
    ("POST", "/api/auth/signup", 5, 3600),
    ("POST", "/api/auth/forgot-password", 5, 3600),
    ("POST", "/api/auth/reset-password", 10, 3600),
)

# Endpoints that trigger OCR/LLM work or a mailbox scan.
EXPENSIVE_RATE_LIMITS: tuple[tuple[str, str, int, int], ...] = (
    ("POST", "/api/bank/budget/analyze", 20, 3600),
    ("POST", "/api/bank/budget/analyze/start", 20, 3600),
    ("POST", "/api/bank/budget/refresh", 30, 3600),
    ("POST", "/api/documents/check-bank", 20, 3600),
    ("POST", "/api/documents/check-bank/start", 20, 3600),
    ("POST", "/api/admin/mail-ingest/run", 12, 3600),
)

# A failed-login budget per account slows targeted credential stuffing from
# many addresses. Only failures count and the budget is generous, so a third
# party cannot lock a real user out of their own account.
LOGIN_ACCOUNT_FAILURE_LIMIT = 30
LOGIN_ACCOUNT_FAILURE_WINDOW = 900

_PRUNE_AFTER_SECONDS = 3600
_MAX_TRACKED_KEYS = 20_000


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def retry_after(self, key: str, *, limit: int, window_seconds: int, register: bool = True) -> int:
        """Return 0 when the call is allowed, else seconds until it may retry.

        With register=False the budget is only inspected, not consumed, which
        lets a caller charge for failures only.
        """
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            hits = self._hits.get(key)
            if hits is None:
                hits = self._hits[key] = deque()
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= limit:
                return max(1, int(window_seconds - (now - hits[0])) + 1)
            if register:
                hits.append(now)
                if len(self._hits) > _MAX_TRACKED_KEYS:
                    self._prune(now)
            return 0

    def _prune(self, now: float) -> None:
        stale = now - _PRUNE_AFTER_SECONDS
        for key in [k for k, v in self._hits.items() if not v or v[-1] <= stale]:
            self._hits.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def rule_for(method: str, path: str) -> tuple[str, int, int] | None:
    """Return (bucket, limit, window) for a rate-limited endpoint."""
    for rule_method, rule_path, limit, window in AUTH_RATE_LIMITS:
        if method == rule_method and path == rule_path:
            return ("auth", limit, window)
    for rule_method, rule_path, limit, window in EXPENSIVE_RATE_LIMITS:
        if method == rule_method and path == rule_path:
            return ("expensive", limit, window)
    return None


def client_ip(request) -> str:
    return str(getattr(getattr(request, "client", None), "host", "") or "unknown")


def caller_identity(request) -> str:
    """Identify the caller of an expensive endpoint.

    Hashing the Authorization header keys the budget to a session without a
    database lookup; unauthenticated callers fall back to their address.
    """
    header = str(request.headers.get("authorization") or "").strip()
    if header:
        return "session:" + hashlib.sha256(header.encode("utf-8")).hexdigest()[:24]
    return "ip:" + client_ip(request)


def account_key(email: str) -> str:
    return "login-failure:" + str(email or "").strip().lower()
