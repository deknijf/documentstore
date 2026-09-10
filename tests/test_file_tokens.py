"""Unit tests for the signed-URL helper that replaced the static file mounts."""

import time
from urllib.parse import parse_qs

import pytest

from app.services.file_tokens import SCOPE_FILE, SCOPE_THUMBNAIL, signed_query, verify


def _parts(query: str) -> tuple[str, str]:
    parsed = parse_qs(query)
    return parsed["exp"][0], parsed["sig"][0]


def test_signed_query_verifies():
    exp, sig = _parts(signed_query(SCOPE_THUMBNAIL, "doc-1"))
    assert verify(SCOPE_THUMBNAIL, "doc-1", "", exp, sig)


def test_tampered_signature_is_rejected():
    exp, sig = _parts(signed_query(SCOPE_THUMBNAIL, "doc-1"))
    flipped = ("0" if sig[0] != "0" else "1") + sig[1:]
    assert not verify(SCOPE_THUMBNAIL, "doc-1", "", exp, flipped)


def test_signature_is_bound_to_the_resource():
    exp, sig = _parts(signed_query(SCOPE_THUMBNAIL, "doc-1"))
    assert not verify(SCOPE_THUMBNAIL, "doc-2", "", exp, sig)


def test_signature_is_bound_to_the_scope():
    exp, sig = _parts(signed_query(SCOPE_THUMBNAIL, "doc-1"))
    assert not verify(SCOPE_FILE, "doc-1", "", exp, sig)


def test_signature_is_bound_to_the_variant():
    exp, sig = _parts(signed_query(SCOPE_FILE, "doc-1", "viewer"))
    assert verify(SCOPE_FILE, "doc-1", "viewer", exp, sig)
    assert not verify(SCOPE_FILE, "doc-1", "original", exp, sig)


def test_expiry_cannot_be_extended_by_the_client():
    exp, sig = _parts(signed_query(SCOPE_FILE, "doc-1", "viewer"))
    assert not verify(SCOPE_FILE, "doc-1", "viewer", str(int(exp) + 3600), sig)


def test_expired_signature_is_rejected():
    assert not verify(SCOPE_FILE, "doc-1", "viewer", str(int(time.time()) - 1), "0" * 32)


@pytest.mark.parametrize("exp,sig", [(None, None), ("", ""), ("abc", "x"), ("123", "")])
def test_malformed_input_is_rejected(exp, sig):
    assert not verify(SCOPE_FILE, "doc-1", "viewer", exp, sig)


def test_url_is_stable_between_polls():
    # The SPA reloads documents every few seconds. A per-request expiry would
    # change the URL each time and defeat browser caching.
    assert signed_query(SCOPE_THUMBNAIL, "doc-1") == signed_query(SCOPE_THUMBNAIL, "doc-1")
