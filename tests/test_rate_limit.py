"""Authentication and expensive endpoints are rate limited.

Rate limiting is off for the rest of the suite so one module cannot spend
another's budget; these tests enable it explicitly and reset the counters.
"""

import pytest

from app.services.rate_limit import (
    LOGIN_ACCOUNT_FAILURE_LIMIT,
    RateLimiter,
    account_key,
    limiter,
    rule_for,
)
from tests.conftest import PASSWORD


@pytest.fixture
def rate_limited(monkeypatch):
    from app.config import settings

    limiter.reset()
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    yield
    limiter.reset()


def test_limiter_allows_up_to_the_limit_then_blocks():
    counter = RateLimiter()
    assert all(counter.retry_after("k", limit=3, window_seconds=60) == 0 for _ in range(3))
    wait = counter.retry_after("k", limit=3, window_seconds=60)
    assert 0 < wait <= 61


def test_limiter_keys_are_independent():
    counter = RateLimiter()
    for _ in range(3):
        counter.retry_after("a", limit=3, window_seconds=60)
    assert counter.retry_after("b", limit=3, window_seconds=60) == 0


def test_inspecting_the_budget_does_not_consume_it():
    counter = RateLimiter()
    for _ in range(10):
        assert counter.retry_after("k", limit=2, window_seconds=60, register=False) == 0
    assert counter.retry_after("k", limit=2, window_seconds=60) == 0


def test_expired_hits_free_the_budget_again():
    counter = RateLimiter()
    for _ in range(2):
        counter.retry_after("k", limit=2, window_seconds=0)
    assert counter.retry_after("k", limit=2, window_seconds=0) == 0


def test_only_configured_endpoints_are_limited():
    assert rule_for("POST", "/api/auth/login") is not None
    assert rule_for("POST", "/api/bank/budget/analyze") is not None
    # Prefix matching would let /analyze and /analyze/start share one budget.
    assert rule_for("POST", "/api/bank/budget/analyze/start") is not None
    assert rule_for("GET", "/api/auth/login") is None
    assert rule_for("GET", "/api/documents") is None


def test_repeated_login_attempts_are_throttled(client, tenant_a, rate_limited):
    _, _, limit, _ = next(r for r in __import__(
        "app.services.rate_limit", fromlist=["AUTH_RATE_LIMITS"]
    ).AUTH_RATE_LIMITS if r[1] == "/api/auth/login")

    statuses = [
        client.post(
            "/api/auth/login", json={"email": tenant_a["email"], "password": "fout"}
        ).status_code
        for _ in range(limit + 1)
    ]
    assert statuses[:limit] == [401] * limit
    assert statuses[-1] == 429


def test_throttled_response_tells_the_client_when_to_retry(client, tenant_a, rate_limited):
    for _ in range(40):
        response = client.post(
            "/api/auth/login", json={"email": tenant_a["email"], "password": "fout"}
        )
        if response.status_code == 429:
            assert int(response.headers["Retry-After"]) > 0
            return
    pytest.fail("login werd nooit afgeknepen")


def test_signup_is_throttled(client, rate_limited):
    import uuid

    statuses = [
        client.post(
            "/api/auth/signup",
            json={
                "name": "spam",
                "email": f"spam-{uuid.uuid4().hex[:10]}@example.invalid",
                "password": PASSWORD,
            },
        ).status_code
        for _ in range(6)
    ]
    assert 429 in statuses


def test_account_failure_budget_blocks_even_from_a_fresh_address(client, tenant_a, rate_limited):
    """The per-IP budget would otherwise always trip first, so fill only the
    account budget: this is what slows a distributed attack on one account."""
    for _ in range(LOGIN_ACCOUNT_FAILURE_LIMIT):
        limiter.retry_after(
            account_key(tenant_a["email"]), limit=LOGIN_ACCOUNT_FAILURE_LIMIT, window_seconds=900
        )
    response = client.post(
        "/api/auth/login", json={"email": tenant_a["email"], "password": PASSWORD}
    )
    assert response.status_code == 429


def test_a_correct_password_still_works_while_the_account_budget_has_room(
    client, tenant_a, rate_limited
):
    # A third party must not be able to lock a real user out of their account.
    for _ in range(LOGIN_ACCOUNT_FAILURE_LIMIT - 1):
        limiter.retry_after(
            account_key(tenant_a["email"]), limit=LOGIN_ACCOUNT_FAILURE_LIMIT, window_seconds=900
        )
    response = client.post(
        "/api/auth/login", json={"email": tenant_a["email"], "password": PASSWORD}
    )
    assert response.status_code == 200


def test_successful_logins_do_not_consume_the_failure_budget(client, tenant_a, rate_limited):
    for _ in range(5):
        assert client.post(
            "/api/auth/login", json={"email": tenant_a["email"], "password": PASSWORD}
        ).status_code == 200
    assert limiter.retry_after(
        account_key(tenant_a["email"]),
        limit=LOGIN_ACCOUNT_FAILURE_LIMIT,
        window_seconds=900,
        register=False,
    ) == 0


def test_rate_limiting_can_be_switched_off(client, tenant_a, monkeypatch):
    from app.config import settings

    limiter.reset()
    monkeypatch.setattr(settings, "rate_limit_enabled", False)
    statuses = [
        client.post(
            "/api/auth/login", json={"email": tenant_a["email"], "password": "fout"}
        ).status_code
        for _ in range(25)
    ]
    assert set(statuses) == {401}
    limiter.reset()
