from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.models import Document
from app.services.document_conversion import (
    convert_pdf_file_to_optimized_pdf,
    convert_image_file_to_pdf,
    is_convertible_image_content_type,
)


def _safe_content_type(value: str | None) -> str:
    return str(value or "").strip().lower()


def _doc_base_name(doc: Document) -> str:
    return str(getattr(doc, "id", "") or "").strip() or "document"


def _preprocessed_path_for(doc: Document) -> Path:
    return Path(settings.preprocessed_dir) / f"{_doc_base_name(doc)}_preprocessed.pdf"


def _is_usable_file(path_value: str | None) -> bool:
    if not path_value:
        return False
    try:
        return Path(path_value).exists()
    except Exception:
        return False


def original_source_for(doc: Document) -> tuple[str, str]:
    """
    Resolve the best original source for preprocessing.
    Falls back to active document path/content_type when legacy rows don't have original_* fields.
    """
    original_path = str(getattr(doc, "original_file_path", "") or "").strip()
    original_type = _safe_content_type(getattr(doc, "original_content_type", None))
    if _is_usable_file(original_path):
        return original_path, (original_type or _safe_content_type(getattr(doc, "content_type", None)))
    return str(getattr(doc, "file_path", "") or ""), _safe_content_type(getattr(doc, "content_type", None))


def ensure_preprocessed_document(doc: Document, rebuild: bool = False) -> tuple[str, str, bool]:
    """
    Return the file path/content-type to use for OCR + thumbnail generation.
    - If DOC_PREPROCESS_ENABLED is off: return active file as-is.
    - If enabled and source is an image: try convert to PDF and return that.
    - On conversion failure: return original file (safe fallback).
    """
    current_path = str(getattr(doc, "file_path", "") or "")
    current_type = _safe_content_type(getattr(doc, "content_type", None))
    if not settings.doc_preprocess_enabled:
        return current_path, current_type, False

    source_path, source_type = original_source_for(doc)
    if not source_path:
        return current_path, current_type, False

    target = _preprocessed_path_for(doc)
    preprocessed_path = str(getattr(doc, "preprocessed_file_path", "") or "").strip()
    preprocessed_type = _safe_content_type(getattr(doc, "preprocessed_content_type", None))
    if not rebuild and _is_usable_file(preprocessed_path):
        return preprocessed_path, (preprocessed_type or "application/pdf"), True

    if is_convertible_image_content_type(source_type):
        convert_image_file_to_pdf(source_path, target)
        return str(target), "application/pdf", True
    if source_type == "application/pdf" and settings.doc_preprocess_pdf_enabled:
        convert_pdf_file_to_optimized_pdf(source_path, target)
        return str(target), "application/pdf", True
    return current_path, current_type, False
