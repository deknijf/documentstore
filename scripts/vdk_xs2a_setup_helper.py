#!/usr/bin/env python3
"""
VDK XS2A setup helper (read-only).

This script does NOT automate portal login actions.
It guides you through the values you must copy from the VDK XS2A portal,
then optionally performs a read-only GET /accounts test call.
"""

from __future__ import annotations

import base64
import json
import sys
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Dict
from urllib import error, parse, request


PORTAL_URL = "https://xs2a-devportal.vdk.be/home"


@dataclass
class VDKConfig:
    base_url: str
    client_id: str
    api_key: str
    password: str


def prompt(msg: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{msg}{suffix}: ").strip()
    return value or default


def prompt_yes_no(msg: str, default: bool = True) -> bool:
    default_hint = "Y/n" if default else "y/N"
    value = input(f"{msg} ({default_hint}): ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "j", "ja"}


def sanitize_base_url(url: str) -> str:
    return url.strip().rstrip("/")


def build_headers(cfg: VDKConfig) -> Dict[str, str]:
    headers: Dict[str, str] = {"Accept": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    if cfg.client_id:
        headers["X-Client-Id"] = cfg.client_id
    if cfg.password:
        headers["X-VDK-Password"] = cfg.password
    return headers


def probe_accounts(cfg: VDKConfig) -> None:
    url = f"{cfg.base_url}/accounts"
    req = request.Request(url=url, method="GET", headers=build_headers(cfg))
    print("\n[TEST] Read-only request: GET /accounts")
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            print(f"[OK] HTTP {resp.status}")
            preview = raw[:900].strip()
            if not preview:
                print("[INFO] Lege response body.")
                return
            try:
                obj = json.loads(raw)
                pretty = json.dumps(obj, indent=2, ensure_ascii=False)
                print("[INFO] Response preview:")
                print(pretty[:900])
            except Exception:
                print("[INFO] Response preview:")
                print(preview)
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] HTTP {e.code}")
        if body:
            print(body[:1000])
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")


def masked(value: str) -> str:
    if not value:
        return "(leeg)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def print_result(cfg: VDKConfig) -> None:
    print("\n=== In te vullen in Admin > Integraties > VDK Bank (read-only) ===")
    print(f"Base URL : {cfg.base_url or '(leeg)'}")
    print(f"Client ID: {cfg.client_id or '(leeg)'}")
    print(f"API key  : {masked(cfg.api_key)}")
    print(f"Password : {masked(cfg.password)}")

    print("\n=== .env vorm ===")
    print(f"VDK_BASE_URL={cfg.base_url}")
    print(f"VDK_CLIENT_ID={cfg.client_id}")
    print("VDK_API_KEY=<jouw token>")
    print("VDK_PASSWORD=<jouw password indien vereist>")


def maybe_write_template(cfg: VDKConfig) -> None:
    if not prompt_yes_no("Wil je een lokaal templatebestand wegschrijven?", default=False):
        return
    path_raw = prompt("Pad voor templatebestand", default="vdk_setup_template.txt")
    path = Path(path_raw)
    content = (
        "# VDK XS2A read-only setup template\n"
        f"VDK_BASE_URL={cfg.base_url}\n"
        f"VDK_CLIENT_ID={cfg.client_id}\n"
        "VDK_API_KEY=\n"
        "VDK_PASSWORD=\n"
    )
    path.write_text(content, encoding="utf-8")
    print(f"[OK] Template opgeslagen: {path.resolve()}")


def main() -> int:
    print("VDK XS2A Setup Helper (read-only)\n")
    print("Portal:", PORTAL_URL)
    print(
        "\nBenodigd uit het VDK XS2A portal:"
        "\n1. Base URL van jouw environment"
        "\n2. Client ID"
        "\n3. Token/API key (of access token)"
        "\n4. Password alleen indien jouw VDK setup dit vereist\n"
    )

    base_url = sanitize_base_url(prompt("VDK Base URL (zonder trailing slash)"))
    if not base_url:
        print("Base URL is verplicht.")
        return 1
    client_id = prompt("VDK Client ID")
    api_key = getpass("VDK API key / Bearer token (input hidden, enter=overslaan): ").strip()
    password = getpass("VDK password (optioneel, input hidden, enter=overslaan): ").strip()

    cfg = VDKConfig(
        base_url=base_url,
        client_id=client_id,
        api_key=api_key,
        password=password,
    )

    print_result(cfg)

    if prompt_yes_no("\nRead-only test call doen naar /accounts?", default=True):
        probe_accounts(cfg)

    maybe_write_template(cfg)

    print("\nKlaar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

