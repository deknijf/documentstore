"""Uploads are size-capped and typed from their own bytes.

The multipart Content-Type is client-supplied, so it must not decide the stored
type, the storage extension, or which processing branch runs.
"""

import io

from tests.conftest import MINIMAL_PDF, TINY_JPEG, TINY_PNG


def _upload(client, tenant, name, data, content_type):
    return client.post(
        "/api/documents",
        headers=tenant["auth"],
        files={"file": (name, io.BytesIO(data), content_type)},
    )


def test_valid_pdf_is_accepted(client, tenant_a):
    response = _upload(client, tenant_a, "factuur.pdf", MINIMAL_PDF, "application/pdf")
    assert response.status_code == 200, response.text
    assert response.json()["content_type"] == "application/pdf"


def test_valid_png_is_accepted(client, tenant_a):
    response = _upload(client, tenant_a, "scan.png", TINY_PNG, "image/png")
    assert response.status_code == 200, response.text
    assert response.json()["content_type"] == "image/png"


def test_valid_jpeg_is_accepted(client, tenant_a):
    response = _upload(client, tenant_a, "scan.jpg", TINY_JPEG, "image/jpeg")
    assert response.status_code == 200, response.text
    assert response.json()["content_type"] == "image/jpeg"


def test_declared_type_cannot_override_the_real_type(client, tenant_a):
    # PDF bytes announced as a PNG must be stored and processed as a PDF.
    response = _upload(client, tenant_a, "verhuld.png", MINIMAL_PDF, "image/png")
    assert response.status_code == 200, response.text
    assert response.json()["content_type"] == "application/pdf"


def test_content_that_is_not_a_supported_type_is_rejected(client, tenant_a):
    response = _upload(client, tenant_a, "nep.pdf", b"gewoon platte tekst\n" * 50, "application/pdf")
    assert response.status_code == 400


def test_disallowed_declared_type_is_rejected(client, tenant_a):
    assert _upload(client, tenant_a, "a.zip", MINIMAL_PDF, "application/zip").status_code == 400


def test_upload_larger_than_the_cap_is_rejected(client, tenant_a):
    from app.config import settings

    oversized = MINIMAL_PDF + b"\x00" * (settings.max_upload_mb * 1024 * 1024 + 1024)
    response = _upload(client, tenant_a, "groot.pdf", oversized, "application/pdf")
    assert response.status_code == 413


def test_stored_extension_comes_from_the_content_not_the_filename(client, tenant_a):
    from pathlib import Path

    from app.db import SessionLocal
    from app.models import Document

    document_id = _upload(client, tenant_a, "../../ontsnapping.png", MINIMAL_PDF, "image/png").json()["id"]
    db = SessionLocal()
    try:
        stored = Path(db.get(Document, document_id).file_path)
    finally:
        db.close()
    assert stored.suffix == ".pdf"
    assert stored.name.startswith(document_id)


def test_shipped_default_upload_cap_is_50mb():
    # conftest lowers the cap to keep the oversize test fast; guard the default.
    from app.config import Settings

    assert Settings.model_fields["max_upload_mb"].default == 50


def test_avatar_upload_is_capped(client, tenant_a):
    response = client.post(
        "/api/auth/me/avatar",
        headers=tenant_a["auth"],
        files={"file": ("avatar.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * (6 * 1024 * 1024)), "image/png")},
    )
    assert response.status_code == 400
    assert "te groot" in response.json()["detail"]
