"""Document artifacts must not be reachable without proof of authorization.

Before this hardening, /uploads and /thumbnails were unauthenticated static
mounts and the viewer carried the session token in the query string.
"""

from pathlib import Path
from urllib.parse import parse_qs, urlparse

from tests.conftest import make_document


def _detail(client, tenant, document_id):
    response = client.get(f"/api/documents/{document_id}", headers=tenant["auth"])
    assert response.status_code == 200, response.text
    return response.json()


def test_uploads_static_mount_is_gone(client, tenant_a, document_a):
    from app.config import settings

    stored = Path(settings.uploads_dir) / f"{document_a}_original.pdf"
    assert stored.is_file(), "fixture should have written the original file"
    assert client.get(f"/uploads/{stored.name}").status_code == 404


def test_document_payload_carries_signed_urls(client, tenant_a, document_a):
    body = _detail(client, tenant_a, document_a)
    for key in ("thumbnail_path", "viewer_url", "original_url"):
        query = parse_qs(urlparse(body[key]).query)
        assert "exp" in query and "sig" in query, f"{key} is not signed: {body[key]}"


def test_signed_thumbnail_loads_without_an_authorization_header(client, tenant_a, document_a):
    # <img> cannot send an Authorization header; the signature stands in for it.
    body = _detail(client, tenant_a, document_a)
    response = client.get(body["thumbnail_path"])
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content


def test_unsigned_thumbnail_is_not_served(client, tenant_a, document_a):
    assert client.get(f"/thumbnails/{document_a}.jpg").status_code == 404


def test_tampered_thumbnail_signature_is_not_served(client, tenant_a, document_a):
    body = _detail(client, tenant_a, document_a)
    tampered = body["thumbnail_path"].replace("sig=", "sig=0")
    assert client.get(tampered).status_code == 404


def test_thumbnail_signature_cannot_be_reused_for_another_document(client, tenant_a, document_a):
    other = make_document(tenant_a)
    query = urlparse(_detail(client, tenant_a, other)["thumbnail_path"]).query
    assert client.get(f"/thumbnails/{document_a}.jpg?{query}").status_code == 404


def test_thumbnail_path_traversal_is_rejected(client, tenant_a):
    assert client.get("/thumbnails/..%2f..%2ftest.db?exp=9999999999&sig=x").status_code == 404


def test_deleted_document_keeps_its_thumbnail_for_the_trash_view(client, tenant_a, document_a):
    thumbnail = _detail(client, tenant_a, document_a)["thumbnail_path"]
    assert client.get(thumbnail).status_code == 200
    assert client.post(
        "/api/documents/delete", json={"document_ids": [document_a]}, headers=tenant_a["auth"]
    ).status_code == 200

    trashed = client.get("/api/documents/trash", headers=tenant_a["auth"]).json()
    entry = next(x for x in trashed if x["id"] == document_a)
    assert client.get(entry["thumbnail_path"]).status_code == 200

    client.post("/api/documents/restore", json={"document_ids": [document_a]}, headers=tenant_a["auth"])


def test_signed_viewer_url_loads_without_an_authorization_header(client, tenant_a, document_a):
    body = _detail(client, tenant_a, document_a)
    assert client.get(body["viewer_url"]).status_code == 200
    assert client.get(body["original_url"]).status_code == 200


def test_files_requires_a_signature_or_a_bearer_token(client, tenant_a, document_a):
    assert client.get(f"/files/{document_a}?variant=viewer").status_code == 401


def test_legacy_access_token_query_parameter_no_longer_authenticates(client, tenant_a, document_a):
    # The session token used to be accepted here, which leaked it into access
    # logs and browser history.
    response = client.get(f"/files/{document_a}?variant=viewer&access_token={tenant_a['token']}")
    assert response.status_code == 401


def test_viewer_signature_cannot_be_swapped_to_another_variant(client, tenant_a, document_a):
    viewer_url = _detail(client, tenant_a, document_a)["viewer_url"]
    assert client.get(viewer_url.replace("variant=viewer", "variant=original")).status_code == 401


def test_bearer_download_still_works(client, tenant_a, document_a):
    response = client.get(f"/files/{document_a}", headers=tenant_a["auth"])
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
