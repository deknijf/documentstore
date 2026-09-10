"""Shared test setup.

app.config builds its Settings object and app.db builds the SQLAlchemy engine at
import time, so the environment has to point at a throwaway data directory
before any app module is imported. Explicit environment variables also take
precedence over the developer's own .env, which keeps the suite from touching
real provider credentials or a real mailbox.
"""

import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="docstore-tests-"))

os.environ.update(
    {
        "ENVIRONMENT": "development",
        "DATA_DIR": str(_TMP),
        "UPLOADS_DIR": str(_TMP / "uploads"),
        "PREPROCESSED_DIR": str(_TMP / "preprocessed"),
        "THUMBNAILS_DIR": str(_TMP / "thumbnails"),
        "AVATARS_DIR": str(_TMP / "avatars"),
        "SQLITE_PATH": str(_TMP / "test.db"),
        "INTEGRATION_MASTER_KEY": "test-master-key",
        # Both must be empty to disable the Host check; TestClient uses
        # "testserver". A developer .env with ALLOWED_HOST_CIDRS set would
        # otherwise keep the middleware active and fail every request.
        "ALLOWED_HOSTS": "",
        "ALLOWED_HOST_CIDRS": "",
        "CORS_ALLOW_ORIGINS": "",
        "TRUST_PROXY_HEADERS": "false",
        "MAIL_INGEST_ENABLED": "false",
        "MAIL_INGEST_FREQUENCY_MINUTES": "0",
        # A small cap keeps the oversize test fast; the shipped default is
        # asserted separately in test_uploads.py.
        "MAX_UPLOAD_MB": "2",
        # No test may reach an external provider.
        "AWS_ACCESS_KEY_ID": "",
        "AWS_SECRET_ACCESS_KEY": "",
        "OPENROUTER_API_KEY": "",
        "OPENAI_API_KEY": "",
        "GOOGLE_API_KEY": "",
    }
)

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

# Fail loudly rather than silently running against the developer's own .env or,
# worse, their real data directory.
assert str(settings.sqlite_path).startswith(str(_TMP)), (
    f"tests are pointed at {settings.sqlite_path}, not at the temporary directory"
)
assert not settings.allowed_hosts and not settings.allowed_host_cidrs, (
    "host allowlist leaked in from .env; TestClient requests would be rejected"
)

PASSWORD = "TestPassw0rd!"

def _encode_image(fmt: str) -> bytes:
    """A real 1x1 image. Pillow is a hard dependency of the app, so tests can
    rely on it instead of carrying hand-written binary blobs."""
    from io import BytesIO

    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (1, 1), (255, 255, 255)).save(buffer, format=fmt)
    return buffer.getvalue()


TINY_JPEG = _encode_image("JPEG")
TINY_PNG = _encode_image("PNG")
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)


@pytest.fixture(scope="session")
def client():
    # The context manager triggers the startup event (init_db, migrations,
    # bootstrap admin, worker threads), exactly as in production.
    with TestClient(app) as test_client:
        yield test_client
    shutil.rmtree(_TMP, ignore_errors=True)


def _signup(client) -> dict:
    email = f"t-{uuid.uuid4().hex[:12]}@example.invalid"
    response = client.post(
        "/api/auth/signup",
        json={"name": f"Tenant {email}", "email": email, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    return {
        "email": email,
        "token": body["token"],
        "auth": {"Authorization": f"Bearer {body['token']}"},
        "tenant_id": body["user"]["tenant_id"],
        "user_id": body["user"]["id"],
        "group_ids": body["user"]["group_ids"],
    }


@pytest.fixture(scope="session")
def tenant_a(client) -> dict:
    return _signup(client)


@pytest.fixture(scope="session")
def tenant_b(client) -> dict:
    return _signup(client)


def make_document(tenant: dict, *, with_thumbnail: bool = True) -> str:
    """Insert a ready document plus its files, without running the OCR pipeline.

    Going through the real upload endpoint would make file-access tests depend
    on OCR/AI providers that tests must never call.
    """
    from app.config import settings
    from app.db import SessionLocal
    from app.models import Document

    document_id = str(uuid.uuid4())
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.thumbnails_dir).mkdir(parents=True, exist_ok=True)

    file_path = Path(settings.uploads_dir) / f"{document_id}_original.pdf"
    file_path.write_bytes(MINIMAL_PDF)
    thumbnail_path = None
    if with_thumbnail:
        (Path(settings.thumbnails_dir) / f"{document_id}.jpg").write_bytes(TINY_JPEG)
        thumbnail_path = f"/thumbnails/{document_id}.jpg"

    db = SessionLocal()
    try:
        db.add(
            Document(
                id=document_id,
                tenant_id=tenant["tenant_id"],
                filename="test.pdf",
                content_type="application/pdf",
                file_path=str(file_path),
                original_file_path=str(file_path),
                original_content_type="application/pdf",
                original_filename="test.pdf",
                thumbnail_path=thumbnail_path,
                group_id=(tenant["group_ids"] or [None])[0],
                uploaded_by_user_id=tenant["user_id"],
                status="ready",
                ocr_processed=True,
                ai_processed=False,
            )
        )
        db.commit()
    finally:
        db.close()
    return document_id


@pytest.fixture
def document_a(tenant_a) -> str:
    return make_document(tenant_a)
