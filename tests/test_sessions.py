"""Session tokens are stored hashed, revocable, and login attempts are audited."""

import hashlib

from tests.conftest import PASSWORD


def _fetch(model, **filters):
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        query = db.query(model)
        for field, value in filters.items():
            query = query.filter(getattr(model, field) == value)
        return query.all()
    finally:
        db.close()


def _login(client, email, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_login_stores_only_a_hash_of_the_token(client, tenant_a):
    from app.models import SessionToken

    token = _login(client, tenant_a["email"]).json()["token"]
    assert not _fetch(SessionToken, token_hash=token), "raw token must not be stored"
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert len(_fetch(SessionToken, token_hash=digest)) == 1


def test_logout_endpoint_is_registered_and_revokes_the_session(client, tenant_a):
    from app.models import SessionToken

    token = _login(client, tenant_a["email"]).json()["token"]
    auth = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/auth/me", headers=auth).status_code == 200
    assert client.post("/api/auth/logout", headers=auth).status_code == 200
    assert client.get("/api/auth/me", headers=auth).status_code == 401

    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert not _fetch(SessionToken, token_hash=digest)


def test_logout_is_audited(client, tenant_a):
    from app.models import AuditLog

    token = _login(client, tenant_a["email"]).json()["token"]
    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert _fetch(AuditLog, tenant_id=tenant_a["tenant_id"], action="auth.logout")


def test_failed_login_against_a_known_account_is_audited(client, tenant_a):
    from app.models import AuditLog

    before = len(_fetch(AuditLog, tenant_id=tenant_a["tenant_id"], action="auth.login_failed"))
    assert _login(client, tenant_a["email"], "het-verkeerde-wachtwoord").status_code == 401
    after = _fetch(AuditLog, tenant_id=tenant_a["tenant_id"], action="auth.login_failed")
    assert len(after) == before + 1
    assert tenant_a["email"] in str(after[-1].details_json)


def test_failed_login_against_an_unknown_account_is_audited(client):
    from app.models import AuditLog

    before = len(_fetch(AuditLog, action="auth.login_failed"))
    assert _login(client, "bestaat-niet@example.invalid", "x").status_code == 401
    assert len(_fetch(AuditLog, action="auth.login_failed")) == before + 1


def test_invalid_and_absent_tokens_are_rejected(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer tok_onzin"}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "tok_onzin"}).status_code == 401


def test_session_token_migration_rehashes_in_place_and_is_idempotent(client):
    """Migration v4 must not log anyone out, and must survive being re-run."""
    import uuid

    from sqlalchemy import text

    from app.db import _apply_pending_migrations, engine

    raw = f"tok_{uuid.uuid4().hex}{uuid.uuid4().hex}"
    row_id = str(uuid.uuid4())
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    with engine.begin() as conn:
        tenant_id = conn.execute(text("SELECT id FROM tenants LIMIT 1")).scalar()
        user_id = conn.execute(text("SELECT id FROM users LIMIT 1")).scalar()
        conn.execute(
            text(
                "INSERT INTO session_tokens(tenant_id, id, token, user_id, created_at) "
                "VALUES (:tenant_id, :id, :token, :user_id, CURRENT_TIMESTAMP)"
            ),
            {"tenant_id": tenant_id, "id": row_id, "token": raw, "user_id": user_id},
        )
        # Pretend the database is still on the previous schema version.
        conn.execute(text("UPDATE schema_migrations SET schema_version = 3 WHERE id = 1"))

        _apply_pending_migrations(conn)
        stored = conn.execute(
            text("SELECT token FROM session_tokens WHERE id = :id"), {"id": row_id}
        ).scalar()
        assert stored == digest, "existing session must be rehashed, not dropped"

        # Re-running must not hash the hash, which would invalidate the session.
        conn.execute(text("UPDATE schema_migrations SET schema_version = 3 WHERE id = 1"))
        _apply_pending_migrations(conn)
        assert (
            conn.execute(text("SELECT token FROM session_tokens WHERE id = :id"), {"id": row_id}).scalar()
            == digest
        )
        conn.execute(text("UPDATE schema_migrations SET schema_version = 4 WHERE id = 1"))
        conn.execute(text("DELETE FROM session_tokens WHERE id = :id"), {"id": row_id})


def test_schema_version_matches_the_application(client):
    from sqlalchemy import text

    from app import __db_schema_version__
    from app.db import engine

    with engine.begin() as conn:
        recorded = conn.execute(text("SELECT schema_version FROM schema_migrations WHERE id = 1")).scalar()
    assert recorded == __db_schema_version__


def test_production_refuses_to_trust_forwarded_headers_from_every_peer(monkeypatch):
    """With '*' any client can spoof its address in the audit log."""
    import pytest

    from app.config import settings
    from app.db import SessionLocal
    from app.legacy_main import _startup_guardrails_and_cleanup

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "allowed_hosts", "docstore.example")
    monkeypatch.setattr(settings, "integration_master_key", "een-echte-sleutel")
    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    monkeypatch.setattr(settings, "forwarded_allow_ips", "*")

    db = SessionLocal()
    try:
        with pytest.raises(RuntimeError, match="FORWARDED_ALLOW_IPS"):
            _startup_guardrails_and_cleanup(db)

        monkeypatch.setattr(settings, "forwarded_allow_ips", "127.0.0.1,172.16.0.0/12")
        _startup_guardrails_and_cleanup(db)
    finally:
        db.close()
