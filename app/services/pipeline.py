import json
import hashlib
import re
import uuid
from datetime import datetime
from difflib import SequenceMatcher

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.config import settings
from app.db import upsert_search_index
from app.models import BankCategoryMapping, Document, CategoryCatalog, ExtractionHint, Group, Label
from app.services.ai_extractor import get_ai_extractor
from app.services.bank_budget_ai import _call_llm
from app.services.integration_settings import get_runtime_settings
from app.services.ocr.google_provider import GoogleOCRProvider
from app.services.ocr.openai_provider import OpenAIOCRProvider
from app.services.ocr.openrouter_provider import OpenRouterOCRProvider
from app.services.ocr.textract_provider import TextractOCRProvider
from app.services.thumbnail_service import ThumbnailService


def _normalize_ocr_text_for_hash(text: str | None) -> str:
    t = str(text or "").lower()
    t = re.sub(r"\\s+", " ", t).strip()
    return t


def _ocr_text_hash(text: str | None) -> str | None:
    norm = _normalize_ocr_text_for_hash(text)
    if not norm:
        return None
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


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


def _normalize_iban(value: str | None) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()


def _iban_checksum_valid(iban: str | None) -> bool:
    normalized = _normalize_iban(iban)
    if len(normalized) < 15 or len(normalized) > 34:
        return False
    if not re.match(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]+$", normalized):
        return False
    rearranged = normalized[4:] + normalized[:4]
    converted = []
    for ch in rearranged:
        if ch.isalpha():
            converted.append(str(ord(ch) - 55))
        else:
            converted.append(ch)
    try:
        return int("".join(converted)) % 97 == 1
    except Exception:
        return False


def _is_iso_date(value: str | None) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return True
    except Exception:
        return False


def _contains_date_variant(ocr_text: str, iso_date: str) -> bool:
    if not iso_date or not ocr_text:
        return False
    raw = str(ocr_text or "")
    if iso_date in raw:
        return True
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
        dmy = dt.strftime("%d/%m/%Y")
        dmy_dash = dt.strftime("%d-%m-%Y")
        ymd_slash = dt.strftime("%Y/%m/%d")
        return any(x in raw for x in [dmy, dmy_dash, ymd_slash])
    except Exception:
        return False


def _amount_appears_in_text(amount: float | int | None, ocr_text: str | None) -> bool:
    if amount is None:
        return False
    raw = str(ocr_text or "")
    try:
        val = float(amount)
    except Exception:
        return False
    if not raw.strip():
        return False
    candidates = {
        f"{val:.2f}",
        f"{val:.1f}",
        str(int(val)) if float(val).is_integer() else "",
    }
    amount_comma = f"{val:.2f}".replace(".", ",")
    candidates.update(
        {
            amount_comma,
            amount_comma.replace(",", "."),
            amount_comma.replace(",", ""),
            f"{val:.2f}".replace(".", ""),
        }
    )
    candidates = {c for c in candidates if c}
    return any(c in raw for c in candidates)


def _build_field_confidence(doc: Document, ocr_text: str | None) -> dict[str, dict]:
    text = str(ocr_text or "")
    lower_text = text.lower()
    conf: dict[str, dict] = {}

    if doc.category:
        cat = str(doc.category).strip()
        score = 0.58
        reasons = ["Categorie herkend."]
        if cat and cat.lower() in lower_text:
            score += 0.28
            reasons.append("Categoriebenaming teruggevonden in OCR-tekst.")
        conf["category"] = {"score": round(min(1.0, score), 2), "reason": " ".join(reasons), "source": "ocr_ai"}

    if doc.total_amount is not None:
        score = 0.55
        reasons = ["Bedrag numeriek herkend."]
        if doc.currency:
            score += 0.12
            reasons.append("Valuta aanwezig.")
        if _amount_appears_in_text(doc.total_amount, text):
            score += 0.25
            reasons.append("Bedrag teruggevonden in OCR-tekst.")
        conf["total_amount"] = {"score": round(min(1.0, score), 2), "reason": " ".join(reasons), "source": "ocr_ai"}

    normalized_iban = _normalize_iban(doc.iban)
    if normalized_iban:
        score = 0.45
        reasons = ["IBAN patroon herkend."]
        if _iban_checksum_valid(normalized_iban):
            score += 0.35
            reasons.append("IBAN checksum geldig.")
        if normalized_iban in _normalize_iban(text):
            score += 0.15
            reasons.append("IBAN teruggevonden in OCR-tekst.")
        conf["iban"] = {"score": round(min(1.0, score), 2), "reason": " ".join(reasons), "source": "ocr_ai"}

    if doc.structured_reference:
        score = 0.45
        reasons = []
        if re.match(r"^\d{3}/\d{4}/\d{5}$", str(doc.structured_reference or "").strip()):
            score += 0.35
            reasons.append("Belgisch formaat 3/4/5 geldig.")
        if str(doc.structured_reference) in text:
            score += 0.15
            reasons.append("Referentie teruggevonden in OCR-tekst.")
        conf["structured_reference"] = {
            "score": round(min(1.0, score), 2),
            "reason": " ".join(reasons) or "Gestructureerde mededeling herkend.",
            "source": "ocr_ai",
        }

    for key in ["document_date", "due_date", "paid_on"]:
        value = getattr(doc, key, None)
        if not value:
            continue
        score = 0.35
        reasons = []
        if _is_iso_date(value):
            score += 0.4
            reasons.append("Geldig ISO datumformaat.")
            if _contains_date_variant(text, value):
                score += 0.2
                reasons.append("Datum teruggevonden in OCR-tekst.")
        conf[key] = {"score": round(min(1.0, score), 2), "reason": " ".join(reasons), "source": "ocr_ai"}

    if doc.issuer:
        score = 0.45
        reasons = ["Afzender herkend."]
        issuer = str(doc.issuer).strip().lower()
        if issuer and issuer in text.lower():
            score += 0.25
            reasons.append("Afzender teruggevonden in OCR-tekst.")
        conf["issuer"] = {"score": round(min(1.0, score), 2), "reason": " ".join(reasons), "source": "ocr_ai"}

    if doc.subject:
        score = 0.5
        reasons = ["Onderwerp herkend."]
        if len(str(doc.subject).strip()) >= 8:
            score += 0.15
        conf["subject"] = {"score": round(min(1.0, score), 2), "reason": " ".join(reasons), "source": "ocr_ai"}

    if getattr(doc, "extra_fields_json", None):
        try:
            loaded = json.loads(str(doc.extra_fields_json or ""))
            if isinstance(loaded, dict):
                for k, v in loaded.items():
                    key = str(k).strip()
                    value = str(v).strip() if v is not None else ""
                    if not key or not value:
                        continue
                    score = 0.52
                    reasons = ["Aangepast veld herkend."]
                    if len(value) >= 4:
                        score += 0.1
                    if value.lower() in lower_text:
                        score += 0.28
                        reasons.append("Waarde teruggevonden in OCR-tekst.")
                    conf[key] = {
                        "score": round(min(1.0, score), 2),
                        "reason": " ".join(reasons),
                        "source": "ocr_ai",
                    }
        except Exception:
            pass

    return conf


def _normalize_training_value(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    raw = re.sub(r"\s+", " ", raw)
    raw = re.sub(r"[^\w\s/\-\.]", "", raw)
    return raw.strip()


def _similar_enough(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) >= 5 and (a in b or b in a):
        return True
    return SequenceMatcher(None, a, b).ratio() >= 0.92


def _apply_extraction_hints(
    db: Session,
    *,
    tenant_id: str,
    category: str | None,
    metadata: dict,
) -> dict[str, dict]:
    """
    Reuse manual correction history as lightweight training:
    if extracted value looks like a previously corrected old_value, replace with new_value.
    """
    if not tenant_id or not isinstance(metadata, dict):
        return {}
    hint_applied: dict[str, dict] = {}
    trainable = {
        "issuer",
        "subject",
        "category",
        "document_date",
        "due_date",
        "total_amount",
        "currency",
        "iban",
        "structured_reference",
    }
    rows = (
        db.query(ExtractionHint)
        .filter(ExtractionHint.tenant_id == tenant_id)
        .order_by(ExtractionHint.created_at.desc())
        .limit(1000)
        .all()
    )
    for field in trainable:
        raw = metadata.get(field)
        raw_s = "" if raw is None else str(raw).strip()
        if not raw_s:
            continue
        n_raw = _normalize_training_value(raw_s)
        if not n_raw:
            continue
        for h in rows:
            if str(getattr(h, "field_key", "") or "").strip() != field:
                continue
            if not str(getattr(h, "new_value", "") or "").strip():
                continue
            hint_category = str(getattr(h, "category", "") or "").strip().lower()
            if category and hint_category and hint_category != str(category).strip().lower():
                continue
            old_v = str(getattr(h, "old_value", "") or "").strip()
            if not old_v:
                continue
            n_old = _normalize_training_value(old_v)
            if not _similar_enough(n_raw, n_old):
                continue
            new_v = str(getattr(h, "new_value", "") or "").strip()
            if not new_v:
                continue
            if _normalize_training_value(new_v) == n_raw:
                # Same value as already extracted, still mark as reinforced learning.
                hint_applied[field] = {
                    "score": 0.97,
                    "reason": "Bevestigd door eerdere manuele validatie.",
                    "source": "hint",
                }
            else:
                metadata[field] = new_v
                hint_applied[field] = {
                    "score": 0.95,
                    "reason": f"Gecorrigeerd via eerdere manuele validatie ({old_v} -> {new_v}).",
                    "source": "hint",
                }
            break
    return hint_applied


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


def _ensure_tenant_default_group_id(db: Session, *, tenant_id: str) -> str | None:
    """
    Labels require a group_id (legacy). When group access control is disabled, we still
    keep a stable per-tenant group to attach labels/documents to.
    """
    if not tenant_id:
        return None
    g = (
        db.query(Group)
        .filter(Group.tenant_id == tenant_id)
        .filter(func.lower(Group.name).like("gebruikers%"))
        .order_by(Group.created_at.asc())
        .first()
    )
    if not g:
        g = (
            db.query(Group)
            .filter(Group.tenant_id == tenant_id)
            .filter(func.lower(Group.name).like("users%"))
            .order_by(Group.created_at.asc())
            .first()
        )
    return str(getattr(g, "id", "") or "").strip() or None


def _ensure_doc_has_label(db: Session, *, doc: Document, label_name: str) -> None:
    name = str(label_name or "").strip()
    if not name:
        return
    group_id = str(getattr(doc, "group_id", "") or "").strip() or _ensure_tenant_default_group_id(db, tenant_id=str(doc.tenant_id or ""))
    if not group_id:
        return
    # Labels are tenant-wide (unique on normalized name). Never key on group_id here.
    label = (
        db.query(Label)
        .filter(Label.tenant_id == doc.tenant_id, func.lower(func.trim(Label.name)) == name.strip().lower())
        .first()
    )
    if not label:
        db.execute(
            text(
                """
                INSERT OR IGNORE INTO labels (id, tenant_id, name, group_id, created_at)
                VALUES (:id, :tenant_id, :name, :group_id, CURRENT_TIMESTAMP)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": str(doc.tenant_id),
                "name": name,
                "group_id": group_id,
            },
        )
        label = (
            db.query(Label)
            .filter(Label.tenant_id == doc.tenant_id, func.lower(func.trim(Label.name)) == name.strip().lower())
            .first()
        )
        if not label:
            return
    if label not in (doc.labels or []):
        doc.labels.append(label)


def _apply_bank_mapping_labels(db: Session, *, doc: Document, ocr_text: str) -> None:
    """
    Best-effort label assignment based on Bank Settings keyword mappings.
    This is intentionally cheap (no LLM): only keyword matching.
    """
    tenant_id = str(doc.tenant_id or "").strip()
    if not tenant_id:
        return

    # Always attach bank paid category (if already determined elsewhere).
    paid_cat = str(getattr(doc, "bank_paid_category", "") or "").strip()
    if paid_cat:
        _ensure_doc_has_label(db, doc=doc, label_name=paid_cat)

    issuer_subject = "\n".join(
        x
        for x in [
            str(doc.issuer or ""),
            str(doc.subject or ""),
            str(doc.filename or ""),
        ]
        if x
    ).lower()
    ocr_lower = str(ocr_text or "").lower()
    if not (issuer_subject.strip() or ocr_lower.strip()):
        return

    rows = (
        db.query(BankCategoryMapping)
        .filter(BankCategoryMapping.tenant_id == tenant_id)
        .filter(BankCategoryMapping.is_active.is_(True))
        .order_by(BankCategoryMapping.priority.desc(), func.length(BankCategoryMapping.keyword).desc())
        .all()
    )
    # Prefer matches on issuer/subject over incidental OCR matches.
    strong_match: tuple[str, int, int] | None = None  # (category, priority, kwlen)
    weak_match: tuple[str, int, int] | None = None
    for r in rows:
        kw = str(getattr(r, "keyword", "") or "").strip()
        if not kw:
            continue
        kwl = kw.lower()
        cat = str(getattr(r, "category", "") or "").strip()
        if not cat:
            continue
        if kwl and kwl in issuer_subject:
            cand = (cat, int(getattr(r, "priority", 0) or 0), len(kw))
            # Among strong matches prefer longest keyword, then highest priority.
            if (strong_match is None) or (cand[2] > strong_match[2]) or (cand[2] == strong_match[2] and cand[1] > strong_match[1]):
                strong_match = cand
            continue
        if kwl and kwl in ocr_lower:
            cand = (cat, int(getattr(r, "priority", 0) or 0), len(kw))
            if (weak_match is None) or (cand[2] > weak_match[2]) or (cand[2] == weak_match[2] and cand[1] > weak_match[1]):
                weak_match = cand

    # If we found an explicit mapping (MAP), it may overwrite MAN/AI (requested behavior).
    picked = strong_match or weak_match
    if picked:
        matched_category = picked[0]
        doc.budget_category = matched_category
        doc.budget_category_source = "mapping"
        _ensure_doc_has_label(db, doc=doc, label_name=matched_category)
        label = (
            db.query(Label)
            .filter(Label.tenant_id == doc.tenant_id, func.lower(func.trim(Label.name)) == matched_category.strip().lower())
            .first()
        )
        if label:
            doc.labels = [label]
        return

    # If no mapping hit: keep existing manual/mapping label, otherwise infer with LLM (AI pill).
    existing_source = str(getattr(doc, "budget_category_source", "") or "").strip().lower()
    existing_category = str(getattr(doc, "budget_category", "") or "").strip()
    if existing_category and existing_source in {"manual", "mapping", "llm"}:
        return

    runtime = get_runtime_settings(db, tenant_id=tenant_id)
    ai_provider = str(runtime.get("ai_provider") or settings.ai_provider or "openrouter").strip().lower()
    ai_enabled = (
        (ai_provider == "openrouter" and bool(runtime.get("openrouter_api_key")))
        or (ai_provider == "openai" and bool(runtime.get("openai_api_key")))
        or (ai_provider in {"google", "gemini"} and bool(runtime.get("google_api_key")))
    )
    if not ai_enabled:
        return

    prompt_template = str(runtime.get("bank_csv_prompt") or "").strip()
    if not prompt_template:
        return

    known_categories = (
        db.query(BankCategoryMapping.category)
        .filter(BankCategoryMapping.tenant_id == tenant_id, BankCategoryMapping.is_active.is_(True))
        .distinct()
        .all()
    )
    known = sorted({str(x[0]).strip() for x in known_categories if x and x[0] and str(x[0]).strip()})
    if not known:
        return

    # Keep payload compact to reduce token usage.
    ocr_snip = (ocr_text or "").strip()
    if len(ocr_snip) > 1600:
        ocr_snip = ocr_snip[:1600]

    # Ask LLM to pick a category. It MUST choose from known categories.
    prompt = f"""
{prompt_template}

Je krijgt nu 1 document (geen transactie). Kies de BESTE budget-categorie voor dit document op basis van afzender/instantie en context.
Gebruik de bestaande categorieen maximaal en kies EXACT 1 categorie uit deze lijst:
{", ".join(known)}

Document info:
- filename: {str(doc.filename or "")[:180]}
- category: {str(doc.category or "")[:80]}
- issuer: {str(doc.issuer or "")[:160]}
- subject: {str(doc.subject or "")[:240]}
- document_date: {str(doc.document_date or "")[:32]}
- due_date: {str(doc.due_date or "")[:32]}
- amount: {str(doc.total_amount or "")} {str(doc.currency or "")}
- iban: {str(doc.iban or "")[:64]}
- structured_reference: {str(doc.structured_reference or "")[:64]}

OCR snippet:
{ocr_snip}

Geef ENKEL geldige JSON terug met exact dit schema:
{{"category":"string","reason":"korte motivatie"}}

Regels:
- category moet exact overeenkomen met een item uit de lijst.
- Als je het niet zeker weet, kies de best passende categorie uit de lijst (geen nieuwe categorie).
"""
    try:
        out = _call_llm(runtime, prompt, max_retries=3)
        cat = str((out or {}).get("category") or "").strip()
        if cat and cat in known:
            doc.budget_category = cat
            doc.budget_category_source = "llm"
            try:
                group_id = str(getattr(doc, "group_id", "") or "").strip() or _ensure_tenant_default_group_id(db, tenant_id=tenant_id)
                label = (
                    db.query(Label)
                    .filter(Label.tenant_id == doc.tenant_id, Label.group_id == group_id, func.lower(Label.name) == cat.lower())
                    .first()
                )
                if not label:
                    label = Label(tenant_id=doc.tenant_id, name=cat.strip(), group_id=group_id)
                    db.add(label)
                    db.flush()
                doc.labels = [label]
            except Exception:
                _ensure_doc_has_label(db, doc=doc, label_name=cat)
            return
    except Exception:
        # Don't fail document processing for optional labeling.
        pass

    # Hard guarantee: every document gets a budget label (MAP or AI).
    # If LLM fails, fall back to a safe bucket and still mark it as AI (llm)
    # to keep UI consistent with the requested MAN/MAP/AI system.
    fallback = "Overige uitgaven"
    doc.budget_category = fallback
    doc.budget_category_source = "llm"
    try:
        group_id = str(getattr(doc, "group_id", "") or "").strip() or _ensure_tenant_default_group_id(db, tenant_id=tenant_id)
        label = (
            db.query(Label)
            .filter(Label.tenant_id == doc.tenant_id, Label.group_id == group_id, func.lower(Label.name) == fallback.lower())
            .first()
        )
        if not label:
            label = Label(tenant_id=doc.tenant_id, name=fallback.strip(), group_id=group_id)
            db.add(label)
            db.flush()
        doc.labels = [label]
    except Exception:
        _ensure_doc_has_label(db, doc=doc, label_name=fallback)
    return


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
        runtime = get_runtime_settings(db, tenant_id=doc.tenant_id)
        ocr_provider = _get_ocr_provider(ocr_provider_name or "", runtime)
        thumbnail_service = ThumbnailService()

        thumb_name = f"{doc.id}.jpg"
        thumb_fs_path = f"{settings.thumbnails_dir}/{thumb_name}"
        thumbnail_service.create_thumbnail(doc.file_path, doc.content_type, thumb_fs_path)

        ocr_text = ocr_provider.extract_text(doc.file_path, doc.content_type)
        doc.ocr_processed = True
        doc.ocr_text_hash = _ocr_text_hash(ocr_text)

        # Duplicate detection after OCR (100% match): keep OCR, but skip costly AI parsing
        # until the user decides whether to keep this as a separate version or delete.
        skip_ai_due_to_duplicate = False
        if doc.ocr_text_hash and not force:
            existing = (
                db.query(Document)
                .filter(
                    Document.tenant_id == doc.tenant_id,
                    Document.deleted_at.is_(None),
                    Document.id != doc.id,
                    Document.ocr_text_hash == doc.ocr_text_hash,
                )
                .order_by(Document.created_at.desc())
                .first()
            )
            if existing:
                doc.duplicate_of_document_id = str(existing.id)
                doc.duplicate_reason = "ocr_text"
                doc.duplicate_resolved = False
                skip_ai_due_to_duplicate = True

        metadata: dict = {}
        category_profiles: list[dict] = []
        hint_confidence_overrides: dict[str, dict] = {}
        ai_provider = str(runtime.get("ai_provider") or settings.ai_provider or "openrouter").strip().lower()
        ai_enabled = (
            (ai_provider == "openrouter" and bool(runtime.get("openrouter_api_key")))
            or (ai_provider == "openai" and bool(runtime.get("openai_api_key")))
            or (ai_provider in {"google", "gemini"} and bool(runtime.get("google_api_key")))
        )
        if ai_enabled and not skip_ai_due_to_duplicate:
            categories = db.query(CategoryCatalog).filter(CategoryCatalog.tenant_id == doc.tenant_id).all()
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
            hint_confidence_overrides = _apply_extraction_hints(
                db,
                tenant_id=str(doc.tenant_id or ""),
                category=str(metadata.get("category") or doc.category or "").strip() or None,
                metadata=metadata,
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
        # Invariant: zodra een betaaldatum bestaat, is het document betaald.
        if str(getattr(doc, "paid_on", "") or "").strip():
            doc.paid = True
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
                .filter(CategoryCatalog.tenant_id == doc.tenant_id)
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

        # Attach labels based on current OCR text + mapping rules (cheap, no LLM).
        _apply_bank_mapping_labels(db, doc=doc, ocr_text=ocr_text)
        field_confidence = _build_field_confidence(doc, ocr_text)
        if hint_confidence_overrides:
            field_confidence.update(hint_confidence_overrides)
        doc.field_confidence_json = json.dumps(field_confidence, ensure_ascii=False) if field_confidence else None

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
        db.rollback()
        doc.status = "failed"
        doc.error_message = str(exc)
        db.commit()
