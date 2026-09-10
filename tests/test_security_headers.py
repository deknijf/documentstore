"""Every response carries the browser-side defences, and CORS is off by default."""

import pytest

from app.main import CONTENT_SECURITY_POLICY


@pytest.mark.parametrize(
    "header,expected",
    [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "SAMEORIGIN"),
        ("Referrer-Policy", "no-referrer"),
        ("Cross-Origin-Opener-Policy", "same-origin"),
    ],
)
def test_security_headers_are_present_on_the_spa(client, header, expected):
    assert client.get("/").headers[header] == expected


def test_security_headers_are_present_on_api_responses(client, tenant_a):
    assert client.get("/api/documents", headers=tenant_a["auth"]).headers["X-Content-Type-Options"] == "nosniff"


def test_security_headers_are_present_on_error_responses(client):
    # An attacker-facing 401 needs the same protections as a 200.
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.headers["Content-Security-Policy"] == CONTENT_SECURITY_POLICY


def test_csp_blocks_inline_and_injected_script_sources(client):
    policy = client.get("/").headers["Content-Security-Policy"]
    assert "script-src 'self'" in policy
    assert "'unsafe-inline' https://fonts.googleapis.com" in policy.split("style-src ")[1]
    assert "object-src 'none'" in policy
    assert "base-uri 'self'" in policy
    assert "frame-ancestors 'self'" in policy


def test_csp_allows_what_the_spa_actually_needs(client):
    policy = client.get("/").headers["Content-Security-Policy"]
    # The viewer renders PDFs in an iframe and images from blob: URLs.
    assert "frame-src 'self' blob:" in policy
    assert "img-src 'self' data: blob:" in policy
    # Google Fonts is referenced from index.html.
    assert "font-src 'self' https://fonts.gstatic.com" in policy


def test_spa_assets_still_load(client):
    for path in ("/", "/app.js", "/styles.css"):
        assert client.get(path).status_code == 200


def test_no_cors_headers_without_explicit_configuration(client):
    response = client.get("/api/health", headers={"Origin": "https://kwaadaardig.example"})
    assert "access-control-allow-origin" not in {k.lower() for k in response.headers}


def test_index_html_has_no_inline_script_that_the_csp_would_block():
    import re

    html = open("static/index.html").read()
    inline = [body for _, body in re.findall(r"<script([^>]*)>(.*?)</script>", html, re.S) if body.strip()]
    assert inline == [], "inline script would be blocked by script-src 'self'"
    assert not re.findall(r"\son(click|change|submit|load|error)=", html)
