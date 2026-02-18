import csv
import hashlib
import io
import json
import re
import unicodedata
from datetime import datetime
from typing import Any


def _normalize_key(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", text)


def _lookup_value(row: dict[str, str], aliases: list[str], *, allow_contains: bool = True) -> str:
    if not row:
        return ""
    normalized_row = {_normalize_key(k): (v if v is not None else "") for k, v in row.items()}
    alias_norm = [_normalize_key(a) for a in aliases if _normalize_key(a)]
    for alias in alias_norm:
        if alias in normalized_row and str(normalized_row.get(alias) or "").strip():
            return str(normalized_row.get(alias) or "").strip()
    if allow_contains:
        for key, value in normalized_row.items():
            if not str(value or "").strip():
                continue
            if any(alias in key or key in alias for alias in alias_norm):
                return str(value or "").strip()
    return ""


def _normalize_amount(raw: str | None) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip().replace(" ", "")
    if not s:
        return None
    s = s.replace("EUR", "").replace("€", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _extract_amount_from_row(row: dict[str, str]) -> float | None:
    direct = _normalize_amount(
        _lookup_value(
            row,
            [
                "amount",
                "bedrag",
                "waarde",
                "amount_eur",
                "bedrag_eur",
                "transactiebedrag",
                "boekingsbedrag",
            ],
        )
    )
    if direct is not None:
        sign_hint = _lookup_value(row, ["debitcredit", "dc", "richting", "sign", "teken"])
        sign_norm = _normalize_key(sign_hint)
        if sign_norm in {"d", "debit", "debet", "af"}:
            return -abs(direct)
        if sign_norm in {"c", "credit", "bij", "in"}:
            return abs(direct)
        return direct

    # Support files that split inflow/outflow across two columns.
    debit = _normalize_amount(
        _lookup_value(
            row,
            [
                "debit",
                "debet",
                "debetbedrag",
                "uit",
                "af",
                "uitgave",
                "uitgaven",
            ],
        )
    )
    credit = _normalize_amount(
        _lookup_value(
            row,
            [
                "credit",
                "krediet",
                "kredietbedrag",
                "in",
                "bij",
                "inkomst",
                "inkomsten",
            ],
        )
    )
    if credit is not None and abs(credit) > 0:
        return abs(credit)
    if debit is not None and abs(debit) > 0:
        return -abs(debit)
    return None


def _normalize_date(raw: str | None) -> str | None:
    if not raw:
        return None
    value = str(raw).strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _build_tx_id(parts: list[str]) -> str:
    src = "|".join(parts)
    return f"imp_{hashlib.sha256(src.encode('utf-8')).hexdigest()[:24]}"


def _likely_header_line(line: str) -> bool:
    n = _normalize_key(line)
    if not n:
        return False
    hints = [
        "datum",
        "date",
        "boekingsdatum",
        "omschrijving",
        "mededeling",
        "bedrag",
        "amount",
        "debet",
        "credit",
        "krediet",
    ]
    return sum(1 for h in hints if h in n) >= 2


def _guess_delimiter(text: str) -> str:
    sample = text[:4096]
    counts = {
        ";": sample.count(";"),
        ",": sample.count(","),
        "\t": sample.count("\t"),
    }
    return max(counts, key=counts.get) if any(counts.values()) else ";"


def _split_csv_line(line: str, delimiter: str) -> list[str]:
    try:
        return next(csv.reader([line], delimiter=delimiter, quotechar='"'))
    except Exception:
        return [p.strip() for p in line.split(delimiter)]


def _find_header_index(lines: list[str], delimiter: str) -> int:
    target_headers = {
        _normalize_key("Uitvoeringsdatum"),
        _normalize_key("Valutadatum"),
        _normalize_key("VDK-refertenummer"),
        _normalize_key("Tegenpartij naam"),
        _normalize_key("Mededeling"),
        _normalize_key("Bedrag"),
    }
    for i, line in enumerate(lines[:120]):
        parts = [p.strip().strip('"') for p in _split_csv_line(line, delimiter)]
        if len(parts) < 4:
            continue
        normalized = {_normalize_key(p) for p in parts if _normalize_key(p)}
        hit_count = len(normalized.intersection(target_headers))
        if hit_count >= 3:
            return i
        if _likely_header_line(line):
            return i
    return 0


def _parse_csv_preamble_metadata(lines: list[str], delimiter: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in lines:
        raw = str(line or "").strip()
        if not raw:
            continue
        parts = [p.strip().strip('"') for p in _split_csv_line(raw, delimiter)]
        parts = [p for p in parts if p]
        if len(parts) < 2:
            continue
        key = parts[0]
        value = " | ".join(parts[1:]).strip()
        if not key or not value:
            continue
        if key in meta:
            meta[key] = f"{meta[key]} | {value}"
        else:
            meta[key] = value
    return meta


def _parse_csv_line_fallback(text: str) -> list[dict[str, Any]]:
    delimiter = _guess_delimiter(text)
    lines = [ln.strip() for ln in text.splitlines() if ln and ln.strip()]
    out: list[dict[str, Any]] = []
    for idx, line in enumerate(lines):
        if _likely_header_line(line):
            continue
        parts = [p.strip() for p in line.split(delimiter)]
        if len(parts) < 2:
            continue

        date_val = None
        amounts: list[float] = []
        text_parts: list[str] = []
        for p in parts:
            d = _normalize_date(p)
            if d and not date_val:
                date_val = d
                continue
            a = _normalize_amount(p)
            if a is not None:
                amounts.append(a)
                continue
            if p:
                text_parts.append(p)

        if not date_val and not amounts and not text_parts:
            continue

        amount_val = None
        if amounts:
            # Prefer last numeric amount in a bank row.
            amount_val = amounts[-1]

        counterparty = text_parts[0] if text_parts else None
        remittance = " | ".join(text_parts[1:]) if len(text_parts) > 1 else (text_parts[0] if text_parts else None)
        tx_id = _build_tx_id([str(idx), date_val or "", str(amount_val or ""), counterparty or "", remittance or ""])
        out.append(
            {
                "external_transaction_id": tx_id,
                "booking_date": date_val,
                "value_date": None,
                "amount": amount_val,
                "currency": "EUR",
                "counterparty_name": counterparty,
                "remittance_information": remittance,
                "raw_json": "",
            }
        )
    return out


def parse_csv_transactions(content: bytes, filename: str = "") -> list[dict[str, Any]]:
    text = content.decode("utf-8-sig", errors="ignore")
    lines = text.splitlines()
    delimiter = _guess_delimiter(text)
    header_idx = _find_header_index(lines, delimiter)
    preamble_meta = _parse_csv_preamble_metadata(lines[:header_idx], delimiter) if header_idx > 0 else {}
    sliced = "\n".join(lines[header_idx:]) if lines else text
    stream = io.StringIO(sliced)

    reader = csv.DictReader(stream, delimiter=delimiter)
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(reader):
        if not row:
            continue
        cleaned = {str(k or "").strip(): (v if v is not None else "") for k, v in row.items()}
        booking_date = _normalize_date(
            _lookup_value(
                cleaned,
                [
                    "booking_date",
                    "bookdate",
                    "date",
                    "boekingsdatum",
                    "boekdatum",
                    "datum",
                    "transactiedatum",
                    "uitvoeringsdatum",
                ],
            )
        )
        value_date = _normalize_date(
            _lookup_value(cleaned, ["value_date", "valutadatum", "valuedate", "valuta_datum"])
        )
        amount = _extract_amount_from_row(cleaned)
        currency = (
            _lookup_value(cleaned, ["currency", "valuta", "munt"], allow_contains=False)
            or "EUR"
        ).strip().upper() or "EUR"
        # Prefer real counterparty names over account identifiers (IBAN/tegenrekening).
        counterparty_name = _lookup_value(
            cleaned,
            [
                "counterparty_name",
                "counterparty",
                "tegenpartij_naam",
                "tegenpartij naam",
                "tegenpartij",
                "begunstigde_naam",
                "begunstigde naam",
                "begunstigde",
                "naam",
            ],
        ).strip()
        counterparty_account = _lookup_value(
            cleaned,
            ["tegenrekening", "counterparty_account", "iban", "rekeningnummer", "rekening"],
        ).strip()
        counterparty = counterparty_name or counterparty_account
        remittance = _lookup_value(
            cleaned,
            ["description", "mededeling", "omschrijving", "remittance", "remittance_information", "referentie"],
        ).strip()
        tx_id = _lookup_value(
            cleaned,
            [
                "transaction_id",
                "id",
                "entry_reference",
                "referentie_id",
                "boekingid",
                "vdk-refertenummer",
                "vdk_refertenummer",
            ],
        ).strip()
        if not tx_id:
            tx_id = _build_tx_id([
                str(idx),
                booking_date or "",
                str(amount if amount is not None else ""),
                currency,
                counterparty,
                remittance,
            ])
        raw_payload = {
            "source_filename": str(filename or "").strip(),
            "csv_metadata": preamble_meta,
            "csv_fields": cleaned,
        }
        out.append(
            {
                "external_transaction_id": tx_id,
                "booking_date": booking_date,
                "value_date": value_date,
                "amount": amount,
                "currency": currency,
                "counterparty_name": counterparty or None,
                "remittance_information": remittance or None,
                "raw_json": json.dumps(raw_payload, ensure_ascii=False),
            }
        )
    quality_ok = out and any(t.get("amount") is not None for t in out) and any(
        (t.get("booking_date") or t.get("counterparty_name") or t.get("remittance_information"))
        for t in out
    )
    if quality_ok:
        return out

    fallback = _parse_csv_line_fallback(text)
    if fallback:
        return fallback
    return out


def parse_coda_transactions(content: bytes) -> list[dict[str, Any]]:
    """
    Best-effort CODA fallback parser.
    It parses movement-like lines and extracts date/amount/description heuristically.
    """
    text = content.decode("latin-1", errors="ignore")
    lines = [ln.rstrip("\n\r") for ln in text.splitlines()]
    out: list[dict[str, Any]] = []

    date_re = re.compile(r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|\d{8})")
    amount_re = re.compile(r"([+-]?\d+[\.,]\d{2})")

    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        # Common CODA records: movement and information blocks often begin with 2/21/22/23
        if not (line.startswith("2") or line.startswith("3")):
            continue

        date_match = date_re.search(line)
        booking_date = None
        if date_match:
            raw_date = date_match.group(1)
            if len(raw_date) == 8 and raw_date.isdigit():
                booking_date = _normalize_date(f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}")
            else:
                booking_date = _normalize_date(raw_date)

        amount_match = amount_re.search(line)
        amount = _normalize_amount(amount_match.group(1) if amount_match else None)

        remittance = re.sub(r"\s+", " ", line[10:]).strip() if len(line) > 10 else line.strip()
        tx_id = _build_tx_id([str(idx), booking_date or "", str(amount if amount is not None else ""), remittance])

        out.append(
            {
                "external_transaction_id": tx_id,
                "booking_date": booking_date,
                "value_date": None,
                "amount": amount,
                "currency": "EUR",
                "counterparty_name": None,
                "remittance_information": remittance or None,
                "raw_json": "",
            }
        )

    return out


def parse_imported_transactions(filename: str, content: bytes) -> tuple[str, list[dict[str, Any]]]:
    lower = (filename or "").lower()
    if lower.endswith(".coda"):
        return "coda", parse_coda_transactions(content)
    return "csv", parse_csv_transactions(content, filename=filename)
