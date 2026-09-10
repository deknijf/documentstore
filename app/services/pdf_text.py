"""Deciding whether a PDF already carries its own text.

Almost every invoice from a utility, telecom provider or insurer is
born-digital: the file already contains exact, selectable text. Running it
through the scan pipeline has nothing to deskew or de-shadow and only replaces
that text with a JPEG.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from app.services.text_quality import ocr_quality_score

# A page below this is treated as having no text: scans often carry only a
# stray header or a page number.
_MIN_CHARS_PER_PAGE = 50
# A digital cover page in front of scanned pages must still go through OCR, so
# most pages have to carry text before the layer counts as usable.
_MIN_PAGE_COVERAGE = 0.8


def _page_text(page) -> str:
    """Text of one page, top-to-bottom and left-to-right.

    get_text() on its own can interleave columns on invoices that put totals in
    a side panel, so blocks are sorted by position instead.
    """
    try:
        blocks = [b for b in page.get_text("blocks") if len(b) >= 5 and str(b[4]).strip()]
    except Exception:
        return str(page.get_text() or "")
    blocks.sort(key=lambda b: (round(float(b[1]), 1), round(float(b[0]), 1)))
    return "\n".join(str(b[4]).strip() for b in blocks)


def _page_texts(path: str | Path) -> list[str]:
    with fitz.open(str(path)) as document:
        return [_page_text(page) for page in document]


def has_usable_text_layer(path: str | Path, *, min_quality: float) -> bool:
    """True when the PDF's own text is complete and rich enough to rely on."""
    try:
        pages = _page_texts(path)
    except Exception:
        return False
    if not pages:
        return False
    with_text = sum(1 for page in pages if len(page.strip()) >= _MIN_CHARS_PER_PAGE)
    if (with_text / len(pages)) < _MIN_PAGE_COVERAGE:
        return False
    return ocr_quality_score("\n".join(pages)) >= float(min_quality)
