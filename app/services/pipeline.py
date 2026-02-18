import json
import re

from sqlalchemy.orm import Session

from app.config import settings
from sqlalchemy import func

from app.db import upsert_search_index
from app.models import CategoryCatalog, Document
from app.services.ai_extractor import get_ai_extractor
from app.services.integration_settings import get_runtime_settings
from app.services.ocr.google_provider import GoogleOCRProvider
from app.services.ocr.openai_provider import OpenAIOCRProvider
from app.services.ocr.openrouter_provider import OpenRouterOCRProvider
from app.services.ocr.textract_provider import TextractOCRProvider
from app.services.thumbnail_service import ThumbnailService


def _normalize_structured_reference(value: str | None) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    # Strip common wrappers like +++...+++ or ***...***
    stripped = raw.replace("+", " ").replace("*", " ")
    m = re.search(r"(\d{3})\s*/\s*(\d{4})\s*/\s*(\d{5})", stripped)
    if m:
        return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    # Fallback: compact digits then reformat if exactly 12 digits.
    digits = re.sub(r"[^0-9]", "", raw)
    if len(digits) == 12:
        return f"{digits[:3]}/{digits[3:7]}/{digits[7:]}"
    return None


def _extract_structured_reference_from_text(text: str | None) -> str | None:
    if not text:
        return None
    # Prefer explicit pattern with optional Belgian wrappers.
    m = re.search(
        r"(?:\+{3}|\*{3})?\s*(\d{3})\s*/\s*(\d{4})\s*/\s*(\d{5})\s*(?:\+{3}|\*{3})?",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    # Secondary pass: only trigger near typical wording to avoid random numbers.
    near = re.search(
        r"(overschrijvingsopdracht|gestructureerde\s+mededeling|mededeling)[^0-9]{0,120}(\d{3}\s*/\s*\d{4}\s*/\s*\d{5})",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if near:
        return _normalize_structured_reference(near.group(2))
    return None


def _get_ocr_provider(provider_name: str, runtime: dict):
    provider = str(provider_name or runtime.get("default_ocr_provider") or settings.ocr_provider).strip().lower()
    if provider in {"llm_vision", "openrouter"}:
        ai_provider = str(runtime.get("ai_provider") or settings.ai_provider or "openrouter").strip().lower()
        if ai_provider == "gemini":
            ai_provider = "google"
        if ai_provider == "openai":
            return OpenAIOCRProvider(
                api_key=runtime.get("openai_api_key"),
                model=runtime.get("openai_ocr_model"),
            )
        if ai_provider == "google":
            return GoogleOCRProvider(
                api_key=runtime.get("google_api_key"),
                model=runtime.get("google_ocr_model"),
            )
        return OpenRouterOCRProvider(
            api_key=runtime.get("openrouter_api_key"),
            model=runtime.get("openrouter_ocr_model"),
        )

    return TextractOCRProvider(
        region=runtime.get("aws_region"),
        access_key=runtime.get("aws_access_key_id"),
        secret_key=runtime.get("aws_secret_access_key"),
    )


def process_document(db: Session, document_id: str, ocr_provider_name: str | None = None, force: bool = False) -> None:
    doc = db.get(Document, document_id)
    if not doc:
        return
    if doc.deleted_at is not None:
        return

    # Prevent costly re-processing for already parsed documents unless forced.
    if not force and doc.status == "ready" and bool(doc.ocr_processed):
        return

    doc.status = "processing"
    doc.error_message = None
    if force:
        doc.ocr_processed = False
        doc.ai_processed = False
    db.commit()

    try:
        runtime = get_runtime_settings(db)
        ocr_provider = _get_ocr_provider(ocr_provider_name or "", runtime)
        thumbnail_service = ThumbnailService()

        thumb_name = f"{doc.id}.jpg"
        thumb_fs_path = f"{settings.thumbnails_dir}/{thumb_name}"
        thumbnail_service.create_thumbnail(doc.file_path, doc.content_type, thumb_fs_path)

        ocr_text = ocr_provider.extract_text(doc.file_path, doc.content_type)
        doc.ocr_processed = True

        metadata: dict = {}
        category_profiles: list[dict] = []
        ai_provider = str(runtime.get("ai_provider") or settings.ai_provider or "openrouter").strip().lower()
        ai_enabled = (
            (ai_provider == "openrouter" and bool(runtime.get("openrouter_api_key")))
            or (ai_provider == "openai" and bool(runtime.get("openai_api_key")))
            or (ai_provider in {"google", "gemini"} and bool(runtime.get("google_api_key")))
        )
        if ai_enabled:
            categories = db.query(CategoryCatalog).all()
            for c in categories:
                fields: list[str] = []
                parse_config: list[dict] = []
                if c.parse_config_json:
                    try:
                        loaded_cfg = json.loads(c.parse_config_json)
                        if isinstance(loaded_cfg, list):
                            seen = set()
                            for item in loaded_cfg:
                                if not isinstance(item, dict):
                                    continue
                                key = str(item.get("key", "")).strip().lower().replace(" ", "_")
                                if not key or key in seen:
                                    continue
                                seen.add(key)
                                parse_config.append(
                                    {
                                        "key": key,
                                        "visible_in_overview": bool(item.get("visible_in_overview", True)),
                                    }
                                )
                    except Exception:
                        parse_config = []
                if c.parse_fields_json:
                    try:
                        loaded = json.loads(c.parse_fields_json)
                        if isinstance(loaded, list):
                            fields = [str(x) for x in loaded]
                    except Exception:
                        fields = []
                if not fields and parse_config:
                    fields = [x["key"] for x in parse_config]
                category_profiles.append(
                    {
                        "name": c.name,
                        "prompt_template": c.prompt_template or "",
                        "parse_fields": fields,
                        "parse_config": parse_config,
                        "paid_default": bool(c.paid_default) if c.paid_default is not None else False,
                    }
                )
            extractor = get_ai_extractor(ai_provider, runtime=runtime)
            metadata = extractor.extract_metadata(
                ocr_text,
                doc.filename,
                category_profiles=category_profiles,
                preferred_category=doc.category,
            )
            doc.ai_processed = True
        else:
            doc.ai_processed = False

        doc.thumbnail_path = f"/thumbnails/{thumb_name}"
        doc.ocr_text = ocr_text
        previous_category = (doc.category or "").strip()
        extracted_category = str(metadata.get("category") or "").strip()
        if extracted_category:
            profile_names = {str(p.get("name", "")).strip().lower(): str(p.get("name", "")).strip() for p in category_profiles}
            doc.category = profile_names.get(extracted_category.lower(), extracted_category)
        elif previous_category:
            doc.category = previous_category
        doc.issuer = metadata.get("issuer")
        doc.subject = metadata.get("subject")
        doc.document_date = metadata.get("document_date")
        doc.due_date = metadata.get("due_date")
        doc.total_amount = metadata.get("total_amount")
        doc.currency = metadata.get("currency")
        doc.iban = metadata.get("iban")
        extracted_ref = _normalize_structured_reference(metadata.get("structured_reference"))
        if not extracted_ref:
            extracted_ref = _extract_structured_reference_from_text(ocr_text)
        doc.structured_reference = extracted_ref
        if metadata.get("paid") is not None:
            doc.paid = bool(metadata.get("paid"))
        if metadata.get("paid_on"):
            doc.paid_on = metadata.get("paid_on")
        if metadata.get("items") is not None:
            items = metadata.get("items")
            if isinstance(items, list):
                doc.line_items = "\n".join([str(i) for i in items if i is not None])
            else:
                doc.line_items = str(items)
        extra_fields: dict[str, str] = {}
        raw_extra = metadata.get("extra_fields")
        if isinstance(raw_extra, dict):
            extra_fields = {
                str(k).strip(): str(v).strip()
                for k, v in raw_extra.items()
                if str(k).strip() and v is not None and str(v).strip()
            }
        known_meta_keys = {
            "category",
            "issuer",
            "subject",
            "document_date",
            "due_date",
            "total_amount",
            "currency",
            "iban",
            "structured_reference",
            "paid",
            "paid_on",
            "items",
            "summary",
            "extra_fields",
        }
        for k, v in metadata.items():
            nk = str(k).strip()
            if nk in known_meta_keys:
                continue
            if not nk or v is None or not str(v).strip():
                continue
            extra_fields[nk] = str(v).strip()
        if extra_fields:
            doc.extra_fields_json = json.dumps(extra_fields, ensure_ascii=False)
        else:
            doc.extra_fields_json = None

        # Apply category defaults from DB profile and enforce parse fields.
        if doc.category:
            cat = (
                db.query(CategoryCatalog)
                .filter(func.lower(CategoryCatalog.name) == doc.category.lower())
                .first()
            )
            allowed_fields: set[str] = set()
            if cat and cat.parse_fields_json:
                try:
                    loaded = json.loads(cat.parse_fields_json)
                    if isinstance(loaded, list):
                        allowed_fields = {str(x) for x in loaded}
                except Exception:
                    allowed_fields = set()

            if allowed_fields:
                if "due_date" not in allowed_fields:
                    doc.due_date = None
                if "iban" not in allowed_fields:
                    doc.iban = None
                if "structured_reference" not in allowed_fields:
                    doc.structured_reference = None
                if "items" not in allowed_fields:
                    doc.line_items = None
                known_fields = {
                    "category",
                    "issuer",
                    "subject",
                    "document_date",
                    "due_date",
                    "total_amount",
                    "currency",
                    "iban",
                    "structured_reference",
                    "paid",
                    "paid_on",
                    "items",
                    "summary",
                }
                allowed_extra = {x for x in allowed_fields if x not in known_fields}
                if allowed_extra:
                    existing_extra: dict[str, str] = {}
                    if doc.extra_fields_json:
                        try:
                            loaded = json.loads(doc.extra_fields_json)
                            if isinstance(loaded, dict):
                                existing_extra = {
                                    str(k): str(v)
                                    for k, v in loaded.items()
                                    if str(k) in allowed_extra and v is not None and str(v).strip()
                                }
                        except Exception:
                            existing_extra = {}
                    doc.extra_fields_json = json.dumps(existing_extra, ensure_ascii=False) if existing_extra else None
                else:
                    doc.extra_fields_json = None

            if cat and cat.paid_default:
                doc.paid = True
                if not doc.paid_on and doc.document_date:
                    doc.paid_on = doc.document_date
            if doc.category.strip().lower() == "kasticket":
                doc.paid = True
                if not doc.paid_on and doc.document_date:
                    doc.paid_on = doc.document_date
                doc.due_date = None
                doc.iban = None
                doc.structured_reference = None
        summary = metadata.get("summary")
        extra_summary = ""
        if doc.extra_fields_json:
            try:
                loaded = json.loads(doc.extra_fields_json)
                if isinstance(loaded, dict):
                    extra_summary = " ".join(
                        f"{str(k)} {str(v)}" for k, v in loaded.items() if k and v is not None and str(v).strip()
                    )
            except Exception:
                extra_summary = ""

        label_text = " ".join([label.name for label in doc.labels])
        searchable = "\n".join(
            x
            for x in [
                doc.filename,
                doc.category,
                doc.issuer,
                doc.subject,
                doc.document_date,
                doc.due_date,
                doc.iban,
                doc.structured_reference,
                doc.line_items,
                extra_summary,
                summary,
                label_text,
                ocr_text,
            ]
            if x
        )
        doc.searchable_text = searchable
        doc.status = "ready"
        db.commit()

        upsert_search_index(doc.id, searchable)
    except Exception as exc:
        doc.status = "failed"
        doc.error_message = str(exc)
        db.commit()
