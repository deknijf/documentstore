"""A PDF that already carries its own text is never rasterised.

The scan pipeline exists for photographs of paper. On a born-digital invoice it
has nothing to deskew and only replaces selectable text with a JPEG.
"""

from pathlib import Path

import pytest

from app.config import settings
from app.services.doc_preprocess import ensure_preprocessed_document
from app.services.pdf_text import has_usable_text_layer

INVOICE_LINES = [
    "Energieleverancier BV, Voorbeeldstraat 12, 9000 Gent",
    "Factuurnummer 2025-000481 van 4 maart 2025",
    "Klantnummer 88213 voor de levering van elektriciteit en aardgas",
    "Verbruiksperiode van 1 januari tot en met 28 februari",
    "Bedrag te betalen tweehonderdvierenveertig euro en zestig cent",
    "Rekeningnummer BE68 5390 0754 7034 bij de bank van de leverancier",
    "Gestructureerde mededeling 090 0004 81036 vermelden bij betaling",
]


def _write_text_pdf(path: Path, *, pages: int = 1, text_pages: int | None = None) -> Path:
    import fitz

    text_pages = pages if text_pages is None else text_pages
    document = fitz.open()
    for index in range(pages):
        page = document.new_page()
        if index < text_pages:
            y = 60
            for _ in range(4):
                for line in INVOICE_LINES:
                    page.insert_text((50, y), line, fontsize=9)
                    y += 12
    document.save(str(path))
    document.close()
    return path


def _write_image_only_pdf(path: Path) -> Path:
    import fitz

    from tests.conftest import TINY_JPEG

    document = fitz.open()
    page = document.new_page()
    page.insert_image(fitz.Rect(0, 0, 200, 200), stream=TINY_JPEG)
    document.save(str(path))
    document.close()
    return path


class _Doc:
    """Minimal stand-in for the Document fields ensure_preprocessed_document reads."""

    def __init__(self, doc_id: str, path: Path):
        self.id = doc_id
        self.file_path = str(path)
        self.content_type = "application/pdf"
        self.original_file_path = str(path)
        self.original_content_type = "application/pdf"
        self.preprocessed_file_path = None
        self.preprocessed_content_type = None


def test_born_digital_pdf_has_a_usable_text_layer(tmp_path):
    pdf = _write_text_pdf(tmp_path / "invoice.pdf")
    assert has_usable_text_layer(pdf, min_quality=settings.pdf_text_layer_min_quality)


def test_image_only_pdf_has_no_usable_text_layer(tmp_path):
    pdf = _write_image_only_pdf(tmp_path / "scan.pdf")
    assert not has_usable_text_layer(pdf, min_quality=settings.pdf_text_layer_min_quality)


def test_a_digital_cover_page_in_front_of_scans_still_needs_ocr(tmp_path):
    # One page of text, four without: the document as a whole is a scan.
    pdf = _write_text_pdf(tmp_path / "mixed.pdf", pages=5, text_pages=1)
    assert not has_usable_text_layer(pdf, min_quality=settings.pdf_text_layer_min_quality)


def test_a_thin_text_layer_is_not_trusted(tmp_path):
    """Enough text to count as a page with text, too little to rely on.

    A scanner that stamps a header onto every page would otherwise pass the
    page-coverage check.
    """
    import fitz

    from app.services.pdf_text import _MIN_CHARS_PER_PAGE
    from app.services.text_quality import ocr_quality_score

    document = fitz.open()
    page = document.new_page()
    page.insert_text((50, 60), "Factuur 2025 van de leverancier, pagina een", fontsize=9)
    page.insert_text((50, 75), "Klantnummer 88213 en verder geen inhoud", fontsize=9)
    document.save(str(tmp_path / "thin.pdf"))
    document.close()

    from app.services.pdf_text import _page_texts

    text = "\n".join(_page_texts(tmp_path / "thin.pdf"))
    assert len(text.strip()) >= _MIN_CHARS_PER_PAGE, "must clear the page-coverage gate"
    assert ocr_quality_score(text) < 0.62, "must fail on quality, not on coverage"
    assert not has_usable_text_layer(tmp_path / "thin.pdf", min_quality=0.62)


def test_an_unreadable_file_is_not_trusted(tmp_path):
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 dit is geen geldige pdf")
    assert not has_usable_text_layer(broken, min_quality=0.62)


def test_born_digital_pdf_is_not_rasterised(tmp_path):
    pdf = _write_text_pdf(tmp_path / "invoice.pdf")
    doc = _Doc("born-1", pdf)
    path, content_type, used_preprocessed = ensure_preprocessed_document(doc)

    assert used_preprocessed is False, "a text PDF must not get a raster derivative"
    assert Path(path) == pdf, "processing must use the original file"
    assert content_type == "application/pdf"
    assert not (Path(settings.preprocessed_dir) / "born-1_preprocessed.pdf").exists()


def test_scanned_pdf_is_still_rasterised(tmp_path):
    pdf = _write_image_only_pdf(tmp_path / "scan.pdf")
    doc = _Doc("scan-1", pdf)
    path, content_type, used_preprocessed = ensure_preprocessed_document(doc)

    assert used_preprocessed is True
    assert Path(path) != pdf
    assert content_type == "application/pdf"


def test_the_rule_can_be_switched_off(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pdf_text_layer_enabled", False)
    pdf = _write_text_pdf(tmp_path / "invoice.pdf")
    doc = _Doc("off-1", pdf)
    _, _, used_preprocessed = ensure_preprocessed_document(doc)
    assert used_preprocessed is True


def test_an_existing_derivative_is_abandoned_for_a_text_pdf(tmp_path):
    """A document preprocessed before this rule existed must stop using it."""
    pdf = _write_text_pdf(tmp_path / "invoice.pdf")
    stale = Path(settings.preprocessed_dir) / "stale-1_preprocessed.pdf"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_bytes(pdf.read_bytes())

    doc = _Doc("stale-1", pdf)
    doc.preprocessed_file_path = str(stale)
    doc.preprocessed_content_type = "application/pdf"

    path, _, used_preprocessed = ensure_preprocessed_document(doc)
    assert used_preprocessed is False
    assert Path(path) == pdf


def test_pipeline_clears_a_stale_derivative(tmp_path):
    from app.services.pipeline import _drop_preprocessed_derivative

    stale = Path(settings.preprocessed_dir) / "dropme_preprocessed.pdf"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_bytes(b"%PDF-1.4\n")

    doc = _Doc("dropme", tmp_path / "invoice.pdf")
    doc.preprocessed_file_path = str(stale)
    doc.preprocessed_content_type = "application/pdf"

    _drop_preprocessed_derivative(doc)
    assert doc.preprocessed_file_path is None
    assert doc.preprocessed_content_type is None
    assert not stale.exists()


def test_pipeline_never_deletes_outside_the_preprocessed_directory(tmp_path):
    from app.services.pipeline import _drop_preprocessed_derivative

    outside = tmp_path / "origineel.pdf"
    outside.write_bytes(b"%PDF-1.4\n")
    doc = _Doc("guard", outside)
    doc.preprocessed_file_path = str(outside)

    _drop_preprocessed_derivative(doc)
    assert outside.exists(), "only files inside the preprocessed directory may be removed"


@pytest.mark.parametrize("quality", [0.0, 0.62])
def test_quality_threshold_is_honoured(tmp_path, quality):
    pdf = _write_image_only_pdf(tmp_path / "scan.pdf")
    # An image-only PDF has no text at all, so no threshold makes it usable.
    assert not has_usable_text_layer(pdf, min_quality=quality)


def test_processing_a_text_pdf_clears_a_stale_derivative(client, tenant_a, monkeypatch):
    """The pipeline must actually drop the pointer, not just be able to."""
    import app.services.pipeline as pipeline
    from app.db import SessionLocal
    from app.models import Document
    from tests.conftest import make_document

    class _StubOCR:
        def extract_text(self, path, content_type):
            return "tekst uit de stub"

    monkeypatch.setattr(pipeline, "_get_ocr_provider", lambda *a, **k: _StubOCR())

    document_id = make_document(tenant_a)
    born = Path(settings.uploads_dir) / f"{document_id}_original.pdf"
    _write_text_pdf(born)

    stale = Path(settings.preprocessed_dir) / f"{document_id}_preprocessed.pdf"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_bytes(b"%PDF-1.4\n")

    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        doc.file_path = str(born)
        doc.original_file_path = str(born)
        doc.preprocessed_file_path = str(stale)
        doc.preprocessed_content_type = "application/pdf"
        doc.status = "uploaded"
        doc.ocr_processed = False
        db.commit()

        pipeline.process_document(db, document_id, force=True)

        doc = db.get(Document, document_id)
        assert doc.status == "ready", doc.error_message
        assert doc.preprocessed_file_path is None
        assert doc.preprocessed_content_type is None
    finally:
        db.close()
    assert not stale.exists(), "the unused derivative should be removed"
