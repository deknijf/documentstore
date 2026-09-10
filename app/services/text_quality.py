"""How much usable text an extraction produced.

Shared by the OCR fallback in the pipeline and by the check that decides
whether a PDF's own text layer is good enough to trust.
"""

import re


def ocr_quality_score(text: str | None) -> float:
    raw = str(text or "").strip()
    if not raw:
        return 0.0
    compact = re.sub(r"\s+", " ", raw).strip()
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-/\.,:]{1,}", compact)
    letters = re.findall(r"[A-Za-zÀ-ÿ]", compact)
    chars = len(compact)
    line_count = len(lines)
    word_count = len(words)
    letter_ratio = (len(letters) / chars) if chars else 0.0

    score = 0.0
    # Enough signal in extracted text.
    score += min(0.35, chars / 2400.0)
    score += min(0.20, line_count / 28.0)
    score += min(0.20, word_count / 220.0)
    # OCR garbage often has too little alphabetic density.
    if letter_ratio >= 0.45:
        score += 0.18
    elif letter_ratio >= 0.30:
        score += 0.1
    # Bonus for structured content patterns commonly present in invoices/bills.
    if re.search(r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{8,}\b", compact):
        score += 0.04
    if re.search(r"\b\d{2}[/-]\d{2}[/-]\d{2,4}\b", compact):
        score += 0.03

    return round(min(1.0, score), 4)
