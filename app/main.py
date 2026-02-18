import uuid
from datetime import datetime, timedelta
from difflib import get_close_matches
import json
import hashlib
from pathlib import Path
import re
from threading import Lock, Thread, Event

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, ensure_bootstrap_admin, engine, init_db, rebuild_search_index_for_all_documents
from app.models import (
    BankAccount,
    BankBudgetAnalysisRun,
    BankBudgetAnalysisTx,
    BankCategoryMapping,
    BankCsvImport,
    BankTransaction,
    CategoryCatalog,
    Document,
    Group,
    Label,
    User,
)
from app.schemas import (
    AuthOut,
    BankAccountOut,
    BudgetQuickCategoryMapIn,
    BudgetAnalysisOut,
    BankTransactionOut,
    BulkDocumentIdsIn,
    CategoryOut,
    CreateBankAccountIn,
    CreateCategoryIn,
    CreateGroupIn,
    CreateLabelIn,
    CreateUserIn,
    DocumentOut,
    GroupOut,
    ImportTransactionsOut,
    IntegrationSettingsOut,
    BankCsvImportOut,
    LabelOut,
    LoginIn,
    SetDocumentLabelsIn,
    UpdateCategoryIn,
    UpdateDocumentIn,
    UpdateIntegrationSettingsIn,
    UpdateMeIn,
    UpdateUserIn,
    UserOut,
)
from app.services.auth import (
    group_to_out,
    issue_token,
    require_admin_access,
    user_group_ids,
    user_is_admin,
    user_to_out,
    verify_password,
)
from app.services.bank_budget_ai import analyze_budget_transactions_with_llm, match_document_payment_with_llm
from app.services.file_service import allowed_avatar_content_type, allowed_content_type, ensure_dirs
from app.services.integration_settings import get_runtime_settings, settings_to_out, update_settings
from app.services.bank_aggregator import BankAggregatorClient
from app.services.bank_import import parse_imported_transactions
from app.services.mail_ingest import ingest_mail_pdfs
from app.services.pipeline import process_document

app = FastAPI(title=settings.app_name)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BUDGET_ANALYZE_PROGRESS: dict[str, dict] = {}
BUDGET_ANALYZE_LOCK = Lock()
MAIL_INGEST_RUN_LOCK = Lock()
MAIL_INGEST_LAST_RUN_AT: datetime | None = None
MAIL_INGEST_STOP_EVENT = Event()
MAIL_INGEST_THREAD: Thread | None = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_dep(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
):
    from app.services.auth import get_current_user

    return get_current_user(db=db, authorization=authorization)


def _set_budget_progress(user_id: str, *, running: bool, processed: int, total: int, done: bool, error: str | None = None) -> None:
    with BUDGET_ANALYZE_LOCK:
        BUDGET_ANALYZE_PROGRESS[user_id] = {
            "running": bool(running),
            "processed": max(0, int(processed or 0)),
            "total": max(0, int(total or 0)),
            "done": bool(done),
            "error": (str(error).strip() if error else None),
            "updated_at": datetime.utcnow().isoformat(),
        }


def _get_budget_progress(user_id: str) -> dict:
    with BUDGET_ANALYZE_LOCK:
        row = BUDGET_ANALYZE_PROGRESS.get(user_id) or {}
    return {
        "running": bool(row.get("running", False)),
        "processed": max(0, int(row.get("processed", 0) or 0)),
        "total": max(0, int(row.get("total", 0) or 0)),
        "done": bool(row.get("done", False)),
        "error": row.get("error"),
        "updated_at": row.get("updated_at"),
    }


def process_document_job(document_id: str, ocr_provider: str | None = None, force: bool = False) -> None:
    db = SessionLocal()
    try:
        process_document(db, document_id, ocr_provider, force=force)
    finally:
        db.close()


def _run_mail_ingest_once(*, triggered_by_user_id: str | None = None) -> dict:
    global MAIL_INGEST_LAST_RUN_AT
    if not MAIL_INGEST_RUN_LOCK.acquire(blocking=False):
        return {"ok": False, "detail": "Mail ingest loopt al"}
    try:
        db = SessionLocal()
        try:
            runtime = get_runtime_settings(db)
            if not bool(runtime.get("mail_ingest_enabled")):
                return {"ok": False, "detail": "Mail ingest staat uit"}
            uploader_id = triggered_by_user_id
            if not uploader_id:
                admin_user = db.query(User).filter(User.is_bootstrap_admin.is_(True)).first()
                uploader_id = str(admin_user.id) if admin_user else None

            result = ingest_mail_pdfs(
                db=db,
                host=str(runtime.get("mail_imap_host") or ""),
                port=int(runtime.get("mail_imap_port") or 993),
                username=str(runtime.get("mail_imap_username") or ""),
                password=str(runtime.get("mail_imap_password") or ""),
                folder=str(runtime.get("mail_imap_folder") or "INBOX"),
                use_ssl=bool(runtime.get("mail_imap_use_ssl")),
                attachment_types=str(runtime.get("mail_ingest_attachment_types") or "pdf"),
                group_id=str(runtime.get("mail_ingest_group_id") or "").strip() or None,
                uploaded_by_user_id=uploader_id,
            )
            for document_id in result.get("document_ids") or []:
                process_document_job(str(document_id), None)
            MAIL_INGEST_LAST_RUN_AT = datetime.utcnow()
            return {"ok": True, **result}
        finally:
            db.close()
    finally:
        MAIL_INGEST_RUN_LOCK.release()


def _mail_ingest_loop() -> None:
    while not MAIL_INGEST_STOP_EVENT.is_set():
        try:
            db = SessionLocal()
            try:
                runtime = get_runtime_settings(db)
                enabled = bool(runtime.get("mail_ingest_enabled"))
                freq_min = max(0, int(runtime.get("mail_ingest_frequency_minutes") or 0))
            finally:
                db.close()
            if enabled and freq_min > 0:
                now = datetime.utcnow()
                last = MAIL_INGEST_LAST_RUN_AT
                if not last or (now - last) >= timedelta(minutes=freq_min):
                    _run_mail_ingest_once(triggered_by_user_id=None)
        except Exception as ex:
            print(f"[MAIL_INGEST] scheduler error: {ex}")
        MAIL_INGEST_STOP_EVENT.wait(30)


def _default_category_profile(name: str) -> dict:
    base_fields = [
        "category",
        "issuer",
        "subject",
        "document_date",
        "due_date",
        "total_amount",
        "currency",
        "iban",
        "structured_reference",
        "summary",
    ]
    structured_ref_instruction = (
        "Voor structured_reference (gestructureerde mededeling): "
        "herken Belgische vorm ###/####/#####, vaak in +++...+++ of ***...***. "
        "Strip +/* tekens en geef exact ###/####/##### terug. "
        "Als geen valide patroon aanwezig is: null."
    )
    base_prompt = (
        "Extracteer relevante documentvelden voor deze categorie. "
        "Geef strikte JSON terug met minstens deze velden: "
        + ", ".join(base_fields)
        + ". "
        "Voor factuur/rekening: probeer afzender, documentdatum, vervaldatum, totaalbedrag, valuta, IBAN en "
        "gestructureerde mededeling te herkennen. "
        + structured_ref_instruction
        + " Zet onzekere velden op null."
    )
    base_config = [{"key": f, "visible_in_overview": True} for f in base_fields]
    n = (name or "").strip().lower()
    if n == "kasticket":
        fields = [
            "category",
            "issuer",
            "subject",
            "document_date",
            "paid",
            "paid_on",
            "total_amount",
            "currency",
            "items",
            "summary",
        ]
        cfg = [{"key": f, "visible_in_overview": True} for f in fields]
        return {
            "prompt_template": (
                "Dit is een kasticket/bon. Extraheer winkel/instantie (issuer), onderwerp, aankoopdatum (document_date), "
                "totaalbedrag (total_amount), valuta (currency), betaald=true, betaaldatum (paid_on indien zichtbaar, anders "
                "document_date), en items als lijst met artikel + hoeveelheid per lijn. "
                "Voor kastickets zijn due_date, iban en structured_reference niet van toepassing: zet ze altijd op null."
            ),
            "parse_fields": fields,
            "parse_config": cfg,
            "paid_default": True,
        }
    return {
        "prompt_template": base_prompt,
        "parse_fields": base_fields,
        "parse_config": base_config,
        "paid_default": False,
    }


def _category_to_out(row: CategoryCatalog | None, name: str) -> dict:
    default = _default_category_profile(name)
    parse_fields: list[str] = []
    if row and row.parse_fields_json:
        try:
            loaded = json.loads(row.parse_fields_json)
            if isinstance(loaded, list):
                parse_fields = [str(x) for x in loaded]
        except Exception:
            parse_fields = []
    if not parse_fields:
        parse_fields = default["parse_fields"]
    parse_config: list[dict] = []
    if row and row.parse_config_json:
        try:
            loaded = json.loads(row.parse_config_json)
            if isinstance(loaded, list):
                seen = set()
                for item in loaded:
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
    if not parse_config:
        parse_config = [{"key": k, "visible_in_overview": True} for k in parse_fields]
    parse_fields = [c["key"] for c in parse_config]
    prompt = row.prompt_template if row and row.prompt_template else default["prompt_template"]
    paid_default = row.paid_default if row and row.paid_default is not None else default["paid_default"]
    return {
        "id": row.id if row else None,
        "name": name,
        "prompt_template": prompt,
        "parse_fields": parse_fields,
        "parse_config": parse_config,
        "paid_default": bool(paid_default),
    }


def _get_category_profiles(db: Session, group_ids: list[str] | None = None) -> list[dict]:
    names = _get_existing_categories(db, group_ids)
    rows = db.query(CategoryCatalog).all()
    row_map = {r.name.lower(): r for r in rows}
    out = []
    for n in names:
        out.append(_category_to_out(row_map.get(n.lower()), n))
    return out


def _get_existing_categories(db: Session, group_ids: list[str] | None = None) -> list[str]:
    q = db.query(Document.category).filter(Document.category.is_not(None), Document.deleted_at.is_(None))
    if group_ids:
        q = q.filter(Document.group_id.in_(group_ids))
    from_docs = [row[0] for row in q.distinct().all() if row[0]]
    from_catalog = [row[0] for row in db.query(CategoryCatalog.name).all() if row[0]]
    baseline = ["factuur", "rekening", "kasticket"]
    merged = sorted({c.strip() for c in from_docs + from_catalog + baseline if c and c.strip()})
    return merged


def _resolve_category(db: Session, candidate: str | None, group_ids: list[str] | None = None) -> str | None:
    if not candidate:
        return None
    raw = candidate.strip()
    if not raw:
        return None

    existing = _get_existing_categories(db, group_ids)
    if not existing:
        return raw

    lower_map = {x.lower(): x for x in existing}
    if raw.lower() in lower_map:
        return lower_map[raw.lower()]

    close = get_close_matches(raw.lower(), list(lower_map.keys()), n=1, cutoff=0.8)
    if close:
        return lower_map[close[0]]

    return None


def document_to_out(doc: Document) -> dict:
    labels = list(doc.labels or [])
    extra_fields: dict[str, str] = {}
    if doc.extra_fields_json:
        try:
            loaded = json.loads(doc.extra_fields_json)
            if isinstance(loaded, dict):
                extra_fields = {str(k): str(v) for k, v in loaded.items() if k and v is not None}
        except Exception:
            extra_fields = {}
    return {
        "id": doc.id,
        "filename": doc.filename,
        "content_type": doc.content_type,
        "thumbnail_path": doc.thumbnail_path,
        "group_id": doc.group_id,
        "status": doc.status,
        "error_message": doc.error_message,
        "category": doc.category,
        "issuer": doc.issuer,
        "subject": doc.subject,
        "document_date": doc.document_date,
        "due_date": doc.due_date,
        "total_amount": doc.total_amount,
        "currency": doc.currency,
        "iban": doc.iban,
        "structured_reference": doc.structured_reference,
        "paid": bool(doc.paid),
        "paid_on": doc.paid_on,
        "bank_paid_verified": bool(getattr(doc, "bank_paid_verified", False)),
        "remark": doc.remark,
        "line_items": doc.line_items,
        "extra_fields": extra_fields,
        "ocr_text": doc.ocr_text,
        "ocr_processed": bool(doc.ocr_processed),
        "ai_processed": bool(doc.ai_processed),
        "deleted_at": doc.deleted_at,
        "label_ids": [l.id for l in labels],
        "label_names": [l.name for l in labels],
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
    }


def bank_account_to_out(row: BankAccount) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "provider": (row.provider or "vdk").strip().lower(),
        "iban": row.iban,
        "external_account_id": row.external_account_id,
        "is_active": bool(row.is_active),
        "created_at": row.created_at,
    }


def bank_transaction_to_out(row: BankTransaction) -> dict:
    return {
        "id": row.id,
        "bank_account_id": row.bank_account_id,
        "external_transaction_id": row.external_transaction_id,
        "csv_import_id": row.csv_import_id,
        "booking_date": row.booking_date,
        "value_date": row.value_date,
        "amount": row.amount,
        "currency": row.currency,
        "counterparty_name": row.counterparty_name,
        "remittance_information": row.remittance_information,
        "movement_type": _tx_movement_type({"movement_type": None, "raw_json": row.raw_json}),
        "raw_json": row.raw_json,
        "created_at": row.created_at,
    }


def bank_csv_import_to_out(row: BankCsvImport, meta: dict | None = None) -> dict:
    meta = meta or {}
    return {
        "id": row.id,
        "filename": row.filename,
        "imported_count": int(row.imported_count or 0),
        "account_number": (str(meta.get("account_number") or "").strip() or None),
        "account_name": (str(meta.get("account_name") or "").strip() or None),
        "filter_date_from": (str(meta.get("filter_date_from") or "").strip() or None),
        "filter_date_to": (str(meta.get("filter_date_to") or "").strip() or None),
        "parsed_at": row.parsed_at,
        "parsed_source_hash": row.parsed_source_hash,
        "created_at": row.created_at,
    }


def _extract_csv_import_meta(raw_json: str | None) -> dict[str, str]:
    if not raw_json:
        return {}
    try:
        payload = json.loads(str(raw_json))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    metadata = payload.get("csv_metadata")
    if not isinstance(metadata, dict):
        return {}

    by_norm: dict[str, str] = {}
    for k, v in metadata.items():
        nk = _normalize_text(str(k or ""))
        if not nk:
            continue
        by_norm[nk] = str(v or "").strip()

    def pick(*candidates: str) -> str:
        for c in candidates:
            nk = _normalize_text(c)
            if nk and by_norm.get(nk):
                return by_norm[nk]
        return ""

    return {
        "account_number": pick("Rekeningnummer", "Rekening nummer", "Rekening"),
        "account_name": pick("Naam", "Rekeninghouder", "Houder"),
        "filter_date_from": pick("Datum van", "Van", "Filter datum van", "Datumvan"),
        "filter_date_to": pick("Datum tot", "Tot", "Filter datum tot", "Datumtot"),
    }


def _normalize_bank_provider(value: str | None) -> str:
    provider = str(value or "vdk").strip().lower()
    return provider if provider in {"vdk", "kbc", "bnp"} else "vdk"


def _is_xs2a_enabled_for_provider(provider: str) -> bool:
    p = _normalize_bank_provider(provider)
    if p == "vdk":
        return bool(settings.vdk_xs2a)
    if p == "kbc":
        return bool(settings.kbc_xs2a)
    if p == "bnp":
        return bool(settings.bnp_xs2a)
    return False


def _compose_external_account_id(provider: str, raw_external_id: str) -> str:
    return f"{_normalize_bank_provider(provider)}:{raw_external_id.strip()}"


def _split_external_account_id(composite_id: str) -> tuple[str, str]:
    value = str(composite_id or "").strip()
    if ":" in value:
        provider, raw = value.split(":", 1)
        provider = _normalize_bank_provider(provider)
        return provider, raw.strip()
    return "vdk", value


def _get_or_create_csv_import_account(db: Session) -> BankAccount:
    existing = db.query(BankAccount).filter(BankAccount.external_account_id == "csv:import").first()
    if existing:
        return existing
    row = BankAccount(
        name="CSV Import",
        provider="csv",
        iban=None,
        external_account_id="csv:import",
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _tx_raw_payload(tx: dict) -> dict:
    raw = tx.get("raw_json")
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(str(raw))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _tx_movement_type(tx: dict) -> str:
    direct = str(tx.get("movement_type") or "").strip()
    if direct:
        return direct
    raw = _tx_raw_payload(tx)
    csv_fields = raw.get("csv_fields")
    if isinstance(csv_fields, dict):
        for key, value in csv_fields.items():
            nk = _normalize_text(str(key or ""))
            if nk == "soortbeweging":
                return str(value or "").strip()
    return ""


def _mapping_category_for_tx(tx: dict, mappings: list[dict[str, str]], flow: str) -> str | None:
    movement_type = _tx_movement_type(tx)
    desc = f"{tx.get('counterparty_name') or ''} {tx.get('remittance_information') or ''} {movement_type}".lower()
    desc_norm = re.sub(r"[^a-z0-9]+", "", desc)
    candidates = []
    relaxed_candidates = []
    for mapping in mappings:
        keyword = str(mapping.get("keyword") or "").strip().lower()
        keyword_norm = re.sub(r"[^a-z0-9]+", "", keyword)
        mflow = str(mapping.get("flow") or "all").strip().lower()
        cat = str(mapping.get("category") or "").strip()
        if not keyword or not cat:
            continue
        match = keyword in desc or (keyword_norm and keyword_norm in desc_norm)
        if not match:
            continue
        if mflow in {"all", flow}:
            candidates.append((len(keyword_norm or keyword), cat))
        else:
            relaxed_candidates.append((len(keyword_norm or keyword), cat))
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    if relaxed_candidates:
        relaxed_candidates.sort(key=lambda x: x[0], reverse=True)
        return relaxed_candidates[0][1]
    return None


def _fallback_budget_category(tx: dict, mappings: list[dict[str, str]]) -> tuple[str, str, str]:
    amount = float(tx.get("amount") or 0)
    flow = "income" if amount >= 0 else "expense"
    movement_type = _tx_movement_type(tx)
    desc = f"{tx.get('counterparty_name') or ''} {tx.get('remittance_information') or ''} {movement_type}".lower()
    mapped = _mapping_category_for_tx(tx, mappings, flow)
    if mapped:
        return flow, mapped, "mapping"

    # Strong bank-cost signal from CSV movement type.
    movement_norm = _normalize_text(movement_type)
    if flow == "expense" and any(x in movement_norm for x in ["aanrekeningbeheerskost", "beheerskost"]):
        return (flow, "Bankkosten", "rule")

    desc = desc.lower()
    if flow == "income":
        if any(k in desc for k in ["werkgever", "werknemer", "loon", "salary", "payroll", "wedde"]):
            return (flow, "Loon", "rule")
        if any(k in desc for k in ["refund", "terugbetaling"]):
            return (flow, "Terugbetalingen", "rule")
        return (flow, "Overige inkomsten", "rule")
    if any(k in desc for k in ["visa", "mastercard", "maestro"]):
        return (flow, "Kaartuitgaven (VISA/MASTERCARD)", "rule")
    if any(k in desc for k in ["bankkost", "kosten", "fee", "servicekost"]):
        return (flow, "Bankkosten", "rule")
    return (flow, "Overige uitgaven", "rule")


def _build_budget_analysis_payload(
    transactions: list[dict],
    llm_data: dict,
    mappings: list[dict[str, str]],
    preferred_categories: list[str] | None = None,
) -> dict:
    category_rows: list[dict] = llm_data.get("transaction_categories") if isinstance(llm_data, dict) else []
    summary_points = llm_data.get("summary_points") if isinstance(llm_data, dict) else []
    category_map: dict[str, dict] = {}
    if isinstance(category_rows, list):
        for row in category_rows:
            if not isinstance(row, dict):
                continue
            ext_id = str(row.get("external_transaction_id") or "").strip()
            if not ext_id:
                continue
            category_map[ext_id] = {
                "category": str(row.get("category") or "").strip(),
                "flow": str(row.get("flow") or "").strip().lower(),
                "reason": str(row.get("reason") or "").strip() or None,
                "source": str(row.get("source") or "").strip().lower() or None,
            }

    analyzed_transactions: list[dict] = []
    preferred_set = {str(c).strip().lower() for c in (preferred_categories or []) if str(c).strip()}
    category_totals: dict[str, dict[str, float]] = {}
    year_totals: dict[str, dict[str, float]] = {}
    month_totals: dict[str, dict[str, float]] = {}
    for tx in transactions:
        ext_id = str(tx.get("external_transaction_id") or "").strip()
        amount = float(tx.get("amount") or 0)
        booking_date = str(tx.get("booking_date") or "")
        year = booking_date[:4] if len(booking_date) >= 4 else "Onbekend"
        month = booking_date[:7] if len(booking_date) >= 7 else "Onbekend"

        row = category_map.get(ext_id) or {}
        flow = "income" if amount >= 0 else "expense"
        direct_mapping = _mapping_category_for_tx(tx, mappings, flow)
        category = str(row.get("category") or "").strip()
        reason = row.get("reason")
        source = str(row.get("source") or "llm").strip().lower() or "llm"

        # Expliciete mapping is altijd prioriteit.
        if direct_mapping:
            category = direct_mapping
            source = "mapping"
        elif category:
            if source not in {"llm", "mapping", "rule", "manual"}:
                source = "llm"
            # Respecteer bestaande LLM-categorieën bij refresh/analyze, ook als ze niet in preferred_set zitten.
            if preferred_set and category.lower() not in preferred_set and source in {"rule"}:
                _, suggested, suggested_source = _fallback_budget_category(tx, mappings)
                if suggested:
                    category = suggested
                    source = suggested_source
        else:
            _, category, source = _fallback_budget_category(tx, mappings)
        abs_amount = abs(amount)

        analyzed_transactions.append(
            {
                "external_transaction_id": ext_id,
                "booking_date": tx.get("booking_date"),
                "amount": amount,
                "currency": tx.get("currency") or "EUR",
                "counterparty_name": tx.get("counterparty_name"),
                "remittance_information": tx.get("remittance_information"),
                "movement_type": _tx_movement_type(tx),
                "flow": flow,
                "category": category,
                "source": source,
                "reason": reason,
                "csv_import_id": tx.get("csv_import_id"),
                "csv_filename": tx.get("csv_filename"),
                "raw_json": tx.get("raw_json"),
                "created_at": tx.get("created_at"),
                "value_date": tx.get("value_date"),
                "linked_document_id": tx.get("linked_document_id"),
                "linked_document_title": tx.get("linked_document_title"),
            }
        )

        if category not in category_totals:
            category_totals[category] = {"income": 0.0, "expense": 0.0}
        if flow == "income":
            category_totals[category]["income"] += abs_amount
        else:
            category_totals[category]["expense"] += abs_amount

        if year not in year_totals:
            year_totals[year] = {"income": 0.0, "expense": 0.0}
        if month not in month_totals:
            month_totals[month] = {"income": 0.0, "expense": 0.0}
        if flow == "income":
            year_totals[year]["income"] += abs_amount
            month_totals[month]["income"] += abs_amount
        else:
            year_totals[year]["expense"] += abs_amount
            month_totals[month]["expense"] += abs_amount

    sorted_categories = sorted(
        category_totals.items(),
        key=lambda x: (x[1]["income"] + x[1]["expense"]),
        reverse=True,
    )
    sorted_years = sorted(year_totals.items(), key=lambda x: x[0])
    sorted_months = sorted(month_totals.items(), key=lambda x: x[0])
    return {
        "summary_points": summary_points if isinstance(summary_points, list) else [],
        "transactions": analyzed_transactions,
        "category_totals": [
            {"category": name, "income": vals["income"], "expense": vals["expense"]}
            for name, vals in sorted_categories
        ],
        "year_totals": [
            {"period": period, "income": vals["income"], "expense": vals["expense"]}
            for period, vals in sorted_years
        ],
        "month_totals": [
            {"period": period, "income": vals["income"], "expense": vals["expense"]}
            for period, vals in sorted_months
        ],
    }


def _sync_budget_categories_to_mapping_settings(db: Session, analyzed_transactions: list[dict] | None) -> int:
    if not analyzed_transactions:
        return 0
    discovered: dict[str, set[str]] = {}
    for row in analyzed_transactions:
        if not isinstance(row, dict):
            continue
        category = str(row.get("category") or "").strip()
        if not category:
            continue
        flow = str(row.get("flow") or "").strip().lower()
        if flow not in {"income", "expense"}:
            flow = "all"
        discovered.setdefault(category, set()).add(flow)
    if not discovered:
        return 0

    existing_rows = (
        db.query(BankCategoryMapping)
        .filter(BankCategoryMapping.is_active.is_(True))
        .all()
    )
    existing_categories = {str(r.category or "").strip().lower() for r in existing_rows if str(r.category or "").strip()}

    max_priority = db.query(func.max(BankCategoryMapping.priority)).scalar() or 0
    created = 0
    for category, flows in discovered.items():
        key = category.lower()
        if key in existing_categories:
            continue
        inferred_flow = "all" if len(flows) > 1 else next(iter(flows))
        max_priority += 1
        db.add(
            BankCategoryMapping(
                keyword="",
                flow=inferred_flow if inferred_flow in {"income", "expense", "all"} else "all",
                category=category,
                priority=int(max_priority),
                is_active=True,
            )
        )
        created += 1
    if created:
        db.commit()
    return created


def _hash_json(value: object) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _preferred_budget_categories(mappings: list[dict[str, str]] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in mappings or []:
        category = str((item or {}).get("category") or "").strip()
        if not category:
            continue
        key = category.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(category)
    return out


def _normalize_text(value: str | None) -> str:
    raw = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    return re.sub(r"[^a-z0-9]+", "", raw)


def _digits_only(value: str | None) -> str:
    return re.sub(r"[^0-9]+", "", str(value or ""))


def _normalize_iban(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").upper())


def _parse_iso_or_slash_date(value: str | None) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            return None
    return None


def _issuer_token_candidates(value: str | None) -> list[str]:
    raw_tokens = [t.strip() for t in re.split(r"[^a-zA-Z0-9]+", str(value or "")) if t and len(t.strip()) >= 4]
    blacklist = {
        "vzw",
        "bvba",
        "bvb",
        "nv",
        "cv",
        "az",
        "the",
        "shop",
        "store",
        "gent",
        "brugge",
        "belgie",
        "belgium",
    }
    out: list[str] = []
    seen: set[str] = set()
    for token in raw_tokens:
        t = token.lower()
        if t in blacklist or len(t) < 4:
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _tx_match_score(doc: Document, tx: BankTransaction) -> tuple[int, str, str]:
    amount = float(doc.total_amount or 0.0)
    tx_amount = abs(float(tx.amount or 0.0))
    if amount <= 0 or abs(tx_amount - amount) > 0.02:
        return (-1, "none", "Bedrag matcht niet exact")

    if doc.currency and tx.currency and str(doc.currency).upper() != str(tx.currency).upper():
        return (-1, "none", "Valuta matcht niet")

    tx_date = _parse_iso_or_slash_date(tx.booking_date)
    doc_date = _parse_iso_or_slash_date(doc.document_date)
    due_date = _parse_iso_or_slash_date(doc.due_date)
    if tx_date and doc_date and tx_date < (doc_date - timedelta(days=14)):
        return (-1, "none", "Transactiedatum te vroeg t.o.v. documentdatum")
    if tx_date and due_date and tx_date > (due_date + timedelta(days=365)):
        return (-1, "none", "Transactiedatum onrealistisch laat t.o.v. due date")

    rem = str(tx.remittance_information or "")
    cp = str(tx.counterparty_name or "")
    raw = str(tx.raw_json or "")
    joined = f"{cp} {rem} {raw}".strip()
    joined_norm = _normalize_text(joined)
    joined_digits = _digits_only(joined)

    ref_digits = _digits_only(doc.structured_reference)
    ref_norm = _normalize_text(doc.structured_reference)
    iban_norm = _normalize_iban(doc.iban)
    joined_iban_norm = _normalize_iban(joined)
    iban_match = bool(iban_norm) and (iban_norm in joined_iban_norm)

    memo_match = False
    if ref_digits and ref_digits in joined_digits:
        memo_match = True
    elif ref_norm and ref_norm in joined_norm:
        memo_match = True

    # Secondary "mededeling" hints if structured reference is missing/weak.
    if not memo_match:
        subject_tokens = [t for t in re.split(r"[^a-z0-9]+", str(doc.subject or "").lower()) if len(t) >= 6]
        issuer_tokens = [t for t in re.split(r"[^a-z0-9]+", str(doc.issuer or "").lower()) if len(t) >= 4]
        if any(_normalize_text(t) in joined_norm for t in subject_tokens[:4]):
            memo_match = True
        elif any(_normalize_text(t) in joined_norm for t in issuer_tokens[:3]):
            memo_match = True

    # Fallback rule requested: amount + IBAN is enough when tx date is within 3 months
    # of the document date (not upload/create date).
    doc_anchor = doc_date
    within_three_months = False
    if tx_date and doc_anchor:
        try:
            within_three_months = abs((tx_date.date() - doc_anchor.date()).days) <= 93
        except Exception:
            within_three_months = False

    # Third fallback: amount + document_date within 3 months + issuer-name part (>=4 chars)
    # appears in remittance/counterparty/raw.
    name_part_match = False
    issuer_tokens = _issuer_token_candidates(doc.issuer)
    for token in issuer_tokens[:6]:
        if _normalize_text(token) in joined_norm:
            name_part_match = True
            break

    strict_match = iban_match and memo_match
    fallback_match = iban_match and within_three_months
    fallback_name_match = within_three_months and name_part_match
    if not strict_match and not fallback_match and not fallback_name_match:
        return (-1, "none", "Geen voldoende IBAN/mededeling/naam-match")

    score = 0
    confidence = "high"
    reason = "Sterke match op bedrag + IBAN + mededeling"
    if strict_match:
        score += 120
    elif fallback_match:
        score += 80
        confidence = "medium"
        reason = "Fallback op bedrag + IBAN + datum binnen 3 maanden"
    elif fallback_name_match:
        score += 65
        confidence = "low"
        reason = "Fallback op bedrag + datum binnen 3 maanden + naamdeel in mededeling"

    if tx_date and due_date and tx_date <= due_date:
        score += 3
    elif tx_date and doc_date and tx_date >= doc_date:
        score += 2

    if memo_match and ref_digits:
        score += 5

    return (score, confidence, reason)


def _build_bank_check_remark(tx: BankTransaction, *, confidence: str = "high", reason: str = "") -> str:
    tx_date = str(tx.booking_date or "").strip()
    amount = f"{abs(float(tx.amount or 0.0)):.2f}".replace(".", ",")
    sign = "-" if float(tx.amount or 0.0) < 0 else "+"
    currency = str(tx.currency or "EUR").upper()
    cp = str(tx.counterparty_name or "").strip() or "Onbekende tegenpartij"
    rem = str(tx.remittance_information or "").strip() or "-"
    msg = (
        f"[BANK CHECK] transactie {tx_date} | {sign}{amount} {currency} | "
        f"tegenpartij: {cp} | mededeling: {rem}"
    )
    accuracy_label = {
        "high": "Nauwkeurigheid: hoog (95-100%)",
        "medium": "Nauwkeurigheid: medium (80-94%)",
        "low": "Nauwkeurigheid: indicatief (65-79%)",
    }.get(confidence, "Nauwkeurigheid: onbekend")
    note = f" [{accuracy_label}"
    if reason:
        note += f" | {reason}"
    note += "]"
    msg += note
    if confidence == "low":
        msg += " [LET OP: geen 100% match, maar goede inschatting.]"
    return msg


def _tx_candidate_for_llm(doc: Document, tx: BankTransaction) -> bool:
    amount = float(doc.total_amount or 0.0)
    tx_amount = abs(float(tx.amount or 0.0))
    if amount <= 0 or abs(tx_amount - amount) > 0.02:
        return False
    if doc.currency and tx.currency and str(doc.currency).upper() != str(tx.currency).upper():
        return False
    tx_date = _parse_iso_or_slash_date(tx.booking_date)
    doc_date = _parse_iso_or_slash_date(doc.document_date)
    if not tx_date or not doc_date:
        return False
    return abs((tx_date.date() - doc_date.date()).days) <= 93


def _amount_to_cents(value: float | int | None) -> int:
    try:
        return int(round(abs(float(value or 0.0)) * 100))
    except Exception:
        return 0


def _enrich_budget_transactions_with_doc_links(db: Session, transactions: list[dict]) -> list[dict]:
    if not transactions:
        return []

    csv_import_ids = {
        str(tx.get("csv_import_id") or "").strip()
        for tx in transactions
        if str(tx.get("csv_import_id") or "").strip()
    }
    csv_name_by_id: dict[str, str] = {}
    if csv_import_ids:
        rows = db.query(BankCsvImport.id, BankCsvImport.filename).filter(BankCsvImport.id.in_(csv_import_ids)).all()
        csv_name_by_id = {str(r.id): str(r.filename or "") for r in rows}

    docs = (
        db.query(Document)
        .filter(
            Document.deleted_at.is_(None),
            Document.paid.is_(True),
            Document.total_amount.is_not(None),
            Document.paid_on.is_not(None),
        )
        .all()
    )
    by_key: dict[tuple[str, int], list[Document]] = {}
    for doc in docs:
        paid_on = str(doc.paid_on or "").strip()
        if len(paid_on) < 10:
            continue
        key = (paid_on[:10], _amount_to_cents(doc.total_amount))
        by_key.setdefault(key, []).append(doc)

    out: list[dict] = []
    for tx in transactions:
        row = dict(tx or {})
        csv_import_id = str(row.get("csv_import_id") or "").strip()
        if csv_import_id and csv_import_id in csv_name_by_id:
            row["csv_filename"] = csv_name_by_id[csv_import_id]
        booking_date = str(row.get("booking_date") or "").strip()
        key = (booking_date[:10], _amount_to_cents(row.get("amount")))
        candidates = by_key.get(key) or []
        picked: Document | None = None
        if len(candidates) == 1:
            picked = candidates[0]
        elif len(candidates) > 1:
            haystack = _normalize_text(
                f"{str(row.get('counterparty_name') or '')} {str(row.get('remittance_information') or '')}"
            )
            best_score = -1
            for doc in candidates:
                score = 0
                for tok in _issuer_token_candidates(doc.issuer):
                    t = _normalize_text(tok)
                    if t and t in haystack:
                        score += 2
                subject_tokens = [t for t in re.split(r"[^a-z0-9]+", str(doc.subject or "").lower()) if len(t) >= 5]
                for tok in subject_tokens[:3]:
                    t = _normalize_text(tok)
                    if t and t in haystack:
                        score += 1
                if score > best_score:
                    best_score = score
                    picked = doc
        if picked:
            row["linked_document_id"] = picked.id
            row["linked_document_title"] = str(picked.subject or picked.filename or "").strip() or "Document"
        out.append(row)
    return out


def _attach_budget_document_context(db: Session, transactions: list[dict]) -> list[dict]:
    if not transactions:
        return []
    out = [dict(t or {}) for t in transactions]
    doc_ids = {str(t.get("linked_document_id") or "").strip() for t in out if str(t.get("linked_document_id") or "").strip()}
    if not doc_ids:
        return out
    docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
    by_id = {str(d.id): d for d in docs}
    for row in out:
        did = str(row.get("linked_document_id") or "").strip()
        if not did or did not in by_id:
            continue
        doc = by_id[did]
        parts = [
            f"categorie={str(doc.category or '').strip()}",
            f"afzender={str(doc.issuer or '').strip()}",
            f"onderwerp={str(doc.subject or '').strip()}",
            f"bedrag={str(doc.total_amount or '')} {str(doc.currency or '').strip()}",
            f"iban={str(doc.iban or '').strip()}",
            f"mededeling={str(doc.structured_reference or '').strip()}",
        ]
        row["linked_document_context"] = " | ".join([p for p in parts if not p.endswith("=")]).strip()
    return out


def ensure_doc_access(doc: Document | None, current_user: User, allow_deleted: bool = False) -> Document:
    if not doc:
        raise HTTPException(status_code=404, detail="Document niet gevonden")
    if not allow_deleted and doc.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Document niet gevonden")
    if not _current_user_can_see_all_groups(current_user) and doc.group_id not in user_group_ids(current_user):
        raise HTTPException(status_code=403, detail="Geen toegang")
    return doc


def _current_user_can_see_all_groups(user: User) -> bool:
    return user_is_admin(user)


def _purge_expired_deleted_docs(db: Session) -> None:
    cutoff = datetime.utcnow() - timedelta(days=7)
    expired_docs = db.query(Document).filter(Document.deleted_at.is_not(None), Document.deleted_at < cutoff).all()
    if not expired_docs:
        return

    with engine.begin() as conn:
        for d in expired_docs:
            conn.execute(text("DELETE FROM document_labels WHERE document_id = :id"), {"id": d.id})
            conn.execute(text("DELETE FROM document_search WHERE document_id = :id"), {"id": d.id})

    for d in expired_docs:
        try:
            if d.file_path:
                Path(d.file_path).unlink(missing_ok=True)
        except Exception:
            pass
        try:
            if d.thumbnail_path:
                thumb = d.thumbnail_path.replace("/thumbnails/", "").strip()
                if thumb:
                    Path(settings.thumbnails_dir, thumb).unlink(missing_ok=True)
        except Exception:
            pass
        db.delete(d)
    db.commit()


def _build_searchable_text(doc: Document) -> str:
    label_text = " ".join([label.name for label in (doc.labels or [])])
    extra_values = ""
    if doc.extra_fields_json:
        try:
            loaded = json.loads(doc.extra_fields_json)
            if isinstance(loaded, dict):
                extra_values = " ".join(
                    f"{str(k)} {str(v)}" for k, v in loaded.items() if k and v is not None and str(v).strip()
                )
        except Exception:
            extra_values = ""
    return "\n".join(
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
            "paid" if doc.paid else "unpaid",
            doc.paid_on,
            doc.remark,
            doc.line_items,
            extra_values,
            label_text,
            doc.ocr_text,
        ]
        if x
    )


@app.on_event("startup")
def startup() -> None:
    global MAIL_INGEST_THREAD
    ensure_dirs()
    init_db()
    ensure_bootstrap_admin()
    rebuild_search_index_for_all_documents()
    if MAIL_INGEST_THREAD is None or not MAIL_INGEST_THREAD.is_alive():
        MAIL_INGEST_STOP_EVENT.clear()
        MAIL_INGEST_THREAD = Thread(target=_mail_ingest_loop, daemon=True, name="mail-ingest-loop")
        MAIL_INGEST_THREAD.start()


@app.on_event("shutdown")
def shutdown() -> None:
    MAIL_INGEST_STOP_EVENT.set()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=AuthOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Ongeldige login")
    token = issue_token(db, user)
    return {"token": token, "user": user_to_out(user)}


@app.get("/api/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user_dep)):
    return user_to_out(current_user)


@app.put("/api/auth/me", response_model=UserOut)
def update_me(
    payload: UpdateMeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    from app.services.auth import hash_password

    email = (payload.email or "").strip()
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Naam is verplicht")
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Email formaat is ongeldig")

    conflict = db.query(User).filter(User.email == email, User.id != current_user.id).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Email bestaat al")

    current_user.name = name
    current_user.email = email
    if payload.password is not None and payload.password.strip():
        current_user.password_hash = hash_password(payload.password.strip())

    db.commit()
    db.refresh(current_user)
    return user_to_out(current_user)


@app.post("/api/auth/me/avatar", response_model=UserOut)
async def upload_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    if not file.content_type or not allowed_avatar_content_type(file.content_type):
        raise HTTPException(status_code=400, detail="Avatar moet png, jpg of webp zijn")

    ext = Path(file.filename or "avatar").suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        ext = ".jpg"
    avatar_name = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
    avatar_fs_path = Path(settings.avatars_dir) / avatar_name
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Avatar is te groot (max 5MB)")
    avatar_fs_path.write_bytes(content)

    old_avatar = (current_user.avatar_path or "").strip()
    current_user.avatar_path = f"/avatars/{avatar_name}"
    db.commit()
    db.refresh(current_user)

    if old_avatar.startswith("/avatars/"):
        old_name = old_avatar.split("/avatars/", 1)[1].strip()
        if old_name:
            try:
                Path(settings.avatars_dir, old_name).unlink(missing_ok=True)
            except Exception:
                pass

    return user_to_out(current_user)


@app.get("/api/meta/providers")
def providers(db: Session = Depends(get_db)) -> dict:
    runtime = get_runtime_settings(db)
    default_ai = str(runtime.get("ai_provider") or settings.ai_provider or "openrouter").strip().lower()
    if default_ai == "gemini":
        default_ai = "google"
    default_ocr = str(runtime.get("default_ocr_provider") or settings.ocr_provider or "textract").strip().lower()
    if default_ocr == "openrouter":
        default_ocr = "llm_vision"
    return {
        "ocr": ["textract", "llm_vision"],
        "ai": ["openrouter", "openai", "google"],
        "default_ocr": default_ocr,
        "default_ai": default_ai,
    }


@app.get("/api/groups", response_model=list[GroupOut])
def my_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    if _current_user_can_see_all_groups(current_user):
        all_groups = db.query(Group).order_by(Group.name.asc()).all()
        return [group_to_out(g) for g in all_groups]
    return [group_to_out(g) for g in current_user.groups]


@app.get("/api/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    if _current_user_can_see_all_groups(current_user):
        return _get_category_profiles(db, None)
    return _get_category_profiles(db, user_group_ids(current_user))


@app.post("/api/categories", response_model=CategoryOut)
def create_category(
    payload: CreateCategoryIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    _ = current_user
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Categorie is verplicht")

    existing = db.query(CategoryCatalog).filter(func.lower(CategoryCatalog.name) == name.lower()).first()
    if existing:
        return _category_to_out(existing, existing.name)

    default = _default_category_profile(name)
    row = CategoryCatalog(
        name=name,
        prompt_template=default["prompt_template"],
        parse_fields_json=json.dumps(default["parse_fields"]),
        parse_config_json=json.dumps(default["parse_config"]),
        paid_default=default["paid_default"],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _category_to_out(row, row.name)


@app.put("/api/categories/{category_name}", response_model=CategoryOut)
def update_category(
    category_name: str,
    payload: UpdateCategoryIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    _ = current_user
    old_name = (category_name or "").strip()
    new_name = (payload.name or "").strip()
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail="Categorie naam is verplicht")

    row = db.query(CategoryCatalog).filter(func.lower(CategoryCatalog.name) == old_name.lower()).first()
    if not row:
        row = CategoryCatalog(name=old_name)
        db.add(row)
        db.flush()

    conflict = db.query(CategoryCatalog).filter(
        func.lower(CategoryCatalog.name) == new_name.lower(),
        CategoryCatalog.id != row.id,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Categorie naam bestaat al")

    old_doc_name = row.name
    row.name = new_name
    row.prompt_template = (payload.prompt_template or "").strip() or None
    fields_set = getattr(payload, "model_fields_set", getattr(payload, "__fields_set__", set()))
    normalized_config: list[dict] = []
    if "parse_config" in fields_set:
        seen = set()
        for item in (payload.parse_config or []):
            key = str(item.key or "").strip().lower().replace(" ", "_")
            if not key or key in seen:
                continue
            seen.add(key)
            normalized_config.append(
                {
                    "key": key,
                    "visible_in_overview": bool(item.visible_in_overview),
                }
            )
    else:
        seen = set()
        for x in (payload.parse_fields or []):
            key = str(x or "").strip().lower().replace(" ", "_")
            if not key or key in seen:
                continue
            seen.add(key)
            normalized_config.append({"key": key, "visible_in_overview": True})

    normalized_fields = [x["key"] for x in normalized_config]
    row.parse_fields_json = json.dumps(normalized_fields)
    row.parse_config_json = json.dumps(normalized_config)
    row.paid_default = payload.paid_default if payload.paid_default is not None else False

    docs = db.query(Document).filter(func.lower(Document.category) == old_doc_name.lower()).all()
    for d in docs:
        d.category = new_name

    db.commit()
    db.refresh(row)
    return _category_to_out(row, row.name)


@app.delete("/api/categories/{category_name}")
def delete_category(
    category_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    _ = current_user
    name = (category_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Categorie is verplicht")

    linked_docs = db.query(Document.id).filter(
        func.lower(Document.category) == name.lower(),
        Document.deleted_at.is_(None),
    ).first()
    if linked_docs:
        raise HTTPException(
            status_code=409,
            detail="Categorie kan niet verwijderd worden: er hangen nog documenten aan.",
        )

    row = db.query(CategoryCatalog).filter(func.lower(CategoryCatalog.name) == name.lower()).first()
    if not row:
        raise HTTPException(status_code=404, detail="Categorie niet gevonden in catalogus")

    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/labels", response_model=list[LabelOut])
def list_labels(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    if _current_user_can_see_all_groups(current_user):
        labels = db.query(Label).order_by(Label.name.asc()).all()
        return [{"id": l.id, "name": l.name, "group_id": l.group_id} for l in labels]
    group_ids = user_group_ids(current_user)
    if not group_ids:
        return []
    labels = db.query(Label).filter(Label.group_id.in_(group_ids)).order_by(Label.name.asc()).all()
    return [{"id": l.id, "name": l.name, "group_id": l.group_id} for l in labels]


@app.post("/api/labels", response_model=LabelOut)
def create_label(
    payload: CreateLabelIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    if not _current_user_can_see_all_groups(current_user) and payload.group_id not in user_group_ids(current_user):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze groep")

    existing = db.query(Label).filter(
        Label.group_id == payload.group_id,
        func.lower(Label.name) == payload.name.lower(),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Label bestaat al in deze groep")

    label = Label(name=payload.name.strip(), group_id=payload.group_id)
    db.add(label)
    db.commit()
    db.refresh(label)
    return {"id": label.id, "name": label.name, "group_id": label.group_id}


@app.put("/api/documents/{document_id}/labels", response_model=DocumentOut)
def set_document_labels(
    document_id: str,
    payload: SetDocumentLabelsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    doc = ensure_doc_access(db.get(Document, document_id), current_user)

    labels = []
    if payload.label_ids:
        labels = db.query(Label).filter(Label.id.in_(payload.label_ids), Label.group_id == doc.group_id).all()

    doc.labels = labels
    db.commit()
    db.refresh(doc)

    searchable = doc.searchable_text or ""
    searchable = searchable + "\n" + " ".join([l.name for l in labels])
    from app.db import upsert_search_index

    upsert_search_index(doc.id, searchable)

    return document_to_out(doc)


@app.get("/api/admin/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    require_admin_access(current_user)
    users = db.query(User).order_by(User.created_at.asc()).all()
    return [user_to_out(u) for u in users]


@app.post("/api/admin/users", response_model=UserOut)
def create_user(
    payload: CreateUserIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    from app.services.auth import hash_password

    require_admin_access(current_user)

    if not EMAIL_RE.match(payload.email or ""):
        raise HTTPException(status_code=400, detail="Email formaat is ongeldig")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email bestaat al")

    user = User(email=payload.email, name=payload.name, password_hash=hash_password(payload.password))
    if payload.group_ids:
        groups = db.query(Group).filter(Group.id.in_(payload.group_ids)).all()
        user.groups = groups

    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_out(user)


@app.put("/api/admin/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UpdateUserIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    from app.services.auth import hash_password

    require_admin_access(current_user)

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    if not EMAIL_RE.match(payload.email or ""):
        raise HTTPException(status_code=400, detail="Email formaat is ongeldig")

    email = (payload.email or "").strip()
    name = (payload.name or "").strip()
    if not email or not name:
        raise HTTPException(status_code=400, detail="Naam en email zijn verplicht")

    conflict = db.query(User).filter(User.email == email, User.id != user.id).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Email bestaat al")

    user.email = email
    user.name = name
    if payload.password is not None and payload.password.strip():
        user.password_hash = hash_password(payload.password.strip())

    if payload.group_id:
        group = db.get(Group, payload.group_id)
        if not group:
            raise HTTPException(status_code=400, detail="Groep niet gevonden")
        user.groups = [group]
    else:
        user.groups = []

    db.commit()
    db.refresh(user)
    return user_to_out(user)


@app.delete("/api/admin/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Je kan je eigen account niet verwijderen")
    if user.is_bootstrap_admin:
        raise HTTPException(status_code=400, detail="Bootstrap admin kan niet verwijderd worden")

    user.groups = []
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM session_tokens WHERE user_id = :uid"), {"uid": user.id})
        conn.execute(text("DELETE FROM user_groups WHERE user_id = :uid"), {"uid": user.id})

    db.delete(user)
    db.commit()
    return {"ok": True}


@app.get("/api/admin/groups", response_model=list[GroupOut])
def list_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    require_admin_access(current_user)
    groups = db.query(Group).order_by(Group.name.asc()).all()
    return [group_to_out(g) for g in groups]


@app.post("/api/admin/groups", response_model=GroupOut)
def create_group(
    payload: CreateGroupIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)

    existing = db.query(Group).filter(Group.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Groepsnaam bestaat al")

    group = Group(name=payload.name)
    if payload.user_ids:
        users = db.query(User).filter(User.id.in_(payload.user_ids)).all()
        group.users = users

    db.add(group)
    db.commit()
    db.refresh(group)
    return group_to_out(group)


@app.delete("/api/admin/groups/{group_id}")
def delete_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)

    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Groep niet gevonden")
    if (group.name or "").strip().lower() == "administrators":
        raise HTTPException(status_code=400, detail="Administrators groep kan niet verwijderd worden")
    if group.users:
        raise HTTPException(status_code=400, detail="Groep kan niet verwijderd worden: er zijn nog gebruikers gekoppeld")

    db.delete(group)
    db.commit()
    return {"ok": True}


@app.get("/api/admin/integrations", response_model=IntegrationSettingsOut)
def get_integrations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    require_admin_access(current_user)
    return settings_to_out(db)


@app.put("/api/admin/integrations", response_model=IntegrationSettingsOut)
def update_integrations(
    payload: UpdateIntegrationSettingsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    return update_settings(
        db,
        aws_region=payload.aws_region,
        aws_access_key_id=payload.aws_access_key_id,
        aws_secret_access_key=payload.aws_secret_access_key,
        ai_provider=payload.ai_provider,
        openrouter_api_key=payload.openrouter_api_key,
        openrouter_model=payload.openrouter_model,
        openrouter_ocr_model=payload.openrouter_ocr_model,
        openai_api_key=payload.openai_api_key,
        openai_model=payload.openai_model,
        openai_ocr_model=payload.openai_ocr_model,
        google_api_key=payload.google_api_key,
        google_model=payload.google_model,
        google_ocr_model=payload.google_ocr_model,
        vdk_base_url=payload.vdk_base_url,
        vdk_client_id=payload.vdk_client_id,
        vdk_api_key=payload.vdk_api_key,
        vdk_password=payload.vdk_password,
        kbc_base_url=payload.kbc_base_url,
        kbc_client_id=payload.kbc_client_id,
        kbc_api_key=payload.kbc_api_key,
        kbc_password=payload.kbc_password,
        bnp_base_url=payload.bnp_base_url,
        bnp_client_id=payload.bnp_client_id,
        bnp_api_key=payload.bnp_api_key,
        bnp_password=payload.bnp_password,
        bank_provider=payload.bank_provider,
        mail_ingest_enabled=payload.mail_ingest_enabled,
        mail_imap_host=payload.mail_imap_host,
        mail_imap_port=payload.mail_imap_port,
        mail_imap_username=payload.mail_imap_username,
        mail_imap_password=payload.mail_imap_password,
        mail_imap_folder=payload.mail_imap_folder,
        mail_imap_use_ssl=payload.mail_imap_use_ssl,
        mail_ingest_frequency_minutes=payload.mail_ingest_frequency_minutes,
        mail_ingest_group_id=payload.mail_ingest_group_id,
        mail_ingest_attachment_types=payload.mail_ingest_attachment_types,
        bank_csv_prompt=payload.bank_csv_prompt,
        bank_csv_mappings=payload.bank_csv_mappings,
        default_ocr_provider=payload.default_ocr_provider,
    )


@app.post("/api/admin/mail-ingest/run")
def run_mail_ingest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    runtime = get_runtime_settings(db)
    if not bool(runtime.get("mail_ingest_enabled")):
        raise HTTPException(status_code=400, detail="Mail ingest staat uit in integraties")
    result = _run_mail_ingest_once(triggered_by_user_id=current_user.id)
    if not bool(result.get("ok")):
        raise HTTPException(status_code=409, detail=str(result.get("detail") or "Mail ingest niet uitgevoerd"))
    return {
        "ok": True,
        "imported": int(result.get("imported") or 0),
        "skipped_seen": int(result.get("skipped_seen") or 0),
        "scanned_messages": int(result.get("scanned_messages") or 0),
    }


@app.get("/api/bank/accounts", response_model=list[BankAccountOut])
def list_bank_accounts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    require_admin_access(current_user)
    rows = db.query(BankAccount).order_by(BankAccount.created_at.desc()).all()
    return [bank_account_to_out(r) for r in rows]


@app.post("/api/bank/accounts", response_model=BankAccountOut)
def create_bank_account(
    payload: CreateBankAccountIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    name = (payload.name or "").strip()
    provider = _normalize_bank_provider(payload.provider)
    raw_external = (payload.external_account_id or "").strip()
    if not name or not raw_external:
        raise HTTPException(status_code=400, detail="Naam en external account id zijn verplicht")
    external = _compose_external_account_id(provider, raw_external)

    existing = db.query(BankAccount).filter(BankAccount.external_account_id == external).first()
    if existing:
        return bank_account_to_out(existing)

    row = BankAccount(
        name=name,
        provider=provider,
        iban=(payload.iban or "").strip() or None,
        external_account_id=external,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return bank_account_to_out(row)


@app.delete("/api/bank/accounts/{account_id}")
def delete_bank_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    row = db.get(BankAccount, account_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rekening niet gevonden")
    db.query(BankTransaction).filter(BankTransaction.bank_account_id == row.id).delete()
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.post("/api/bank/sync-accounts", response_model=list[BankAccountOut])
def sync_bank_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    runtime = get_runtime_settings(db)
    provider = _normalize_bank_provider(runtime.get("bank_provider"))
    if not _is_xs2a_enabled_for_provider(provider):
        raise HTTPException(status_code=400, detail=f"XS2A voor {provider.upper()} staat uit")
    client = BankAggregatorClient(
        provider=provider,
        base_url=str(runtime.get("bank_base_url") or ""),
        client_id=str(runtime.get("bank_client_id") or ""),
        api_key=str(runtime.get("bank_api_key") or ""),
        password=str(runtime.get("bank_password") or ""),
    )
    remote_accounts = client.fetch_accounts()
    for r in remote_accounts:
        external = str(r.get("external_account_id") or "").strip()
        if not external:
            continue
        row = db.query(BankAccount).filter(BankAccount.external_account_id == external).first()
        if row:
            row.name = str(r.get("name") or row.name).strip() or row.name
            row.provider = _normalize_bank_provider(r.get("provider") or row.provider)
            row.iban = str(r.get("iban") or row.iban or "").strip() or row.iban
            row.is_active = True
        else:
            db.add(
                BankAccount(
                    name=str(r.get("name") or external).strip() or external,
                    provider=_normalize_bank_provider(r.get("provider")),
                    iban=str(r.get("iban") or "").strip() or None,
                    external_account_id=external,
                    is_active=True,
                )
            )
    db.commit()
    rows = db.query(BankAccount).order_by(BankAccount.created_at.desc()).all()
    return [bank_account_to_out(r) for r in rows]


@app.get("/api/bank/accounts/{account_id}/transactions", response_model=list[BankTransactionOut])
def list_bank_transactions(
    account_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    account = db.get(BankAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Rekening niet gevonden")
    rows = (
        db.query(BankTransaction)
        .filter(BankTransaction.bank_account_id == account.id)
        .order_by(BankTransaction.booking_date.desc(), BankTransaction.created_at.desc())
        .limit(limit)
        .all()
    )
    return [bank_transaction_to_out(r) for r in rows]


@app.post("/api/bank/accounts/{account_id}/sync-transactions", response_model=list[BankTransactionOut])
def sync_bank_transactions(
    account_id: str,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    account = db.get(BankAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Rekening niet gevonden")

    runtime = get_runtime_settings(db)
    provider = _normalize_bank_provider(account.provider)
    if not _is_xs2a_enabled_for_provider(provider):
        raise HTTPException(status_code=400, detail=f"XS2A voor {provider.upper()} staat uit")
    client = BankAggregatorClient(
        provider=provider,
        base_url=str(runtime.get(f"{provider}_base_url") or runtime.get("bank_base_url") or ""),
        client_id=str(runtime.get(f"{provider}_client_id") or runtime.get("bank_client_id") or ""),
        api_key=str(runtime.get(f"{provider}_api_key") or runtime.get("bank_api_key") or ""),
        password=str(runtime.get(f"{provider}_password") or runtime.get("bank_password") or ""),
    )
    _, raw_external_account_id = _split_external_account_id(account.external_account_id)

    txs = client.fetch_transactions(
        raw_external_account_id,
        date_from=(date_from or "").strip() or None,
        date_to=(date_to or "").strip() or None,
    )
    for t in txs:
        ext_id = str(t.get("external_transaction_id") or "").strip()
        if not ext_id:
            continue
        row = (
            db.query(BankTransaction)
            .filter(
                BankTransaction.bank_account_id == account.id,
                BankTransaction.external_transaction_id == ext_id,
            )
            .first()
        )
        if row:
            row.booking_date = t.get("booking_date")
            row.value_date = t.get("value_date")
            row.amount = t.get("amount")
            row.currency = t.get("currency")
            row.counterparty_name = t.get("counterparty_name")
            row.remittance_information = t.get("remittance_information")
            row.raw_json = t.get("raw_json")
        else:
            db.add(
                BankTransaction(
                    bank_account_id=account.id,
                    external_transaction_id=ext_id,
                    booking_date=t.get("booking_date"),
                    value_date=t.get("value_date"),
                    amount=t.get("amount"),
                    currency=t.get("currency"),
                    counterparty_name=t.get("counterparty_name"),
                    remittance_information=t.get("remittance_information"),
                    raw_json=t.get("raw_json"),
                )
            )
    db.commit()
    rows = (
        db.query(BankTransaction)
        .filter(BankTransaction.bank_account_id == account.id)
        .order_by(BankTransaction.booking_date.desc(), BankTransaction.created_at.desc())
        .limit(500)
        .all()
    )
    return [bank_transaction_to_out(r) for r in rows]


@app.post("/api/bank/accounts/{account_id}/import-transactions", response_model=ImportTransactionsOut)
async def import_bank_transactions(
    account_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    account = db.get(BankAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Rekening niet gevonden")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Bestand is leeg")

    _, txs = parse_imported_transactions(file.filename or "", content)
    imported = 0
    for t in txs:
        ext_id = str(t.get("external_transaction_id") or "").strip()
        if not ext_id:
            continue
        row = (
            db.query(BankTransaction)
            .filter(
                BankTransaction.bank_account_id == account.id,
                BankTransaction.external_transaction_id == ext_id,
            )
            .first()
        )
        if row:
            row.booking_date = t.get("booking_date")
            row.value_date = t.get("value_date")
            row.amount = t.get("amount")
            row.currency = t.get("currency")
            row.counterparty_name = t.get("counterparty_name")
            row.remittance_information = t.get("remittance_information")
            row.raw_json = t.get("raw_json")
            imported += 1
        else:
            db.add(
                BankTransaction(
                    bank_account_id=account.id,
                    external_transaction_id=ext_id,
                    booking_date=t.get("booking_date"),
                    value_date=t.get("value_date"),
                    amount=t.get("amount"),
                    currency=t.get("currency"),
                    counterparty_name=t.get("counterparty_name"),
                    remittance_information=t.get("remittance_information"),
                    raw_json=t.get("raw_json"),
                )
            )
            imported += 1

    db.commit()
    return {"imported": imported}


@app.post("/api/bank/import-csv", response_model=ImportTransactionsOut)
async def import_bank_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    filename = (file.filename or "").strip().lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Enkel .csv bestanden zijn toegestaan")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Bestand is leeg")
    account = _get_or_create_csv_import_account(db)
    _, txs = parse_imported_transactions(file.filename or "", content)
    import_row = BankCsvImport(
        filename=file.filename or "import.csv",
        imported_count=0,
    )
    db.add(import_row)
    db.commit()
    db.refresh(import_row)
    imported = 0
    for t in txs:
        ext_id = str(t.get("external_transaction_id") or "").strip()
        if not ext_id:
            continue
        row = (
            db.query(BankTransaction)
            .filter(
                BankTransaction.bank_account_id == account.id,
                BankTransaction.external_transaction_id == ext_id,
            )
            .first()
        )
        if row:
            row.booking_date = t.get("booking_date")
            row.value_date = t.get("value_date")
            row.amount = t.get("amount")
            row.currency = t.get("currency")
            row.counterparty_name = t.get("counterparty_name")
            row.remittance_information = t.get("remittance_information")
            row.raw_json = t.get("raw_json")
            row.csv_import_id = import_row.id
            imported += 1
        else:
            db.add(
                BankTransaction(
                    bank_account_id=account.id,
                    csv_import_id=import_row.id,
                    external_transaction_id=ext_id,
                    booking_date=t.get("booking_date"),
                    value_date=t.get("value_date"),
                    amount=t.get("amount"),
                    currency=t.get("currency"),
                    counterparty_name=t.get("counterparty_name"),
                    remittance_information=t.get("remittance_information"),
                    raw_json=t.get("raw_json"),
                )
            )
            imported += 1
    import_row.imported_count = imported
    if imported > 0:
        import_row.parsed_at = datetime.utcnow()
        import_row.parsed_source_hash = "csv-import"
    db.commit()
    return {"imported": imported}


@app.get("/api/bank/import-csv/transactions", response_model=list[BankTransactionOut])
def list_bank_csv_transactions(
    limit: int = Query(default=200, ge=1, le=20000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    account = _get_or_create_csv_import_account(db)
    rows = (
        db.query(BankTransaction)
        .filter(BankTransaction.bank_account_id == account.id)
        .order_by(BankTransaction.booking_date.desc(), BankTransaction.created_at.desc())
        .limit(limit)
        .all()
    )
    data = [bank_transaction_to_out(r) for r in rows]
    return _enrich_budget_transactions_with_doc_links(db, data)


@app.post("/api/bank/budget/analyze", response_model=BudgetAnalysisOut)
def analyze_bank_budget(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    progress_user_id = str(current_user.id)
    account = _get_or_create_csv_import_account(db)
    rows = (
        db.query(BankTransaction)
        .filter(BankTransaction.bank_account_id == account.id)
        .order_by(BankTransaction.booking_date.asc(), BankTransaction.created_at.asc())
        .all()
    )
    tx_payload = [bank_transaction_to_out(r) for r in rows]
    tx_payload = _enrich_budget_transactions_with_doc_links(db, tx_payload)
    tx_payload = _attach_budget_document_context(db, tx_payload)
    tx_payload = _enrich_budget_transactions_with_doc_links(db, tx_payload)
    tx_payload = _attach_budget_document_context(db, tx_payload)
    _set_budget_progress(
        progress_user_id,
        running=True,
        processed=0,
        total=len(tx_payload),
        done=False,
    )
    csv_import_ids = sorted({str(r.csv_import_id) for r in rows if r.csv_import_id})

    out_settings = settings_to_out(db)
    runtime = get_runtime_settings(db)
    mappings = out_settings.get("bank_csv_mappings") if isinstance(out_settings, dict) else []
    preferred_categories = _preferred_budget_categories(mappings if isinstance(mappings, list) else [])
    prompt = str(out_settings.get("bank_csv_prompt") or "").strip() if isinstance(out_settings, dict) else ""
    provider = str(runtime.get("ai_provider") or "openrouter").strip().lower()
    if provider == "gemini":
        provider = "google"
    model = (
        str(runtime.get("openai_model") or "gpt-4o-mini")
        if provider == "openai"
        else str(runtime.get("google_model") or "gemini-1.5-flash")
        if provider == "google"
        else str(runtime.get("openrouter_model") or "openai/gpt-4o-mini")
    )
    tx_hash = _hash_json(
        [
            {
                "external_transaction_id": t.get("external_transaction_id"),
                "booking_date": t.get("booking_date"),
                "amount": t.get("amount"),
                "currency": t.get("currency"),
                "counterparty_name": t.get("counterparty_name"),
                "remittance_information": t.get("remittance_information"),
                "movement_type": _tx_movement_type(t),
                "linked_document_context": t.get("linked_document_context"),
            }
            for t in tx_payload
        ]
    )
    mappings_hash = _hash_json(mappings if isinstance(mappings, list) else [])
    prompt_hash = _hash_json(prompt)
    source_hash = _hash_json(
        {
            "provider": provider,
            "model": model,
            "prompt_hash": prompt_hash,
            "mappings_hash": mappings_hash,
            "tx_hash": tx_hash,
        }
    )
    cached = db.query(BankBudgetAnalysisRun).filter(BankBudgetAnalysisRun.source_hash == source_hash).first()
    if cached:
        if csv_import_ids:
            db.query(BankCsvImport).filter(BankCsvImport.id.in_(csv_import_ids)).update(
                {
                    BankCsvImport.parsed_at: datetime.utcnow(),
                    BankCsvImport.parsed_source_hash: source_hash,
                },
                synchronize_session=False,
            )
            db.commit()
        cached_rows = (
            db.query(BankBudgetAnalysisTx)
            .filter(BankBudgetAnalysisTx.run_id == cached.id)
            .order_by(BankBudgetAnalysisTx.booking_date.asc(), BankBudgetAnalysisTx.created_at.asc())
            .all()
        )
        cached_summary = []
        try:
            loaded = json.loads(cached.summary_json or "[]")
            if isinstance(loaded, list):
                cached_summary = loaded
        except Exception:
            cached_summary = []
        merged = _build_budget_analysis_payload(
            [
                {
                    "external_transaction_id": r.external_transaction_id,
                    "booking_date": r.booking_date,
                    "amount": r.amount,
                    "currency": r.currency,
                    "counterparty_name": r.counterparty_name,
                    "remittance_information": r.remittance_information,
                    **next(
                        (
                            x
                            for x in tx_payload
                            if str(x.get("external_transaction_id") or "").strip()
                            == str(r.external_transaction_id or "").strip()
                        ),
                        {},
                    ),
                }
                for r in cached_rows
            ],
            {
                "summary_points": cached_summary,
                "transaction_categories": [
                    {
                        "external_transaction_id": r.external_transaction_id,
                        "category": r.category,
                        "flow": r.flow,
                        "reason": r.reason,
                    }
                    for r in cached_rows
                ],
            },
            mappings if isinstance(mappings, list) else [],
            preferred_categories=preferred_categories,
        )
        merged["transactions"] = _enrich_budget_transactions_with_doc_links(db, merged.get("transactions") or [])
        _sync_budget_categories_to_mapping_settings(db, merged.get("transactions"))
        _set_budget_progress(
            progress_user_id,
            running=False,
            processed=len(tx_payload),
            total=len(tx_payload),
            done=True,
        )
        return {
            "provider": cached.provider,
            "model": cached.model,
            "generated_at": cached.updated_at or cached.created_at,
            "prompt_used": bool(prompt),
            "mappings_count": len(mappings) if isinstance(mappings, list) else 0,
            "summary_points": merged.get("summary_points") or [],
            "transactions": merged.get("transactions") or [],
            "category_totals": merged.get("category_totals") or [],
            "year_totals": merged.get("year_totals") or [],
            "month_totals": merged.get("month_totals") or [],
        }

    llm_data: dict = {}
    try:
        llm_data = analyze_budget_transactions_with_llm(
            transactions=tx_payload,
            prompt_template=prompt,
            mappings=mappings if isinstance(mappings, list) else [],
            runtime=runtime,
            known_categories=preferred_categories,
            progress_callback=lambda processed, total: _set_budget_progress(
                progress_user_id,
                running=True,
                processed=processed,
                total=total,
                done=False,
            ),
        )
    except Exception as ex:
        _set_budget_progress(
            progress_user_id,
            running=False,
            processed=len(tx_payload),
            total=len(tx_payload),
            done=True,
            error=str(ex),
        )
        llm_data = {"summary_points": [f"LLM analyse fallback actief: {str(ex)}"], "transaction_categories": []}

    merged = _build_budget_analysis_payload(
        tx_payload,
        llm_data,
        mappings if isinstance(mappings, list) else [],
        preferred_categories=preferred_categories,
    )
    merged["transactions"] = _enrich_budget_transactions_with_doc_links(db, merged.get("transactions") or [])
    _sync_budget_categories_to_mapping_settings(db, merged.get("transactions"))
    run = BankBudgetAnalysisRun(
        source_hash=source_hash,
        provider=provider,
        model=model,
        prompt_hash=prompt_hash,
        mappings_hash=mappings_hash,
        transactions_hash=tx_hash,
        tx_count=len(tx_payload),
        summary_json=json.dumps(merged.get("summary_points") or [], ensure_ascii=False),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    for item in merged.get("transactions") or []:
        db.add(
            BankBudgetAnalysisTx(
                run_id=run.id,
                external_transaction_id=str(item.get("external_transaction_id") or ""),
                booking_date=item.get("booking_date"),
                amount=item.get("amount"),
                currency=item.get("currency"),
                counterparty_name=item.get("counterparty_name"),
                remittance_information=item.get("remittance_information"),
                flow=str(item.get("flow") or "expense"),
                category=str(item.get("category") or "Ongecategoriseerd"),
                source=str(item.get("source") or "llm"),
                reason=item.get("reason"),
            )
        )
    if csv_import_ids:
        db.query(BankCsvImport).filter(BankCsvImport.id.in_(csv_import_ids)).update(
            {
                BankCsvImport.parsed_at: datetime.utcnow(),
                BankCsvImport.parsed_source_hash: source_hash,
            },
            synchronize_session=False,
        )
    db.commit()
    _set_budget_progress(
        progress_user_id,
        running=False,
        processed=len(tx_payload),
        total=len(tx_payload),
        done=True,
    )
    return {
        "provider": provider,
        "model": model,
        "generated_at": run.updated_at or run.created_at,
        "prompt_used": bool(prompt),
        "mappings_count": len(mappings) if isinstance(mappings, list) else 0,
        "summary_points": merged.get("summary_points") or [],
        "transactions": merged.get("transactions") or [],
        "category_totals": merged.get("category_totals") or [],
        "year_totals": merged.get("year_totals") or [],
        "month_totals": merged.get("month_totals") or [],
    }


@app.get("/api/bank/budget/analyze/progress")
def get_budget_analyze_progress(current_user: User = Depends(get_current_user_dep)):
    require_admin_access(current_user)
    return _get_budget_progress(str(current_user.id))


@app.post("/api/bank/budget/refresh", response_model=BudgetAnalysisOut)
def refresh_bank_budget_from_mappings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    account = _get_or_create_csv_import_account(db)
    rows = (
        db.query(BankTransaction)
        .filter(BankTransaction.bank_account_id == account.id)
        .order_by(BankTransaction.booking_date.asc(), BankTransaction.created_at.asc())
        .all()
    )
    tx_payload = [bank_transaction_to_out(r) for r in rows]
    csv_import_ids = sorted({str(r.csv_import_id) for r in rows if r.csv_import_id})

    out_settings = settings_to_out(db)
    mappings = out_settings.get("bank_csv_mappings") if isinstance(out_settings, dict) else []
    preferred_categories = _preferred_budget_categories(mappings if isinstance(mappings, list) else [])
    prompt = str(out_settings.get("bank_csv_prompt") or "").strip() if isinstance(out_settings, dict) else ""
    tx_hash = _hash_json(
        [
            {
                "external_transaction_id": t.get("external_transaction_id"),
                "booking_date": t.get("booking_date"),
                "amount": t.get("amount"),
                "currency": t.get("currency"),
                "counterparty_name": t.get("counterparty_name"),
                "remittance_information": t.get("remittance_information"),
                "movement_type": _tx_movement_type(t),
                "linked_document_context": t.get("linked_document_context"),
            }
            for t in tx_payload
        ]
    )
    mappings_hash = _hash_json(mappings if isinstance(mappings, list) else [])
    source_hash = _hash_json(
        {
            "mode": "mapping-refresh",
            "mappings_hash": mappings_hash,
            "tx_hash": tx_hash,
        }
    )

    cached = db.query(BankBudgetAnalysisRun).filter(BankBudgetAnalysisRun.source_hash == source_hash).first()
    if cached:
        if csv_import_ids:
            db.query(BankCsvImport).filter(BankCsvImport.id.in_(csv_import_ids)).update(
                {
                    BankCsvImport.parsed_at: datetime.utcnow(),
                    BankCsvImport.parsed_source_hash: source_hash,
                },
                synchronize_session=False,
            )
            db.commit()
        cached_rows = (
            db.query(BankBudgetAnalysisTx)
            .filter(BankBudgetAnalysisTx.run_id == cached.id)
            .order_by(BankBudgetAnalysisTx.booking_date.asc(), BankBudgetAnalysisTx.created_at.asc())
            .all()
        )
        cached_summary = []
        try:
            loaded = json.loads(cached.summary_json or "[]")
            if isinstance(loaded, list):
                cached_summary = loaded
        except Exception:
            cached_summary = []
        merged = _build_budget_analysis_payload(
            [
                {
                    "external_transaction_id": r.external_transaction_id,
                    "booking_date": r.booking_date,
                    "amount": r.amount,
                    "currency": r.currency,
                    "counterparty_name": r.counterparty_name,
                    "remittance_information": r.remittance_information,
                    **next(
                        (
                            x
                            for x in tx_payload
                            if str(x.get("external_transaction_id") or "").strip()
                            == str(r.external_transaction_id or "").strip()
                        ),
                        {},
                    ),
                }
                for r in cached_rows
            ],
            {
                "summary_points": cached_summary,
                "transaction_categories": [
                    {
                        "external_transaction_id": r.external_transaction_id,
                        "category": r.category,
                        "flow": r.flow,
                        "reason": r.reason,
                    }
                    for r in cached_rows
                ],
            },
            mappings if isinstance(mappings, list) else [],
            preferred_categories=preferred_categories,
        )
        merged["transactions"] = _enrich_budget_transactions_with_doc_links(db, merged.get("transactions") or [])
        _sync_budget_categories_to_mapping_settings(db, merged.get("transactions"))
        return {
            "provider": cached.provider,
            "model": cached.model,
            "generated_at": cached.updated_at or cached.created_at,
            "prompt_used": bool(prompt),
            "mappings_count": len(mappings) if isinstance(mappings, list) else 0,
            "summary_points": merged.get("summary_points") or [],
            "transactions": merged.get("transactions") or [],
            "category_totals": merged.get("category_totals") or [],
            "year_totals": merged.get("year_totals") or [],
            "month_totals": merged.get("month_totals") or [],
        }

    previous_llm_run = (
        db.query(BankBudgetAnalysisRun)
        .filter(
            BankBudgetAnalysisRun.transactions_hash == tx_hash,
            BankBudgetAnalysisRun.provider != "mapping-refresh",
        )
        .order_by(BankBudgetAnalysisRun.created_at.desc())
        .first()
    )
    previous_tx_rows = []
    if previous_llm_run:
        previous_tx_rows = (
            db.query(BankBudgetAnalysisTx)
            .filter(BankBudgetAnalysisTx.run_id == previous_llm_run.id)
            .all()
        )
    previous_category_rows = [
        {
            "external_transaction_id": r.external_transaction_id,
            "category": r.category,
            "flow": r.flow,
            "reason": r.reason,
            "source": r.source,
        }
        for r in previous_tx_rows
    ]
    merged = _build_budget_analysis_payload(
        tx_payload,
        {
            "summary_points": ["Categorieën refreshed op basis van huidige mappings."],
            "transaction_categories": previous_category_rows,
        },
        mappings if isinstance(mappings, list) else [],
        preferred_categories=preferred_categories,
    )
    merged["transactions"] = _enrich_budget_transactions_with_doc_links(db, merged.get("transactions") or [])
    _sync_budget_categories_to_mapping_settings(db, merged.get("transactions"))
    run = BankBudgetAnalysisRun(
        source_hash=source_hash,
        provider="mapping-refresh",
        model="rules-only",
        prompt_hash=_hash_json(prompt),
        mappings_hash=mappings_hash,
        transactions_hash=tx_hash,
        tx_count=len(tx_payload),
        summary_json=json.dumps(merged.get("summary_points") or [], ensure_ascii=False),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    for item in merged.get("transactions") or []:
        db.add(
            BankBudgetAnalysisTx(
                run_id=run.id,
                external_transaction_id=str(item.get("external_transaction_id") or ""),
                booking_date=item.get("booking_date"),
                amount=item.get("amount"),
                currency=item.get("currency"),
                counterparty_name=item.get("counterparty_name"),
                remittance_information=item.get("remittance_information"),
                flow=str(item.get("flow") or "expense"),
                category=str(item.get("category") or "Ongecategoriseerd"),
                source=str(item.get("source") or "fallback"),
                reason=item.get("reason"),
            )
        )
    if csv_import_ids:
        db.query(BankCsvImport).filter(BankCsvImport.id.in_(csv_import_ids)).update(
            {
                BankCsvImport.parsed_at: datetime.utcnow(),
                BankCsvImport.parsed_source_hash: source_hash,
            },
            synchronize_session=False,
        )
    db.commit()
    return {
        "provider": "mapping-refresh",
        "model": "rules-only",
        "generated_at": run.updated_at or run.created_at,
        "prompt_used": bool(prompt),
        "mappings_count": len(mappings) if isinstance(mappings, list) else 0,
        "summary_points": merged.get("summary_points") or [],
        "transactions": merged.get("transactions") or [],
        "category_totals": merged.get("category_totals") or [],
        "year_totals": merged.get("year_totals") or [],
        "month_totals": merged.get("month_totals") or [],
    }


@app.get("/api/bank/import-csv/files", response_model=list[BankCsvImportOut])
def list_bank_csv_files(
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    parsed_ids = [
        r[0]
        for r in db.query(BankTransaction.csv_import_id)
        .filter(BankTransaction.csv_import_id.is_not(None))
        .distinct()
        .all()
        if r and r[0]
    ]
    if parsed_ids:
        db.query(BankCsvImport).filter(
            BankCsvImport.id.in_(parsed_ids),
            BankCsvImport.parsed_at.is_(None),
        ).update(
            {
                BankCsvImport.parsed_at: datetime.utcnow(),
                BankCsvImport.parsed_source_hash: "csv-import",
            },
            synchronize_session=False,
        )
        db.commit()
    rows = db.query(BankCsvImport).order_by(BankCsvImport.created_at.desc()).limit(limit).all()
    import_ids = [str(r.id) for r in rows if r and r.id]
    meta_by_import: dict[str, dict[str, str]] = {}
    if import_ids:
        tx_rows = (
            db.query(BankTransaction.csv_import_id, BankTransaction.raw_json)
            .filter(
                BankTransaction.csv_import_id.in_(import_ids),
                BankTransaction.raw_json.is_not(None),
            )
            .order_by(BankTransaction.created_at.asc())
            .all()
        )
        for csv_import_id, raw_json in tx_rows:
            key = str(csv_import_id or "").strip()
            if not key or key in meta_by_import:
                continue
            meta = _extract_csv_import_meta(raw_json)
            if meta.get("account_number") or meta.get("account_name") or meta.get("filter_date_from") or meta.get("filter_date_to"):
                meta_by_import[key] = meta
    return [bank_csv_import_to_out(r, meta_by_import.get(str(r.id), {})) for r in rows]


@app.delete("/api/bank/import-csv/files/{import_id}")
def delete_bank_csv_file(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    row = db.get(BankCsvImport, import_id)
    if not row:
        raise HTTPException(status_code=404, detail="CSV import niet gevonden")

    db.query(BankTransaction).filter(BankTransaction.csv_import_id == row.id).delete()
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.post("/api/bank/import-csv/mark-parsed")
def mark_bank_csv_as_parsed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    account = _get_or_create_csv_import_account(db)
    import_ids = [
        r[0]
        for r in (
            db.query(BankTransaction.csv_import_id)
            .filter(
                BankTransaction.bank_account_id == account.id,
                BankTransaction.csv_import_id.is_not(None),
            )
            .distinct()
            .all()
        )
        if r and r[0]
    ]
    if not import_ids:
        return {"updated": 0}
    updated = (
        db.query(BankCsvImport)
        .filter(BankCsvImport.id.in_(import_ids), BankCsvImport.parsed_at.is_(None))
        .update(
            {
                BankCsvImport.parsed_at: datetime.utcnow(),
                BankCsvImport.parsed_source_hash: "budget-view",
            },
            synchronize_session=False,
        )
    )
    db.commit()
    return {"updated": int(updated or 0)}


@app.post("/api/bank/budget/quick-map")
def quick_map_budget_category(
    payload: BudgetQuickCategoryMapIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    external_id = str(payload.external_transaction_id or "").strip()
    category = str(payload.category or "").strip()
    if not external_id or not category:
        raise HTTPException(status_code=400, detail="external_transaction_id en category zijn verplicht")

    account = _get_or_create_csv_import_account(db)
    tx = (
        db.query(BankTransaction)
        .filter(
            BankTransaction.bank_account_id == account.id,
            BankTransaction.external_transaction_id == external_id,
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transactie niet gevonden")

    keyword = str(tx.counterparty_name or "").strip() or str(tx.remittance_information or "").strip()
    if not keyword:
        keyword = external_id
    flow = "income" if float(tx.amount or 0) >= 0 else "expense"

    existing = (
        db.query(BankCategoryMapping)
        .filter(
            func.lower(BankCategoryMapping.keyword) == keyword.lower(),
            BankCategoryMapping.flow == flow,
            BankCategoryMapping.is_active.is_(True),
        )
        .first()
    )
    if existing:
        existing.category = category
    else:
        max_priority = db.query(func.max(BankCategoryMapping.priority)).scalar()
        db.add(
            BankCategoryMapping(
                keyword=keyword,
                flow=flow,
                category=category,
                priority=int(max_priority or 0) + 1,
                is_active=True,
            )
        )
    db.commit()
    return {"ok": True, "keyword": keyword, "flow": flow, "category": category}


@app.post("/api/documents", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    if not file.content_type or not allowed_content_type(file.content_type):
        raise HTTPException(status_code=400, detail="Unsupported bestandstype")

    member_group_ids = user_group_ids(current_user)
    if not member_group_ids:
        raise HTTPException(status_code=400, detail="Gebruiker heeft geen groep")

    auto_group_id = sorted(member_group_ids)[0]

    ext = Path(file.filename or "document").suffix or ".bin"
    document_id = str(uuid.uuid4())
    storage_name = f"{document_id}{ext}"
    file_path = Path(settings.uploads_dir) / storage_name

    data = await file.read()
    file_path.write_bytes(data)

    doc = Document(
        id=document_id,
        filename=file.filename or storage_name,
        content_type=file.content_type,
        file_path=str(file_path),
        group_id=auto_group_id,
        uploaded_by_user_id=current_user.id,
        paid=False,
        ocr_processed=False,
        ai_processed=False,
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document_job, document_id, None)
    return document_to_out(doc)


@app.get("/api/documents", response_model=list[DocumentOut])
def list_documents(
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    can_see_all = _current_user_can_see_all_groups(current_user)
    group_ids = user_group_ids(current_user)
    if not can_see_all and not group_ids:
        return []
    _purge_expired_deleted_docs(db)

    q = db.query(Document).filter(Document.deleted_at.is_(None))
    if not can_see_all:
        q = q.filter(Document.group_id.in_(group_ids))
    docs = q.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()
    return [document_to_out(d) for d in docs]


@app.post("/api/documents/check-bank")
def check_documents_against_bank_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    from app.db import upsert_search_index

    can_see_all = _current_user_can_see_all_groups(current_user)
    group_ids = set(user_group_ids(current_user))

    docs_q = db.query(Document).filter(
        Document.deleted_at.is_(None),
        func.lower(Document.category).in_(["factuur", "rekening", "kasticket"]),
        Document.total_amount.is_not(None),
    )
    if not can_see_all:
        if not group_ids:
            return {"checked": 0, "matched": 0, "updated_document_ids": []}
        docs_q = docs_q.filter(Document.group_id.in_(group_ids))
    docs = docs_q.all()

    txs = (
        db.query(BankTransaction)
        .filter(BankTransaction.amount.is_not(None), BankTransaction.amount < 0)
        .all()
    )
    runtime = get_runtime_settings(db)

    updated_ids: list[str] = []
    now = datetime.utcnow().strftime("%Y-%m-%d")
    for doc in docs:
        best_score = -1
        best_confidence = "none"
        best_reason = ""
        best_tx: BankTransaction | None = None
        for tx in txs:
            score, confidence, reason = _tx_match_score(doc, tx)
            if score > best_score:
                best_score = score
                best_confidence = confidence
                best_reason = reason
                best_tx = tx

        # For receipts, allow a second-pass LLM pattern check on short candidate list
        # when rule-based score is not yet strong enough.
        if (not best_tx or best_score < 60) and (str(doc.category or "").strip().lower() == "kasticket"):
            llm_candidates = [tx for tx in txs if _tx_candidate_for_llm(doc, tx)]
            if llm_candidates:
                doc_payload = {
                    "id": doc.id,
                    "category": doc.category,
                    "issuer": doc.issuer,
                    "subject": doc.subject,
                    "document_date": doc.document_date,
                    "due_date": doc.due_date,
                    "total_amount": doc.total_amount,
                    "currency": doc.currency,
                    "iban": doc.iban,
                    "structured_reference": doc.structured_reference,
                }
                tx_payload = [
                    {
                        "external_transaction_id": tx.external_transaction_id,
                        "booking_date": tx.booking_date,
                        "amount": tx.amount,
                        "currency": tx.currency,
                        "counterparty_name": tx.counterparty_name,
                        "remittance_information": tx.remittance_information,
                        "raw_json": tx.raw_json,
                    }
                    for tx in llm_candidates[:8]
                ]
                llm_match = match_document_payment_with_llm(
                    document=doc_payload,
                    candidates=tx_payload,
                    runtime=runtime,
                )
                if llm_match.get("matched") and llm_match.get("external_transaction_id"):
                    ext = str(llm_match.get("external_transaction_id") or "").strip()
                    picked = next((tx for tx in llm_candidates if str(tx.external_transaction_id) == ext), None)
                    if picked:
                        best_tx = picked
                        best_confidence = str(llm_match.get("confidence") or "low")
                        llm_reason = str(llm_match.get("reason") or "").strip()
                        best_reason = (
                            f"LLM patroonherkenning: {llm_reason}" if llm_reason else "LLM patroonherkenning"
                        )
                        best_score = 70 if best_confidence == "low" else 85

        # Require a sufficiently confident match to avoid false positives.
        if not best_tx or best_score < 60:
            continue

        doc.paid = True
        doc.bank_paid_verified = True
        doc.paid_on = str(best_tx.booking_date or doc.paid_on or now)
        bank_remark = _build_bank_check_remark(best_tx, confidence=best_confidence, reason=best_reason)
        current_remark = str(doc.remark or "").strip()
        if bank_remark not in current_remark:
            doc.remark = f"{current_remark}\n{bank_remark}".strip() if current_remark else bank_remark
        doc.searchable_text = _build_searchable_text(doc)
        updated_ids.append(doc.id)

    if updated_ids:
        db.commit()
        for doc_id in updated_ids:
            row = db.get(Document, doc_id)
            if row:
                upsert_search_index(doc_id, row.searchable_text or "")
    else:
        db.rollback()

    return {
        "checked": len(docs),
        "matched": len(updated_ids),
        "updated_document_ids": updated_ids,
    }


@app.get("/api/documents/trash", response_model=list[DocumentOut])
def list_deleted_documents(
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    can_see_all = _current_user_can_see_all_groups(current_user)
    group_ids = user_group_ids(current_user)
    if not can_see_all and not group_ids:
        return []
    _purge_expired_deleted_docs(db)

    q = db.query(Document).filter(Document.deleted_at.is_not(None))
    if not can_see_all:
        q = q.filter(Document.group_id.in_(group_ids))
    docs = q.order_by(Document.deleted_at.desc()).offset(offset).limit(limit).all()
    return [document_to_out(d) for d in docs]


@app.post("/api/documents/delete")
def soft_delete_documents(
    payload: BulkDocumentIdsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    if not payload.document_ids:
        return {"count": 0}

    count = 0
    now = datetime.utcnow()
    for doc_id in payload.document_ids:
        doc = ensure_doc_access(db.get(Document, doc_id), current_user, allow_deleted=True)
        if doc.deleted_at is not None:
            continue
        doc.deleted_at = now
        count += 1

    db.commit()
    with engine.begin() as conn:
        for doc_id in payload.document_ids:
            conn.execute(text("DELETE FROM document_search WHERE document_id = :id"), {"id": doc_id})
    return {"count": count}


@app.post("/api/documents/restore")
def restore_documents(
    payload: BulkDocumentIdsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    from app.db import upsert_search_index

    if not payload.document_ids:
        return {"count": 0}

    can_see_all = _current_user_can_see_all_groups(current_user)
    group_ids = set(user_group_ids(current_user))
    count = 0
    for doc_id in payload.document_ids:
        doc = db.get(Document, doc_id)
        if not doc:
            continue
        if not can_see_all and doc.group_id not in group_ids:
            continue
        if doc.deleted_at is None:
            continue
        doc.deleted_at = None
        count += 1

    db.commit()

    for doc_id in payload.document_ids:
        doc = db.get(Document, doc_id)
        if doc and doc.deleted_at is None and doc.searchable_text:
            upsert_search_index(doc.id, doc.searchable_text or "")

    return {"count": count}


@app.get("/api/documents/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    doc = ensure_doc_access(db.get(Document, document_id), current_user)
    return document_to_out(doc)


@app.post("/api/documents/{document_id}/reprocess", response_model=DocumentOut)
def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    doc = ensure_doc_access(db.get(Document, document_id), current_user)
    doc.status = "uploaded"
    doc.error_message = None
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document_job, document_id, None, True)
    return document_to_out(doc)


@app.put("/api/documents/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: str,
    payload: UpdateDocumentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    from app.db import upsert_search_index

    doc = ensure_doc_access(db.get(Document, document_id), current_user)

    updateable_fields = [
        "subject",
        "issuer",
        "document_date",
        "due_date",
        "total_amount",
        "currency",
        "iban",
        "structured_reference",
        "paid",
        "paid_on",
        "remark",
        "line_items",
    ]
    fields_set = getattr(payload, "model_fields_set", getattr(payload, "__fields_set__", set()))
    for field in updateable_fields:
        # Respect explicit nulls from client (required for category-based hidden fields).
        if field in fields_set:
            setattr(doc, field, getattr(payload, field))
    if "paid" in fields_set and not bool(payload.paid):
        doc.bank_paid_verified = False

    if "extra_fields" in fields_set:
        extra = payload.extra_fields or {}
        cleaned = {
            str(k).strip(): str(v).strip()
            for k, v in extra.items()
            if str(k).strip() and v is not None and str(v).strip()
        }
        doc.extra_fields_json = json.dumps(cleaned, ensure_ascii=False) if cleaned else None

    if payload.category is not None:
        raw_category = (payload.category or "").strip()
        if not raw_category:
            doc.category = None
        else:
            resolved = _resolve_category(db, raw_category, [doc.group_id] if doc.group_id else None)
            if resolved:
                doc.category = resolved

    if payload.label_ids is not None:
        labels = []
        if payload.label_ids:
            labels = db.query(Label).filter(Label.id.in_(payload.label_ids), Label.group_id == doc.group_id).all()
        doc.labels = labels

    doc.searchable_text = _build_searchable_text(doc)
    db.commit()
    db.refresh(doc)
    upsert_search_index(doc.id, doc.searchable_text or "")
    return document_to_out(doc)


@app.get("/api/search", response_model=list[DocumentOut])
def search_documents(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    can_see_all = _current_user_can_see_all_groups(current_user)
    group_ids = user_group_ids(current_user)
    if not can_see_all and not group_ids:
        return []

    query = q.replace('"', " ").strip()
    try:
        with engine.begin() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT document_id
                    FROM document_search
                    WHERE content MATCH :q
                    LIMIT :limit
                    """
                ),
                {"q": query, "limit": limit * 3},
            ).mappings().all()
    except Exception:
        return []

    doc_ids = [r["document_id"] for r in rows]
    if not doc_ids:
        return []

    q = db.query(Document).filter(Document.id.in_(doc_ids), Document.deleted_at.is_(None))
    if not can_see_all:
        q = q.filter(Document.group_id.in_(group_ids))
    docs = q.order_by(Document.created_at.desc()).limit(limit).all()
    return [document_to_out(d) for d in docs]


@app.get("/files/{document_id}")
def download_original(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    doc = ensure_doc_access(db.get(Document, document_id), current_user)
    return FileResponse(doc.file_path, filename=doc.filename)


Path(settings.thumbnails_dir).mkdir(parents=True, exist_ok=True)
Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
Path(settings.avatars_dir).mkdir(parents=True, exist_ok=True)
app.mount("/thumbnails", StaticFiles(directory=settings.thumbnails_dir), name="thumbnails")
app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
app.mount("/avatars", StaticFiles(directory=settings.avatars_dir), name="avatars")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
