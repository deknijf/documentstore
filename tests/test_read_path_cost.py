"""GET /api/documents is polled by every open tab, so it must never call a
provider itself. The expensive fallback belongs in a background job."""

import pytest

from tests.conftest import _signup, make_document


@pytest.fixture
def tenant(client):
    """A fresh tenant per test: the backfill has a per-tenant cooldown, so a
    shared tenant would make these tests depend on each other's ordering."""
    return _signup(client)


def _document_needing_a_budget_label(tenant) -> str:
    from app.db import SessionLocal
    from app.models import Document

    document_id = make_document(tenant)
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        doc.ocr_text = "Factuur van een onbekende leverancier zonder mapping"
        doc.budget_category = None
        doc.budget_category_source = None
        db.commit()
    finally:
        db.close()
    return document_id


def _enable_ai_for(tenant) -> None:
    """Give the tenant a usable provider and a category to choose from.

    Without this the LLM branch returns early on its own and a test asserting
    "the LLM was not called" would pass no matter what the read path does.
    """
    from app.db import SessionLocal
    from app.models import BankCategoryMapping
    from app.services.integration_settings import get_or_create_settings
    from app.services.security import encrypt_secret

    db = SessionLocal()
    try:
        row = get_or_create_settings(db, tenant_id=tenant["tenant_id"])
        row.ai_provider = "openrouter"
        row.openrouter_api_key_encrypted = encrypt_secret("test-key")
        db.add(
            BankCategoryMapping(
                tenant_id=tenant["tenant_id"],
                keyword="komt-niet-voor-in-dit-document",
                flow="expense",
                category="Overige uitgaven",
                priority=1,
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()


def test_listing_documents_never_calls_the_llm(client, tenant, monkeypatch):
    import app.services.pipeline as pipeline
    from app.db import SessionLocal
    from app.models import Document

    _enable_ai_for(tenant)
    calls = []
    monkeypatch.setattr(pipeline, "_call_llm", lambda *a, **k: calls.append(a) or {})

    document_id = _document_needing_a_budget_label(tenant)
    assert client.get("/api/documents", headers=tenant["auth"]).status_code == 200
    assert calls == [], "the read path reached the LLM"

    # Prove the branch really is reachable, so the assertion above has meaning.
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        pipeline._apply_bank_mapping_labels(db, doc=doc, ocr_text=str(doc.ocr_text), allow_llm=True)
    finally:
        db.close()
    assert calls, "the LLM branch was unreachable, so the test proved nothing"


def test_listing_documents_queues_a_backfill_job_instead(client, tenant, monkeypatch):
    import app.legacy_main as legacy_main
    import app.services.pipeline as pipeline
    from app.db import SessionLocal
    from app.models import AsyncJob

    monkeypatch.setattr(pipeline, "_call_llm", lambda *a, **k: {})
    # Keep the job out of a worker thread so the test stays deterministic.
    started = []
    monkeypatch.setattr(legacy_main, "_start_async_job", lambda job_id, worker: started.append(job_id))

    _document_needing_a_budget_label(tenant)
    assert client.get("/api/documents", headers=tenant["auth"]).status_code == 200

    db = SessionLocal()
    try:
        jobs = (
            db.query(AsyncJob)
            .filter(
                AsyncJob.tenant_id == tenant["tenant_id"],
                AsyncJob.job_type == legacy_main.BUDGET_LABEL_JOB_TYPE,
            )
            .all()
        )
    finally:
        db.close()
    assert len(jobs) == 1
    assert started == [str(jobs[0].id)]


def test_backfill_is_not_requeued_on_every_poll(client, tenant, monkeypatch):
    import app.legacy_main as legacy_main
    import app.services.pipeline as pipeline
    from app.db import SessionLocal
    from app.models import AsyncJob

    monkeypatch.setattr(pipeline, "_call_llm", lambda *a, **k: {})
    monkeypatch.setattr(legacy_main, "_start_async_job", lambda job_id, worker: None)

    _document_needing_a_budget_label(tenant)
    for _ in range(5):
        client.get("/api/documents", headers=tenant["auth"])

    db = SessionLocal()
    try:
        count = (
            db.query(AsyncJob)
            .filter(
                AsyncJob.tenant_id == tenant["tenant_id"],
                AsyncJob.job_type == legacy_main.BUDGET_LABEL_JOB_TYPE,
            )
            .count()
        )
    finally:
        db.close()
    assert count == 1, "a polled endpoint must not queue a job per request"


def test_keyword_mapping_still_runs_inline(client, tenant):
    """The cheap path must keep working, so labels are not delayed by a job."""
    from app.db import SessionLocal
    from app.models import BankCategoryMapping, Document

    db = SessionLocal()
    try:
        db.add(
            BankCategoryMapping(
                tenant_id=tenant["tenant_id"],
                keyword="Energieleverancier",
                flow="expense",
                category="Energie",
                priority=1,
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()

    document_id = make_document(tenant)
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        doc.issuer = "Energieleverancier BV"
        doc.ocr_text = "factuur energie"
        doc.budget_category = None
        db.commit()
    finally:
        db.close()

    client.get("/api/documents", headers=tenant["auth"])

    db = SessionLocal()
    try:
        assert db.get(Document, document_id).budget_category == "Energie"
    finally:
        db.close()


def test_label_assignment_and_single_label_survive_one_transaction(client, tenant):
    """Regression: assigning a budget label and then enforcing the single-label
    invariant used to collide on document_labels, rolling back the whole
    transaction and silently discarding the label."""
    from app.db import SessionLocal
    from app.legacy_main import _ensure_doc_single_label
    from app.models import BankCategoryMapping, Document
    from app.services.pipeline import _apply_bank_mapping_labels

    db = SessionLocal()
    try:
        db.add(
            BankCategoryMapping(
                tenant_id=tenant["tenant_id"],
                keyword="Telecomprovider",
                flow="expense",
                category="Telecom",
                priority=1,
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()

    document_id = make_document(tenant)
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        doc.issuer = "Telecomprovider NV"
        doc.ocr_text = "maandelijkse telecomfactuur"
        doc.budget_category = None
        db.commit()

        doc = db.get(Document, document_id)
        _apply_bank_mapping_labels(db, doc=doc, ocr_text=str(doc.ocr_text), allow_llm=False)
        _ensure_doc_single_label(db, doc)
        db.commit()
    finally:
        db.close()

    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        assert doc.budget_category == "Telecom"
        assert [label.name for label in doc.labels] == ["Telecom"]
    finally:
        db.close()
