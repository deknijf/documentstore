import uuid
from datetime import datetime, timedelta
from difflib import get_close_matches
import json
import hashlib
import traceback
import logging
import smtplib
import ssl
import secrets
from pathlib import Path
import re
from threading import Lock, Thread, Event
from urllib.parse import quote
from email.message import EmailMessage

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, UploadFile, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text, func, or_, and_
from sqlalchemy.orm import Session

from app.config import settings
from app.db import (
    SessionLocal,
    ensure_bootstrap_admin,
    engine,
    get_default_tenant_id,
    init_db,
    rebuild_search_index_for_all_documents,
)
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
    IntegrationSettings,
    Label,
    PasswordResetToken,
    SessionToken,
    AsyncJob,
    Tenant,
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
    CreateTenantIn,
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
    ForgotPasswordIn,
    LoginIn,
    ResetPasswordIn,
    SignupIn,
    SetDocumentLabelsIn,
    SwitchTenantIn,
    TenantOut,
    UpdateCategoryIn,
    UpdateDocumentIn,
    UpdateIntegrationSettingsIn,
    UpdateMeIn,
    UpdateTenantIn,
    UpdateUserIn,
    UserOut,
)
from app.services.auth import (
    ROLE_ADMIN,
    ROLE_SUPERADMIN,
    ROLE_USER,
    extract_bearer_token,
    group_to_out,
    issue_token,
    require_admin_access,
    require_bootstrap_admin,
    hash_password,
    user_group_ids,
    user_is_admin,
    user_role,
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
from app.services.audit import audit_log

app = FastAPI(title=settings.app_name)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("docstore")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BUDGET_ANALYZE_PROGRESS: dict[str, dict] = {}
BUDGET_ANALYZE_LOCK = Lock()
MAIL_INGEST_RUN_LOCK = Lock()
MAIL_INGEST_LAST_RUN_AT: dict[str, datetime] = {}
MAIL_INGEST_STOP_EVENT = Event()
MAIL_INGEST_THREAD: Thread | None = None
GROUPS_ENABLED = False


def _slugify_tenant(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    base = re.sub(r"-{2,}", "-", base)
    return (base or "tenant")[:64]


def _ensure_unique_tenant_slug(db: Session, value: str) -> str:
    base = _slugify_tenant(value)
    candidate = base
    seq = 2
    while db.query(Tenant).filter(func.lower(Tenant.slug) == candidate.lower()).first():
        suffix = f"-{seq}"
        candidate = f"{base[: max(1, 64 - len(suffix))]}{suffix}"
        seq += 1
    return candidate


def _tenant_for_id(db: Session, tenant_id: str) -> Tenant:
    row = db.query(Tenant).filter(Tenant.id == str(tenant_id or "").strip()).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tenant niet gevonden")
    return row


def _send_smtp_email(runtime: dict[str, str | None], recipient: str, subject: str, body_text: str) -> None:
    host = str(runtime.get("smtp_server") or "").strip()
    port = int(runtime.get("smtp_port") or 587)
    username = str(runtime.get("smtp_username") or "").strip()
    password = str(runtime.get("smtp_password") or "")
    sender = str(runtime.get("smtp_sender_email") or username or "").strip()
    if not host or not username or not password or not sender:
        raise RuntimeError("SMTP niet volledig geconfigureerd")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body_text)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(msg)

def _split_csv_env(value: str) -> list[str]:
    return [p.strip() for p in (value or "").split(",") if p.strip()]


# Limit allowed Host headers in production (prevents Host header attacks).
allowed_hosts = _split_csv_env(settings.allowed_hosts)
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# CORS: Only needed when frontend is served from a different origin.
cors_origins = _split_csv_env(settings.cors_allow_origins)
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Dev-friendly default: allow all origins, but without credentials.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
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


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()

def _create_async_job_db(db: Session, *, job_type: str, tenant_id: str, user_id: str) -> str:
    row = AsyncJob(
        tenant_id=tenant_id,
        job_type=str(job_type),
        status="queued",
        user_id=user_id,
        processed=0,
        total=0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return str(row.id)


def _async_job_to_dict(row: AsyncJob) -> dict:
    result = None
    try:
        result = json.loads(row.result_json) if row.result_json else None
    except Exception:
        result = None
    return {
        "id": str(row.id),
        "type": str(row.job_type),
        "tenant_id": str(row.tenant_id),
        "user_id": str(row.user_id),
        "status": str(row.status),
        "processed": int(row.processed or 0),
        "total": int(row.total or 0),
        "error": row.error,
        "result": result,
        "created_at": (row.created_at.isoformat() if row.created_at else None),
        "updated_at": (row.updated_at.isoformat() if row.updated_at else None),
        "started_at": (row.started_at.isoformat() if row.started_at else None),
        "finished_at": (row.finished_at.isoformat() if row.finished_at else None),
    }


def _update_async_job_db(db: Session, job_id: str, **fields) -> None:
    row = db.query(AsyncJob).filter(AsyncJob.id == job_id).first()
    if not row:
        return
    for k, v in fields.items():
        if k == "result":
            setattr(row, "result_json", json.dumps(v or {}, ensure_ascii=True, default=str))
        else:
            setattr(row, k, v)
    db.commit()


def _get_async_job_db(db: Session, job_id: str) -> dict | None:
    row = db.query(AsyncJob).filter(AsyncJob.id == job_id).first()
    return _async_job_to_dict(row) if row else None


def _find_running_async_job_db(db: Session, *, tenant_id: str, job_type: str) -> dict | None:
    row = (
        db.query(AsyncJob)
        .filter(
            AsyncJob.tenant_id == tenant_id,
            AsyncJob.job_type == job_type,
            AsyncJob.status.in_(["queued", "running"]),
        )
        .order_by(AsyncJob.created_at.desc())
        .first()
    )
    return _async_job_to_dict(row) if row else None


def _startup_guardrails_and_cleanup(db: Session) -> None:
    # Production guardrails: fail fast if critical settings are unsafe.
    if str(settings.environment or "").strip().lower() == "production":
        if not str(settings.allowed_hosts or "").strip():
            raise RuntimeError("ALLOWED_HOSTS is verplicht in productie")
        if str(settings.integration_master_key or "").strip() in {"", "change-this-in-production"}:
            raise RuntimeError("INTEGRATION_MASTER_KEY moet aangepast worden in productie")

    # If the process restarted, any in-process jobs are lost. Mark 'running' jobs as failed
    # so the UI doesn't show them as stuck forever.
    try:
        db.query(AsyncJob).filter(AsyncJob.status == "running").update(
            {
                AsyncJob.status: "failed",
                AsyncJob.error: "Server restart: job interrupted",
                AsyncJob.finished_at: datetime.utcnow(),
            },
            synchronize_session=False,
        )
        db.commit()
    except Exception:
        db.rollback()


def process_document_job(document_id: str, ocr_provider: str | None = None, force: bool = False) -> None:
    db = SessionLocal()
    try:
        process_document(db, document_id, ocr_provider, force=force)
    finally:
        db.close()


def _start_async_job(job_id: str, worker) -> None:
    def _runner():
        db = SessionLocal()
        try:
            _update_async_job_db(db, job_id, status="running", started_at=datetime.utcnow())
            try:
                result = worker(
                    lambda p, t: _update_async_job_db(db, job_id, processed=int(p or 0), total=int(t or 0))
                )
                completed = int(
                    (result or {}).get("checked")
                    or (result or {}).get("total")
                    or len((result or {}).get("transactions") or [])
                )
                _update_async_job_db(
                    db,
                    job_id,
                    status="done",
                    finished_at=datetime.utcnow(),
                    result=result,
                    processed=completed,
                    total=completed,
                )
            except Exception as ex:
                log.exception("async job failed: %s", job_id)
                _update_async_job_db(
                    db,
                    job_id,
                    status="failed",
                    finished_at=datetime.utcnow(),
                    error=f"{type(ex).__name__}: {ex}",
                    result={"traceback": traceback.format_exc(limit=12)},
                )
        finally:
            db.close()

    thread = Thread(target=_runner, daemon=True)
    thread.start()


def _run_mail_ingest_once(*, triggered_by_user_id: str | None = None, tenant_id_override: str | None = None) -> dict:
    global MAIL_INGEST_LAST_RUN_AT
    if not MAIL_INGEST_RUN_LOCK.acquire(blocking=False):
        return {"ok": False, "detail": "Mail ingest loopt al"}
    try:
        db = SessionLocal()
        try:
            tenant_id = str(tenant_id_override or "").strip()
            uploader_id = triggered_by_user_id
            if not uploader_id:
                admin_q = db.query(User).filter(User.is_bootstrap_admin.is_(True))
                if tenant_id:
                    admin_q = admin_q.filter(User.tenant_id == tenant_id)
                admin_user = admin_q.order_by(User.created_at.asc()).first()
                uploader_id = str(admin_user.id) if admin_user else None
                if not tenant_id:
                    tenant_id = str(admin_user.tenant_id or "") if admin_user else ""
            else:
                uploader = db.query(User).filter(User.id == uploader_id).first()
                tenant_id = str(uploader.tenant_id or "") if uploader else ""
            if not tenant_id:
                tenant_id = get_default_tenant_id()
            runtime = get_runtime_settings(db, tenant_id=tenant_id)
            if not bool(runtime.get("mail_ingest_enabled")):
                return {"ok": False, "detail": "Mail ingest staat uit"}

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
                tenant_id=tenant_id,
            )
            for document_id in result.get("document_ids") or []:
                process_document_job(str(document_id), None)
            MAIL_INGEST_LAST_RUN_AT[tenant_id] = datetime.utcnow()
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
                tenant_rows = (
                    db.query(IntegrationSettings.tenant_id)
                    .filter(IntegrationSettings.mail_ingest_enabled.is_(True))
                    .distinct()
                    .all()
                )
            finally:
                db.close()
            for row in tenant_rows:
                tenant_id = str(row[0] or "").strip()
                if not tenant_id:
                    continue
                db_tenant = SessionLocal()
                try:
                    runtime = get_runtime_settings(db_tenant, tenant_id=tenant_id)
                    enabled = bool(runtime.get("mail_ingest_enabled"))
                    freq_min = max(0, int(runtime.get("mail_ingest_frequency_minutes") or 0))
                finally:
                    db_tenant.close()
                if not enabled or freq_min <= 0:
                    continue
                now = datetime.utcnow()
                last = MAIL_INGEST_LAST_RUN_AT.get(tenant_id)
                if not last or (now - last) >= timedelta(minutes=freq_min):
                    _run_mail_ingest_once(triggered_by_user_id=None, tenant_id_override=tenant_id)
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
    if n == "attest":
        fields = [
            "category",
            "issuer",
            "subject",
            "document_date",
            "beneficiary",
            "tax_year",
            "reference_number",
            "period_from",
            "period_to",
            "total_amount",
            "currency",
            "summary",
        ]
        cfg = [
            {"key": "category", "visible_in_overview": True},
            {"key": "issuer", "visible_in_overview": True},
            {"key": "subject", "visible_in_overview": True},
            {"key": "document_date", "visible_in_overview": True},
            {"key": "beneficiary", "visible_in_overview": True},
            {"key": "tax_year", "visible_in_overview": True},
            {"key": "summary", "visible_in_overview": False},
            {"key": "reference_number", "visible_in_overview": False},
            {"key": "period_from", "visible_in_overview": False},
            {"key": "period_to", "visible_in_overview": False},
            {"key": "total_amount", "visible_in_overview": False},
            {"key": "currency", "visible_in_overview": False},
        ]
        return {
            "prompt_template": (
                "Dit document is een attest (bewijs/verklaring/certificaat) dat een persoon of organisatie "
                "een activiteit/feit bevestigt, vaak voor overheid/belastingen.\n\n"
                "Geef strikte JSON terug (geen extra tekst) met deze velden:\n"
                "- category (string, altijd 'attest')\n"
                "- issuer (string|null): afzender/instantie die het attest uitreikt\n"
                "- subject (string|null): korte titel/onderwerp van het attest\n"
                "- document_date (YYYY-MM-DD|null): opmaakdatum van het attest\n"
                "- beneficiary (string|null): naam van de persoon/organisatie voor wie het attest geldt\n"
                "- tax_year (string|null): relevant aanslagjaar/belastingjaar (bv '2025')\n"
                "- reference_number (string|null): dossier-/referentienummer\n"
                "- period_from (YYYY-MM-DD|null): start van de periode (indien vermeld)\n"
                "- period_to (YYYY-MM-DD|null): einde van de periode (indien vermeld)\n"
                "- total_amount (number|null) en currency (string|null) enkel als er een bedrag in het attest staat\n"
                "- summary (string|null): 1 zin samenvatting\n\n"
                "Herken synoniemen: attest, attestation, certificate, verklaring, bewijs, certificaat.\n"
                "Zet onbekende velden op null. Datums altijd ISO (YYYY-MM-DD)."
            ),
            "parse_fields": fields,
            "parse_config": cfg,
            "paid_default": False,
        }
    return {
        "prompt_template": base_prompt,
        "parse_fields": base_fields,
        "parse_config": base_config,
        "paid_default": False,
    }


def _tenant_id_for_user(user: User) -> str:
    tenant_id = str(getattr(user, "active_tenant_id", None) or getattr(user, "tenant_id", "") or "").strip()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Gebruiker heeft geen tenant")
    return tenant_id


def _tenant_name_for_id(db: Session, tenant_id: str) -> str:
    row = db.query(Tenant).filter(Tenant.id == str(tenant_id or "").strip()).first()
    return str(getattr(row, "name", "") or "")


def _tenant_stats(db: Session, tenant_id: str) -> dict[str, int]:
    users_count = db.query(func.count(User.id)).filter(User.tenant_id == tenant_id).scalar() or 0
    admins_count = (
        db.query(func.count(func.distinct(User.id)))
        .outerjoin(User.groups)
        .filter(User.tenant_id == tenant_id)
        .filter(
            or_(
                User.is_bootstrap_admin.is_(True),
                and_(Group.tenant_id == tenant_id, func.lower(Group.name).like("administrators%")),
            )
        )
        .scalar()
        or 0
    )
    documents_count = db.query(func.count(Document.id)).filter(Document.tenant_id == tenant_id).scalar() or 0
    transactions_count = db.query(func.count(BankTransaction.id)).filter(BankTransaction.tenant_id == tenant_id).scalar() or 0
    groups_count = db.query(func.count(Group.id)).filter(Group.tenant_id == tenant_id).scalar() or 0
    return {
        "users_count": int(users_count),
        "admins_count": int(admins_count),
        "groups_count": int(groups_count),
        "documents_count": int(documents_count),
        "transactions_count": int(transactions_count),
    }


def _find_tenant_admin_group(db: Session, tenant_id: str) -> Group | None:
    return (
        db.query(Group)
        .filter(Group.tenant_id == tenant_id)
        .filter(func.lower(Group.name).like("administrators%"))
        .order_by(Group.created_at.asc())
        .first()
    )


def _ensure_tenant_admin_group(db: Session, tenant_id: str) -> Group:
    existing = _find_tenant_admin_group(db, tenant_id)
    if existing:
        return existing
    group = Group(tenant_id=tenant_id, name=f"Administrators ({tenant_id[:8]})")
    db.add(group)
    db.flush()
    return group


def _ensure_tenant_user_group(db: Session, tenant_id: str) -> Group:
    existing = (
        db.query(Group)
        .filter(Group.tenant_id == tenant_id)
        .filter(
            or_(
                func.lower(Group.name).in_(["gebruikers", "users"]),
                func.lower(Group.name).like("gebruikers%"),
                func.lower(Group.name).like("users%"),
            )
        )
        .order_by(Group.created_at.asc())
        .first()
    )
    if existing:
        return existing
    group = Group(tenant_id=tenant_id, name=f"Gebruikers ({tenant_id[:8]})")
    db.add(group)
    db.flush()
    return group


def _apply_user_role(
    db: Session,
    user: User,
    tenant_id: str,
    role: str | None,
    actor: User,
) -> None:
    desired = str(role or "").strip().lower() or ROLE_USER
    if desired not in {ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_USER}:
        raise HTTPException(status_code=400, detail="Ongeldige permissie")
    if desired == ROLE_SUPERADMIN and not actor.is_bootstrap_admin:
        raise HTTPException(status_code=403, detail="Alleen superadmin kan superadmin toekennen")

    admin_group = _find_tenant_admin_group(db, tenant_id)
    if desired == ROLE_SUPERADMIN:
        user.is_bootstrap_admin = True
        if admin_group and admin_group not in (user.groups or []):
            user.groups = [*list(user.groups or []), admin_group]
        return

    user.is_bootstrap_admin = False
    if desired == ROLE_ADMIN:
        admin_group = admin_group or _ensure_tenant_admin_group(db, tenant_id)
        current = [g for g in (user.groups or []) if str(getattr(g, "tenant_id", "") or "") == tenant_id]
        if admin_group not in current:
            current.append(admin_group)
        user.groups = current
        return

    # gewone gebruiker: haal admin-groep weg, maar behoud/maak niet-admin groepen voor documenttoegang
    non_admin_groups = [
        g
        for g in (user.groups or [])
        if str(getattr(g, "tenant_id", "") or "") == tenant_id and not (g.name or "").strip().lower().startswith("administrators")
    ]
    if not non_admin_groups:
        non_admin_groups = [_ensure_tenant_user_group(db, tenant_id)]
    user.groups = non_admin_groups


def _current_session_token(db: Session, authorization: str | None) -> SessionToken:
    raw = extract_bearer_token(authorization)
    row = db.query(SessionToken).filter(SessionToken.token == raw).first()
    if not row:
        raise HTTPException(status_code=401, detail="Ongeldige sessie")
    return row


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


def _get_category_profiles(db: Session, tenant_id: str, group_ids: list[str] | None = None) -> list[dict]:
    names = _get_existing_categories(db, tenant_id, group_ids)
    rows = db.query(CategoryCatalog).filter(CategoryCatalog.tenant_id == tenant_id).all()
    row_map = {r.name.lower(): r for r in rows}
    out = []
    for n in names:
        out.append(_category_to_out(row_map.get(n.lower()), n))
    return out


def _get_existing_categories(db: Session, tenant_id: str, group_ids: list[str] | None = None) -> list[str]:
    q = db.query(Document.category).filter(Document.category.is_not(None), Document.deleted_at.is_(None))
    q = q.filter(Document.tenant_id == tenant_id)
    if group_ids:
        q = q.filter(Document.group_id.in_(group_ids))
    from_docs = [row[0] for row in q.distinct().all() if row[0]]
    from_catalog = [row[0] for row in db.query(CategoryCatalog.name).filter(CategoryCatalog.tenant_id == tenant_id).all() if row[0]]
    baseline = ["factuur", "rekening", "kasticket"]
    merged = sorted({c.strip() for c in from_docs + from_catalog + baseline if c and c.strip()})
    return merged


def _resolve_category(db: Session, tenant_id: str, candidate: str | None, group_ids: list[str] | None = None) -> str | None:
    if not candidate:
        return None
    raw = candidate.strip()
    if not raw:
        return None

    existing = _get_existing_categories(db, tenant_id, group_ids)
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
        "duplicate_of_document_id": getattr(doc, "duplicate_of_document_id", None),
        "duplicate_reason": getattr(doc, "duplicate_reason", None),
        "duplicate_resolved": bool(getattr(doc, "duplicate_resolved", True)),
        "paid": bool(doc.paid),
        "paid_on": doc.paid_on,
        "bank_paid_verified": bool(getattr(doc, "bank_paid_verified", False)),
        "bank_match_score": getattr(doc, "bank_match_score", None),
        "bank_match_confidence": getattr(doc, "bank_match_confidence", None),
        "bank_match_reason": getattr(doc, "bank_match_reason", None),
        "bank_match_external_transaction_id": getattr(doc, "bank_match_external_transaction_id", None),
        "bank_paid_category": getattr(doc, "bank_paid_category", None),
        "bank_paid_category_source": getattr(doc, "bank_paid_category_source", None),
        "budget_category": getattr(doc, "budget_category", None),
        "budget_category_source": getattr(doc, "budget_category_source", None),
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
        "tenant_id": row.tenant_id,
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
        "tenant_id": row.tenant_id,
        "bank_account_id": row.bank_account_id,
        "external_transaction_id": row.external_transaction_id,
        "dedupe_hash": getattr(row, "dedupe_hash", None),
        "csv_import_id": row.csv_import_id,
        "booking_date": row.booking_date,
        "value_date": row.value_date,
        "amount": row.amount,
        "currency": row.currency,
        "counterparty_name": row.counterparty_name,
        "remittance_information": row.remittance_information,
        "movement_type": _tx_movement_type({"movement_type": None, "raw_json": row.raw_json}),
        "category": row.category,
        "source": row.source,
        "auto_mapping": bool(getattr(row, "auto_mapping", False)),
        "llm_mapping": bool(getattr(row, "llm_mapping", False)),
        "manual_mapping": bool(getattr(row, "manual_mapping", False)),
        "raw_json": row.raw_json,
        "created_at": row.created_at,
    }


def bank_csv_import_to_out(row: BankCsvImport, meta: dict | None = None) -> dict:
    meta = meta or {}
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
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


def _ensure_bank_category_labels(db: Session, tenant_id: str) -> None:
    """
    Synchronize bank mapping categories into document labels (tenant-wide).
    Labels are used in the UI as badges on paid documents, and as searchable facets.
    """
    # Keep labels in a single tenant group when GROUPS_ENABLED is off.
    grp = _ensure_tenant_user_group(db, tenant_id)
    if not grp.id:
        db.flush()
    group_id = grp.id

    cats = [
        c[0]
        for c in db.query(BankCategoryMapping.category)
        .filter(BankCategoryMapping.tenant_id == tenant_id, BankCategoryMapping.is_active == True)  # noqa: E712
        .distinct()
        .all()
        if c and c[0]
    ]
    cats = [str(x).strip() for x in cats if str(x or "").strip()]
    if not cats:
        return

    existing = {
        (str(l.name or "").strip().lower()): l
        for l in db.query(Label).filter(Label.tenant_id == tenant_id, Label.group_id == group_id).all()
    }
    created = 0
    for cat in sorted(set(cats), key=lambda x: x.lower()):
        if cat.lower() in existing:
            continue
        db.add(Label(tenant_id=tenant_id, name=cat, group_id=group_id))
        created += 1
    if created:
        db.commit()


def _ensure_doc_has_label(db: Session, doc: Document, label_name: str) -> None:
    if not label_name:
        return
    label_name = str(label_name or "").strip()
    if not label_name:
        return
    grp = _ensure_tenant_user_group(db, doc.tenant_id)
    if not grp.id:
        db.flush()
    group_id = grp.id
    label = (
        db.query(Label)
        .filter(
            Label.tenant_id == doc.tenant_id,
            Label.group_id == group_id,
            func.lower(func.trim(Label.name)) == label_name.lower(),
        )
        .first()
    )
    if not label:
        label = Label(tenant_id=doc.tenant_id, name=label_name.strip(), group_id=group_id)
        db.add(label)
        db.commit()
        db.refresh(label)
    if label not in (doc.labels or []):
        doc.labels.append(label)


def _ensure_doc_single_label(db: Session, doc: Document) -> bool:
    """
    Docstore currently treats labels as a single primary label per document (budget category).
    This helper enforces that invariant by keeping only the primary label:
    - Prefer doc.budget_category, then doc.bank_paid_category, otherwise keep first existing label.
    Returns True if a change was applied.
    """
    target = str(getattr(doc, "budget_category", "") or "").strip() or str(getattr(doc, "bank_paid_category", "") or "").strip()
    existing = list(doc.labels or [])
    if not target and not existing:
        return False
    if not target and existing:
        target = str(existing[0].name or "").strip()
    if not target:
        return False

    # Ensure label exists and set it as the only label.
    grp = _ensure_tenant_user_group(db, doc.tenant_id)
    if not grp.id:
        db.flush()
    group_id = grp.id
    label = (
        db.query(Label)
        .filter(
            Label.tenant_id == doc.tenant_id,
            Label.group_id == group_id,
            func.lower(func.trim(Label.name)) == target.lower(),
        )
        .first()
    )
    if not label:
        label = Label(tenant_id=doc.tenant_id, name=target.strip(), group_id=group_id)
        db.add(label)
        db.commit()
        db.refresh(label)

    target_label_id = str(label.id)
    try:
        # ORM sometimes doesn't remove association rows reliably for older DBs; do it explicitly.
        db.execute(
            text(
                """
                DELETE FROM document_labels
                WHERE document_id = :doc_id AND label_id != :label_id
                """
            ),
            {"doc_id": str(doc.id), "label_id": target_label_id},
        )
        db.execute(
            text(
                """
                INSERT OR IGNORE INTO document_labels(document_id, label_id)
                VALUES (:doc_id, :label_id)
                """
            ),
            {"doc_id": str(doc.id), "label_id": target_label_id},
        )
        # Ensure the ORM doesn't try to delete already-deleted association rows.
        db.expire(doc, ["labels"])
        return True
    except Exception:
        # Fallback to ORM relationship assignment only (may fail on older DBs).
        if len(existing) != 1 or (existing and str(existing[0].id) != target_label_id):
            doc.labels = [label]
            return True
    return False


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


def _get_or_create_csv_import_account(db: Session, tenant_id: str) -> BankAccount:
    existing = (
        db.query(BankAccount)
        .filter(BankAccount.tenant_id == tenant_id, BankAccount.external_account_id == "csv:import")
        .first()
    )
    if existing:
        return existing
    row = BankAccount(
        tenant_id=tenant_id,
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
        auto_mapping = False
        llm_mapping = False
        manual_mapping = False

        # Expliciete mapping (uit settings) is altijd prioriteit.
        if direct_mapping:
            category = direct_mapping
            source = "mapping"
            auto_mapping = True
        elif category:
            # Niet-expliciet: LLM/inschatting-kanaal.
            source = "llm"
            llm_mapping = True
        else:
            # Fallback blijft in "inschatting" kanaal zodat de rest altijd gecategoriseerd raakt.
            _, category, _ = _fallback_budget_category(tx, mappings)
            source = "llm"
            llm_mapping = True
            if not reason:
                reason = "Fallback op patroonregels (LLM niet beschikbaar of geen expliciete match)."
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
                "auto_mapping": auto_mapping,
                "llm_mapping": llm_mapping,
                "manual_mapping": manual_mapping,
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


def _sync_budget_categories_to_mapping_settings(db: Session, tenant_id: str, analyzed_transactions: list[dict] | None) -> int:
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
        .filter(BankCategoryMapping.tenant_id == tenant_id, BankCategoryMapping.is_active.is_(True))
        .all()
    )
    existing_categories = {str(r.category or "").strip().lower() for r in existing_rows if str(r.category or "").strip()}

    max_priority = (
        db.query(func.max(BankCategoryMapping.priority))
        .filter(BankCategoryMapping.tenant_id == tenant_id)
        .scalar()
        or 0
    )
    created = 0
    for category, flows in discovered.items():
        key = category.lower()
        if key in existing_categories:
            continue
        inferred_flow = "all" if len(flows) > 1 else next(iter(flows))
        max_priority += 1
        db.add(
            BankCategoryMapping(
                tenant_id=tenant_id,
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


def _persist_bank_tx_classification(
    db: Session,
    tenant_id: str,
    analyzed_transactions: list[dict] | None,
) -> int:
    if not analyzed_transactions:
        return 0
    by_external_id: dict[str, dict] = {}
    for row in analyzed_transactions:
        if not isinstance(row, dict):
            continue
        ext_id = str(row.get("external_transaction_id") or "").strip()
        if not ext_id:
            continue
        by_external_id[ext_id] = row
    if not by_external_id:
        return 0

    tx_rows = (
        db.query(BankTransaction)
        .filter(
            BankTransaction.tenant_id == tenant_id,
            BankTransaction.external_transaction_id.in_(list(by_external_id.keys())),
        )
        .all()
    )
    updated = 0
    for tx in tx_rows:
        payload = by_external_id.get(str(tx.external_transaction_id or "").strip())
        if not payload:
            continue
        tx.category = str(payload.get("category") or "").strip() or None
        tx.source = str(payload.get("source") or "").strip() or None
        tx.auto_mapping = bool(payload.get("auto_mapping"))
        tx.llm_mapping = bool(payload.get("llm_mapping"))
        tx.manual_mapping = bool(payload.get("manual_mapping"))
        updated += 1
    if updated:
        db.commit()
    return updated


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


def _document_content_sha256(data: bytes) -> str:
    return hashlib.sha256(data or b"").hexdigest()


def _tx_dedupe_hash_from_payload(payload: dict) -> str:
    key = {
        "booking_date": str(payload.get("booking_date") or "").strip(),
        "value_date": str(payload.get("value_date") or "").strip(),
        "amount": f"{float(payload.get('amount') or 0.0):.2f}",
        "currency": str(payload.get("currency") or "EUR").strip().upper(),
        "counterparty_name": _normalize_text(str(payload.get("counterparty_name") or "")),
        "remittance_information": _normalize_text(str(payload.get("remittance_information") or "")),
    }
    return hashlib.sha256(json.dumps(key, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


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


def _find_existing_bank_tx(
    db: Session,
    *,
    tenant_id: str,
    bank_account_id: str,
    external_transaction_id: str,
    dedupe_hash: str | None,
) -> BankTransaction | None:
    ext = str(external_transaction_id or "").strip()
    if ext:
        row = (
            db.query(BankTransaction)
            .filter(
                BankTransaction.bank_account_id == bank_account_id,
                BankTransaction.tenant_id == tenant_id,
                BankTransaction.external_transaction_id == ext,
            )
            .first()
        )
        if row:
            return row
    if dedupe_hash:
        return (
            db.query(BankTransaction)
            .filter(
                BankTransaction.bank_account_id == bank_account_id,
                BankTransaction.tenant_id == tenant_id,
                BankTransaction.dedupe_hash == dedupe_hash,
            )
            .first()
        )
    return None


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

    tenant_ids = {str(tx.get("tenant_id") or "").strip() for tx in transactions if str(tx.get("tenant_id") or "").strip()}
    docs_q = (
        db.query(Document)
        .filter(
            Document.deleted_at.is_(None),
            Document.paid.is_(True),
            Document.total_amount.is_not(None),
            Document.paid_on.is_not(None),
        )
    )
    if tenant_ids:
        docs_q = docs_q.filter(Document.tenant_id.in_(tenant_ids))
    docs = docs_q.all()
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
    tenant_ids = {str(t.get("tenant_id") or "").strip() for t in out if str(t.get("tenant_id") or "").strip()}
    docs_q = db.query(Document).filter(Document.id.in_(doc_ids))
    if tenant_ids:
        docs_q = docs_q.filter(Document.tenant_id.in_(tenant_ids))
    docs = docs_q.all()
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
    if str(getattr(doc, "tenant_id", "") or "") != _tenant_id_for_user(current_user):
        raise HTTPException(status_code=403, detail="Geen toegang")
    if not allow_deleted and doc.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Document niet gevonden")
    if not _current_user_can_see_all_groups(current_user) and doc.group_id not in user_group_ids(current_user):
        raise HTTPException(status_code=403, detail="Geen toegang")
    return doc


def _current_user_can_see_all_groups(user: User) -> bool:
    if not GROUPS_ENABLED:
        return True
    return user_is_admin(user)


def _purge_expired_deleted_docs(db: Session, tenant_id: str) -> None:
    cutoff = datetime.utcnow() - timedelta(days=7)
    expired_docs = (
        db.query(Document)
        .filter(Document.tenant_id == tenant_id, Document.deleted_at.is_not(None), Document.deleted_at < cutoff)
        .all()
    )
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
    # Guardrails + mark interrupted jobs (init_db ensures async_jobs exists).
    db = SessionLocal()
    try:
        _startup_guardrails_and_cleanup(db)
    finally:
        db.close()
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
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Ongeldige login")
    token = issue_token(db, user)
    try:
        audit_log(
            db,
            tenant_id=str(getattr(user, "tenant_id", "") or ""),
            user_id=str(user.id),
            action="auth.login",
            entity_type="user",
            entity_id=str(user.id),
            details={"email": str(user.email or "")},
            ip=str(getattr(getattr(request, "client", None), "host", "") or "") or None,
            user_agent=str(request.headers.get("user-agent") or "") or None,
        )
        db.commit()
    except Exception:
        db.rollback()
    return {"token": token, "user": user_to_out(user, tenant_name=_tenant_name_for_id(db, user.tenant_id))}


@app.post("/api/auth/logout")
def logout_api(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    current_user: User = Depends(get_current_user_dep),
):
    session_row = _current_session_token(db, authorization)
    if session_row and str(session_row.user_id or "") == str(current_user.id or ""):
        db.delete(session_row)
        try:
            audit_log(
                db,
                tenant_id=_tenant_id_for_user(current_user),
                user_id=str(current_user.id),
                action="auth.logout",
                entity_type="user",
                entity_id=str(current_user.id),
                details={},
                ip=str(getattr(getattr(request, "client", None), "host", "") or "") or None,
                user_agent=str(request.headers.get("user-agent") or "") or None,
            )
        except Exception:
            pass
        db.commit()
    return {"ok": True}


@app.post("/api/auth/signup", response_model=AuthOut)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    name = (payload.name or "").strip()
    email = (payload.email or "").strip().lower()
    password = str(payload.password or "")
    if not name:
        raise HTTPException(status_code=400, detail="Naam is verplicht")
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Email formaat is ongeldig")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Wachtwoord moet minstens 8 karakters zijn")
    if db.query(User).filter(func.lower(User.email) == email.lower()).first():
        raise HTTPException(status_code=400, detail="Email bestaat al")

    tenant = Tenant(name=name, slug=_ensure_unique_tenant_slug(db, name))
    db.add(tenant)
    db.flush()
    _ensure_tenant_admin_group(db, tenant.id)
    _ensure_tenant_user_group(db, tenant.id)

    user = User(
        tenant_id=tenant.id,
        email=email,
        name=name,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()
    user.created_by_user_id = user.id
    _apply_user_role(db, user, tenant.id, ROLE_ADMIN, user)
    db.commit()
    db.refresh(user)

    token = issue_token(db, user)
    return {"token": token, "user": user_to_out(user, tenant_name=_tenant_name_for_id(db, user.tenant_id))}


@app.post("/api/auth/forgot-password")
def forgot_password(payload: ForgotPasswordIn, request: Request, db: Session = Depends(get_db)):
    email = str(payload.email or "").strip().lower()
    # No user enumeration: always return generic success.
    generic_ok = {"ok": True, "message": "Als de gebruiker bestaat, is een resetlink verstuurd."}
    if not email:
        return generic_ok

    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        return generic_ok

    now = datetime.utcnow()
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": now}, synchronize_session=False)

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    reset_row = PasswordResetToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + timedelta(hours=1),
    )
    db.add(reset_row)
    db.commit()

    base_url = str(settings.public_base_url or "").strip().rstrip("/") or str(request.base_url).rstrip("/")
    reset_link = f"{base_url}/#reset-password?token={quote(raw_token)}&email={quote(user.email)}"
    runtime = get_runtime_settings(db, tenant_id=str(user.tenant_id or ""))
    try:
        _send_smtp_email(
            runtime,
            user.email,
            "Docstore password reset",
            (
                "Je vroeg een wachtwoord-reset aan voor Docstore.\n\n"
                f"Reset je wachtwoord via deze link:\n{reset_link}\n\n"
                "Deze link is 1 uur geldig. Heb je dit niet aangevraagd? Dan mag je deze mail negeren."
            ),
        )
    except Exception as ex:
        print(f"[AUTH] forgot-password mail error for {user.email}: {ex}")
    return generic_ok


@app.post("/api/auth/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    email = str(payload.email or "").strip().lower()
    raw_token = str(payload.token or "").strip()
    password = str(payload.password or "")
    confirm = str(payload.confirm_password or "")
    if not email or not raw_token:
        raise HTTPException(status_code=400, detail="Reset link is ongeldig")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Wachtwoord moet minstens 8 karakters zijn")
    if password != confirm:
        raise HTTPException(status_code=400, detail="Wachtwoorden komen niet overeen")

    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Reset link is ongeldig of verlopen")

    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = datetime.utcnow()
    row = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .order_by(PasswordResetToken.created_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=400, detail="Reset link is ongeldig of verlopen")

    user.password_hash = hash_password(password)
    row.used_at = now
    db.query(SessionToken).filter(SessionToken.user_id == user.id).delete()
    db.commit()
    return {"ok": True}


@app.get("/api/auth/me", response_model=UserOut)
def me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    return user_to_out(current_user, tenant_name=_tenant_name_for_id(db, _tenant_id_for_user(current_user)))


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

    conflict = db.query(User).filter(
        User.tenant_id == str(getattr(current_user, "tenant_id", "") or ""),
        User.email == email,
        User.id != current_user.id,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Email bestaat al")

    current_user.name = name
    current_user.email = email
    if payload.password is not None and payload.password.strip():
        current_user.password_hash = hash_password(payload.password.strip())

    db.commit()
    db.refresh(current_user)
    return user_to_out(current_user, tenant_name=_tenant_name_for_id(db, _tenant_id_for_user(current_user)))


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

    return user_to_out(current_user, tenant_name=_tenant_name_for_id(db, _tenant_id_for_user(current_user)))


@app.post("/api/auth/switch-tenant", response_model=UserOut)
def switch_tenant(
    payload: SwitchTenantIn,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    current_user: User = Depends(get_current_user_dep),
):
    require_bootstrap_admin(current_user)
    tenant_id = str(payload.tenant_id or "").strip()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is verplicht")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant niet gevonden")
    session_row = _current_session_token(db, authorization)
    if str(session_row.user_id or "") != str(current_user.id or ""):
        raise HTTPException(status_code=401, detail="Ongeldige sessie")
    session_row.tenant_id = tenant.id
    db.commit()
    current_user.active_tenant_id = tenant.id
    return user_to_out(current_user, tenant_name=str(getattr(tenant, "name", "") or ""))


@app.get("/api/admin/tenants", response_model=list[TenantOut])
def list_tenants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    active_tenant_id = _tenant_id_for_user(current_user)
    if current_user.is_bootstrap_admin:
        rows = db.query(Tenant).order_by(Tenant.created_at.asc()).all()
    elif user_is_admin(current_user):
        rows = db.query(Tenant).filter(Tenant.id == active_tenant_id).order_by(Tenant.created_at.asc()).all()
    else:
        raise HTTPException(status_code=403, detail="Alleen administrators hebben toegang")
    out = []
    for row in rows:
        tid = str(row.id)
        stats = _tenant_stats(db, tid)
        out.append(
            {
                "id": tid,
                "name": row.name,
                "slug": row.slug,
                "is_active": tid == active_tenant_id,
                **stats,
            }
        )
    return out


@app.post("/api/admin/tenants", response_model=TenantOut)
def create_tenant(
    payload: CreateTenantIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_bootstrap_admin(current_user)

    name = str(payload.name or "").strip()
    slug = _slugify_tenant(str(payload.slug or name))

    if not name:
        raise HTTPException(status_code=400, detail="Tenant naam is verplicht")

    exists_slug = db.query(Tenant).filter(func.lower(Tenant.slug) == slug.lower()).first()
    if exists_slug:
        raise HTTPException(status_code=400, detail="Tenant slug bestaat al")

    tenant = Tenant(name=name, slug=slug)
    db.add(tenant)
    db.flush()

    _ensure_tenant_admin_group(db, tenant.id)
    _ensure_tenant_user_group(db, tenant.id)
    db.commit()

    stats = _tenant_stats(db, str(tenant.id))
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "is_active": False,
        **stats,
    }


@app.put("/api/admin/tenants/{tenant_id}", response_model=TenantOut)
def update_tenant(
    tenant_id: str,
    payload: UpdateTenantIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_bootstrap_admin(current_user)
    tenant = _tenant_for_id(db, tenant_id)
    name = str(payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Tenant naam is verplicht")
    tenant.name = name
    db.commit()
    db.refresh(tenant)
    active_tenant_id = _tenant_id_for_user(current_user)
    tid = str(tenant.id)
    stats = _tenant_stats(db, tid)
    return {
        "id": tid,
        "name": tenant.name,
        "slug": tenant.slug,
        "is_active": tid == active_tenant_id,
        **stats,
    }


@app.get("/api/admin/tenant-users")
def list_tenant_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    if not user_is_admin(current_user):
        raise HTTPException(status_code=403, detail="Alleen administrators hebben toegang")
    active_tenant_id = _tenant_id_for_user(current_user)
    tenants = {str(t.id): t for t in db.query(Tenant).all()}
    q = db.query(User)
    if current_user.is_bootstrap_admin:
        rows = q.order_by(User.name.asc(), User.email.asc()).all()
    else:
        rows = (
            q.filter(User.tenant_id == active_tenant_id)
            .filter((User.created_by_user_id == current_user.id) | (User.id == current_user.id))
            .order_by(User.name.asc(), User.email.asc())
            .all()
        )
    out = []
    for row in rows:
        tid = str(row.tenant_id or "")
        tenant = tenants.get(tid)
        out.append(
            {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "tenant_id": tid,
                "tenant_name": tenant.name if tenant else "",
                "is_bootstrap_admin": bool(row.is_bootstrap_admin),
            }
        )
    return out


@app.get("/api/admin/tenants/{tenant_id}/users")
def list_users_for_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    if not user_is_admin(current_user):
        raise HTTPException(status_code=403, detail="Alleen administrators hebben toegang")
    tenant = _tenant_for_id(db, tenant_id)
    if not current_user.is_bootstrap_admin and str(tenant.id) != _tenant_id_for_user(current_user):
        raise HTTPException(status_code=403, detail="Admin heeft enkel toegang tot eigen tenant")
    q = db.query(User).filter(User.tenant_id == tenant.id)
    if current_user.is_bootstrap_admin:
        rows = q.order_by(User.name.asc(), User.email.asc()).all()
    else:
        rows = (
            q.filter((User.created_by_user_id == current_user.id) | (User.id == current_user.id))
            .order_by(User.name.asc(), User.email.asc())
            .all()
        )
    return [
        {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "tenant_id": str(row.tenant_id or ""),
            "tenant_name": tenant.name,
            "is_bootstrap_admin": bool(row.is_bootstrap_admin),
        }
        for row in rows
    ]


@app.post("/api/admin/tenants/{tenant_id}/users/{user_id}")
def add_user_to_tenant(
    tenant_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    if not user_is_admin(current_user):
        raise HTTPException(status_code=403, detail="Alleen administrators hebben toegang")
    tenant = _tenant_for_id(db, tenant_id)
    if not current_user.is_bootstrap_admin and str(tenant.id) != _tenant_id_for_user(current_user):
        raise HTTPException(status_code=403, detail="Admin heeft enkel toegang tot eigen tenant")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    if user.is_bootstrap_admin:
        raise HTTPException(status_code=400, detail="Bootstrap admin kan niet verplaatst worden")
    if not current_user.is_bootstrap_admin and str(user.created_by_user_id or "") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Admin kan enkel eigen aangemaakte gebruikers toevoegen")
    changing_tenant = str(user.tenant_id or "") != str(tenant.id)
    user.tenant_id = tenant.id
    if changing_tenant:
        user.groups = [_ensure_tenant_user_group(db, tenant.id)]
    db.commit()
    return {"ok": True}


@app.delete("/api/admin/tenants/{tenant_id}/users/{user_id}")
def remove_user_from_tenant(
    tenant_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    if not user_is_admin(current_user):
        raise HTTPException(status_code=403, detail="Alleen administrators hebben toegang")
    tenant = _tenant_for_id(db, tenant_id)
    if not current_user.is_bootstrap_admin and str(tenant.id) != _tenant_id_for_user(current_user):
        raise HTTPException(status_code=403, detail="Admin heeft enkel toegang tot eigen tenant")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    if user.is_bootstrap_admin:
        raise HTTPException(status_code=400, detail="Bootstrap admin kan niet verplaatst worden")
    if not current_user.is_bootstrap_admin and str(user.created_by_user_id or "") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Admin kan enkel eigen aangemaakte gebruikers aanpassen")
    if str(user.tenant_id or "") != str(tenant.id):
        return {"ok": True}
    default_tenant_id = get_default_tenant_id()
    if str(tenant.id) == str(default_tenant_id):
        raise HTTPException(status_code=400, detail="Gebruiker kan niet uit de default tenant verwijderd worden")
    changing_tenant = str(user.tenant_id or "") != str(default_tenant_id)
    user.tenant_id = default_tenant_id
    if changing_tenant:
        user.groups = [_ensure_tenant_user_group(db, default_tenant_id)]
    db.commit()
    return {"ok": True}


@app.get("/api/meta/providers")
def providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
) -> dict:
    runtime = get_runtime_settings(db, tenant_id=_tenant_id_for_user(current_user))
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
    tenant_id = _tenant_id_for_user(current_user)
    if _current_user_can_see_all_groups(current_user):
        all_groups = db.query(Group).filter(Group.tenant_id == tenant_id).order_by(Group.name.asc()).all()
        return [group_to_out(g) for g in all_groups]
    return [group_to_out(g) for g in current_user.groups if str(g.tenant_id or "") == tenant_id]


@app.get("/api/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    tenant_id = _tenant_id_for_user(current_user)
    if _current_user_can_see_all_groups(current_user):
        return _get_category_profiles(db, tenant_id, None)
    return _get_category_profiles(db, tenant_id, user_group_ids(current_user))


@app.post("/api/categories", response_model=CategoryOut)
def create_category(
    payload: CreateCategoryIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    _ = current_user
    tenant_id = _tenant_id_for_user(current_user)
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Categorie is verplicht")

    existing = db.query(CategoryCatalog).filter(CategoryCatalog.tenant_id == tenant_id, func.lower(CategoryCatalog.name) == name.lower()).first()
    if existing:
        return _category_to_out(existing, existing.name)

    default = _default_category_profile(name)
    row = CategoryCatalog(
        tenant_id=tenant_id,
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
    tenant_id = _tenant_id_for_user(current_user)
    old_name = (category_name or "").strip()
    new_name = (payload.name or "").strip()
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail="Categorie naam is verplicht")

    row = db.query(CategoryCatalog).filter(CategoryCatalog.tenant_id == tenant_id, func.lower(CategoryCatalog.name) == old_name.lower()).first()
    if not row:
        row = CategoryCatalog(tenant_id=tenant_id, name=old_name)
        db.add(row)
        db.flush()

    conflict = db.query(CategoryCatalog).filter(
        CategoryCatalog.tenant_id == tenant_id,
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

    docs = db.query(Document).filter(Document.tenant_id == tenant_id, func.lower(Document.category) == old_doc_name.lower()).all()
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
    tenant_id = _tenant_id_for_user(current_user)
    name = (category_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Categorie is verplicht")

    linked_docs = db.query(Document.id).filter(
        Document.tenant_id == tenant_id,
        func.lower(Document.category) == name.lower(),
        Document.deleted_at.is_(None),
    ).first()
    if linked_docs:
        raise HTTPException(
            status_code=409,
            detail="Categorie kan niet verwijderd worden: er hangen nog documenten aan.",
        )

    row = db.query(CategoryCatalog).filter(CategoryCatalog.tenant_id == tenant_id, func.lower(CategoryCatalog.name) == name.lower()).first()
    if not row:
        raise HTTPException(status_code=404, detail="Categorie niet gevonden in catalogus")

    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/labels", response_model=list[LabelOut])
def list_labels(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    tenant_id = _tenant_id_for_user(current_user)
    # Keep bank categories available as labels, so documents can be tagged consistently.
    try:
        _ensure_bank_category_labels(db, tenant_id)
    except Exception:
        db.rollback()
    if not GROUPS_ENABLED or _current_user_can_see_all_groups(current_user):
        labels = db.query(Label).filter(Label.tenant_id == tenant_id).order_by(Label.name.asc()).all()
        return [{"id": l.id, "name": l.name, "group_id": l.group_id} for l in labels]
    group_ids = user_group_ids(current_user)
    if not group_ids:
        return []
    labels = db.query(Label).filter(Label.tenant_id == tenant_id, Label.group_id.in_(group_ids)).order_by(Label.name.asc()).all()
    return [{"id": l.id, "name": l.name, "group_id": l.group_id} for l in labels]


@app.post("/api/labels", response_model=LabelOut)
def create_label(
    payload: CreateLabelIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    if payload.group_id and (not _current_user_can_see_all_groups(current_user)) and payload.group_id not in user_group_ids(current_user):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze groep")
    group_id = str(payload.group_id or "").strip()
    if not group_id:
        grp = _ensure_tenant_user_group(db, tenant_id)
        if not grp.id:
            db.flush()
        group_id = grp.id

    name = str(payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Label naam is verplicht")

    existing = db.query(Label).filter(
        Label.tenant_id == tenant_id,
        func.lower(func.trim(Label.name)) == name.lower(),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Label bestaat al")

    label = Label(tenant_id=tenant_id, name=name, group_id=group_id)
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
        chosen_ids = [str(x) for x in payload.label_ids if str(x).strip()][:1]
        if chosen_ids:
            labels = db.query(Label).filter(Label.id.in_(chosen_ids), Label.tenant_id == doc.tenant_id).all()

    if labels:
        doc.labels = labels
        chosen = str(labels[0].name or "").strip()
        if chosen:
            doc.budget_category = chosen
            doc.budget_category_source = "manual"
        _ensure_doc_single_label(db, doc)
    else:
        db.execute(text("DELETE FROM document_labels WHERE document_id = :doc_id"), {"doc_id": str(doc.id)})
        doc.labels = []
        doc.budget_category = None
        doc.budget_category_source = None
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
    tenant_id = _tenant_id_for_user(current_user)
    tenant_name = _tenant_name_for_id(db, tenant_id)
    users = db.query(User).filter(User.tenant_id == tenant_id).order_by(User.created_at.asc()).all()
    return [user_to_out(u, tenant_name=tenant_name) for u in users]


@app.post("/api/admin/users", response_model=UserOut)
def create_user(
    payload: CreateUserIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    from app.services.auth import hash_password

    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)
    email = str(payload.email or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email/login is verplicht")

    existing = db.query(User).filter(User.tenant_id == tenant_id, func.lower(User.email) == email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email bestaat al")

    user = User(
        tenant_id=tenant_id,
        email=email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        created_by_user_id=current_user.id,
    )
    role = str(payload.role or ROLE_USER).strip().lower()
    if role == ROLE_SUPERADMIN and not current_user.is_bootstrap_admin:
        raise HTTPException(status_code=403, detail="Admin kan geen superadmin aanmaken")
    _apply_user_role(db, user, tenant_id, role, current_user)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_out(user, tenant_name=_tenant_name_for_id(db, tenant_id))


@app.put("/api/admin/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UpdateUserIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    from app.services.auth import hash_password

    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)

    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    email = (payload.email or "").strip()
    name = (payload.name or "").strip()
    if not email or not name:
        raise HTTPException(status_code=400, detail="Naam en email/login zijn verplicht")

    conflict = db.query(User).filter(User.tenant_id == tenant_id, User.email == email, User.id != user.id).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Email bestaat al")

    user.email = email
    user.name = name
    if payload.password is not None and payload.password.strip():
        user.password_hash = hash_password(payload.password.strip())

    role = str(payload.role or user_role(user)).strip().lower()
    if role == ROLE_SUPERADMIN and not current_user.is_bootstrap_admin:
        raise HTTPException(status_code=403, detail="Admin kan geen superadmin toekennen")
    if user.is_bootstrap_admin and role != ROLE_SUPERADMIN and not current_user.is_bootstrap_admin:
        raise HTTPException(status_code=403, detail="Admin kan geen superadmin aanpassen")
    _apply_user_role(db, user, tenant_id, role, current_user)

    db.commit()
    db.refresh(user)
    return user_to_out(user, tenant_name=_tenant_name_for_id(db, tenant_id))


@app.delete("/api/admin/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)

    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Je kan je eigen account niet verwijderen")
    if user.is_bootstrap_admin:
        raise HTTPException(status_code=400, detail="Bootstrap admin kan niet verwijderd worden")

    user.groups = []
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM session_tokens WHERE user_id = :uid AND tenant_id = :tid"), {"uid": user.id, "tid": tenant_id})
        conn.execute(text("DELETE FROM user_groups WHERE user_id = :uid"), {"uid": user.id})

    db.delete(user)
    db.commit()
    return {"ok": True}


@app.get("/api/admin/groups", response_model=list[GroupOut])
def list_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)
    groups = db.query(Group).filter(Group.tenant_id == tenant_id).order_by(Group.name.asc()).all()
    return [group_to_out(g) for g in groups]


@app.post("/api/admin/groups", response_model=GroupOut)
def create_group(
    payload: CreateGroupIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)

    existing = db.query(Group).filter(Group.tenant_id == tenant_id, Group.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Groepsnaam bestaat al")

    group = Group(tenant_id=tenant_id, name=payload.name)
    if payload.user_ids:
        users = db.query(User).filter(User.tenant_id == tenant_id, User.id.in_(payload.user_ids)).all()
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
    tenant_id = _tenant_id_for_user(current_user)

    group = db.query(Group).filter(Group.id == group_id, Group.tenant_id == tenant_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Groep niet gevonden")
    if (group.name or "").strip().lower().startswith("administrators"):
        raise HTTPException(status_code=400, detail="Administrators groep kan niet verwijderd worden")
    if group.users:
        raise HTTPException(status_code=400, detail="Groep kan niet verwijderd worden: er zijn nog gebruikers gekoppeld")

    db.delete(group)
    db.commit()
    return {"ok": True}


@app.get("/api/admin/integrations", response_model=IntegrationSettingsOut)
def get_integrations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_dep)):
    require_admin_access(current_user)
    return settings_to_out(db, tenant_id=_tenant_id_for_user(current_user))


@app.put("/api/admin/integrations", response_model=IntegrationSettingsOut)
def update_integrations(
    payload: UpdateIntegrationSettingsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)
    out = update_settings(
        db,
        tenant_id=tenant_id,
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
        smtp_server=payload.smtp_server,
        smtp_port=payload.smtp_port,
        smtp_username=payload.smtp_username,
        smtp_password=payload.smtp_password,
        smtp_sender_email=payload.smtp_sender_email,
        bank_csv_prompt=payload.bank_csv_prompt,
        bank_csv_mappings=payload.bank_csv_mappings,
        default_ocr_provider=payload.default_ocr_provider,
    )
    try:
        fields_set = getattr(payload, "model_fields_set", getattr(payload, "__fields_set__", set()))
        touched = sorted([str(x) for x in fields_set if x])
        audit_log(
            db,
            tenant_id=tenant_id,
            user_id=str(current_user.id),
            action="settings.integrations.update",
            entity_type="integration_settings",
            entity_id=str(tenant_id),
            details={"touched_fields": touched},
        )
        db.commit()
    except Exception:
        db.rollback()
    return out


@app.post("/api/admin/mail-ingest/run")
def run_mail_ingest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    runtime = get_runtime_settings(db, tenant_id=_tenant_id_for_user(current_user))
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
    tenant_id = _tenant_id_for_user(current_user)
    rows = db.query(BankAccount).filter(BankAccount.tenant_id == tenant_id).order_by(BankAccount.created_at.desc()).all()
    return [bank_account_to_out(r) for r in rows]


@app.post("/api/bank/accounts", response_model=BankAccountOut)
def create_bank_account(
    payload: CreateBankAccountIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)
    name = (payload.name or "").strip()
    provider = _normalize_bank_provider(payload.provider)
    raw_external = (payload.external_account_id or "").strip()
    if not name or not raw_external:
        raise HTTPException(status_code=400, detail="Naam en external account id zijn verplicht")
    external = _compose_external_account_id(provider, raw_external)

    existing = db.query(BankAccount).filter(BankAccount.tenant_id == tenant_id, BankAccount.external_account_id == external).first()
    if existing:
        return bank_account_to_out(existing)

    row = BankAccount(
        tenant_id=tenant_id,
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
    tenant_id = _tenant_id_for_user(current_user)
    row = db.query(BankAccount).filter(BankAccount.id == account_id, BankAccount.tenant_id == tenant_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Rekening niet gevonden")
    db.query(BankTransaction).filter(BankTransaction.tenant_id == tenant_id, BankTransaction.bank_account_id == row.id).delete()
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.post("/api/bank/sync-accounts", response_model=list[BankAccountOut])
def sync_bank_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)
    runtime = get_runtime_settings(db, tenant_id=tenant_id)
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
        row = db.query(BankAccount).filter(BankAccount.tenant_id == tenant_id, BankAccount.external_account_id == external).first()
        if row:
            row.name = str(r.get("name") or row.name).strip() or row.name
            row.provider = _normalize_bank_provider(r.get("provider") or row.provider)
            row.iban = str(r.get("iban") or row.iban or "").strip() or row.iban
            row.is_active = True
        else:
            db.add(
                BankAccount(
                    tenant_id=tenant_id,
                    name=str(r.get("name") or external).strip() or external,
                    provider=_normalize_bank_provider(r.get("provider")),
                    iban=str(r.get("iban") or "").strip() or None,
                    external_account_id=external,
                    is_active=True,
                )
            )
    db.commit()
    rows = db.query(BankAccount).filter(BankAccount.tenant_id == tenant_id).order_by(BankAccount.created_at.desc()).all()
    return [bank_account_to_out(r) for r in rows]


@app.get("/api/bank/accounts/{account_id}/transactions", response_model=list[BankTransactionOut])
def list_bank_transactions(
    account_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)
    account = db.query(BankAccount).filter(BankAccount.id == account_id, BankAccount.tenant_id == tenant_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Rekening niet gevonden")
    rows = (
        db.query(BankTransaction)
        .filter(BankTransaction.tenant_id == tenant_id, BankTransaction.bank_account_id == account.id)
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
    tenant_id = _tenant_id_for_user(current_user)
    account = db.query(BankAccount).filter(BankAccount.id == account_id, BankAccount.tenant_id == tenant_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Rekening niet gevonden")

    runtime = get_runtime_settings(db, tenant_id=tenant_id)
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
        dedupe_hash = _tx_dedupe_hash_from_payload(t)
        if not ext_id and not dedupe_hash:
            continue
        row = _find_existing_bank_tx(
            db,
            tenant_id=tenant_id,
            bank_account_id=account.id,
            external_transaction_id=ext_id,
            dedupe_hash=dedupe_hash,
        )
        if row:
            row.external_transaction_id = ext_id or row.external_transaction_id
            row.booking_date = t.get("booking_date")
            row.value_date = t.get("value_date")
            row.amount = t.get("amount")
            row.currency = t.get("currency")
            row.counterparty_name = t.get("counterparty_name")
            row.remittance_information = t.get("remittance_information")
            row.raw_json = t.get("raw_json")
            row.dedupe_hash = dedupe_hash
        else:
            db.add(
                BankTransaction(
                    tenant_id=tenant_id,
                    bank_account_id=account.id,
                    external_transaction_id=ext_id or f"dedupe_{dedupe_hash[:16]}",
                    dedupe_hash=dedupe_hash,
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
        .filter(BankTransaction.tenant_id == tenant_id, BankTransaction.bank_account_id == account.id)
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
    tenant_id = _tenant_id_for_user(current_user)
    account = db.query(BankAccount).filter(BankAccount.id == account_id, BankAccount.tenant_id == tenant_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Rekening niet gevonden")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Bestand is leeg")

    _, txs = parse_imported_transactions(file.filename or "", content)
    imported = 0
    for t in txs:
        ext_id = str(t.get("external_transaction_id") or "").strip()
        dedupe_hash = _tx_dedupe_hash_from_payload(t)
        if not ext_id and not dedupe_hash:
            continue
        row = _find_existing_bank_tx(
            db,
            tenant_id=tenant_id,
            bank_account_id=account.id,
            external_transaction_id=ext_id,
            dedupe_hash=dedupe_hash,
        )
        if row:
            row.external_transaction_id = ext_id or row.external_transaction_id
            row.booking_date = t.get("booking_date")
            row.value_date = t.get("value_date")
            row.amount = t.get("amount")
            row.currency = t.get("currency")
            row.counterparty_name = t.get("counterparty_name")
            row.remittance_information = t.get("remittance_information")
            row.raw_json = t.get("raw_json")
            row.dedupe_hash = dedupe_hash
            imported += 1
        else:
            db.add(
                BankTransaction(
                    tenant_id=tenant_id,
                    bank_account_id=account.id,
                    external_transaction_id=ext_id or f"dedupe_{dedupe_hash[:16]}",
                    dedupe_hash=dedupe_hash,
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
    tenant_id = _tenant_id_for_user(current_user)
    filename = (file.filename or "").strip().lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Enkel .csv bestanden zijn toegestaan")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Bestand is leeg")

    file_sha256 = hashlib.sha256(content).hexdigest()
    account = _get_or_create_csv_import_account(db, tenant_id)
    _, txs = parse_imported_transactions(file.filename or "", content)

    # If the exact same file was already imported, ignore this upload completely.
    existing_file = (
        db.query(BankCsvImport)
        .filter(BankCsvImport.tenant_id == tenant_id, BankCsvImport.file_sha256 == file_sha256)
        .order_by(BankCsvImport.created_at.desc())
        .first()
    )
    if existing_file:
        try:
            audit_log(
                db,
                tenant_id=tenant_id,
                user_id=str(current_user.id),
                action="bank.csv.duplicate_file",
                entity_type="bank_csv_import",
                entity_id=str(existing_file.id),
                details={"filename": str(existing_file.filename or ""), "file_sha256": file_sha256},
            )
            db.commit()
        except Exception:
            db.rollback()
        return {"imported": 0, "duplicate_file": True, "existing_filename": str(existing_file.filename or "")}

    # First pass: determine which transactions are new (no duplicates).
    new_payloads: list[dict] = []
    for t in txs:
        ext_id = str(t.get("external_transaction_id") or "").strip()
        dedupe_hash = _tx_dedupe_hash_from_payload(t)
        if not ext_id and not dedupe_hash:
            continue
        row = _find_existing_bank_tx(
            db,
            tenant_id=tenant_id,
            bank_account_id=account.id,
            external_transaction_id=ext_id,
            dedupe_hash=dedupe_hash,
        )
        if row:
            continue
        new_payloads.append(t)

    if not new_payloads:
        try:
            audit_log(
                db,
                tenant_id=tenant_id,
                user_id=str(current_user.id),
                action="bank.csv.no_new_transactions",
                entity_type="bank_csv_import",
                entity_id="",
                details={"filename": str(file.filename or ""), "file_sha256": file_sha256},
            )
            db.commit()
        except Exception:
            db.rollback()
        return {"imported": 0, "no_new_transactions": True}

    import_row = BankCsvImport(
        tenant_id=tenant_id,
        filename=file.filename or "import.csv",
        imported_count=0,
        file_sha256=file_sha256,
    )
    db.add(import_row)
    db.commit()
    db.refresh(import_row)

    imported = 0
    for t in new_payloads:
        ext_id = str(t.get("external_transaction_id") or "").strip()
        dedupe_hash = _tx_dedupe_hash_from_payload(t)
        if not ext_id and not dedupe_hash:
            continue
        db.add(
            BankTransaction(
                tenant_id=tenant_id,
                bank_account_id=account.id,
                csv_import_id=import_row.id,
                external_transaction_id=ext_id or f"dedupe_{dedupe_hash[:16]}",
                dedupe_hash=dedupe_hash,
                booking_date=t.get("booking_date"),
                value_date=t.get("value_date"),
                amount=t.get("amount"),
                currency=t.get("currency"),
                counterparty_name=t.get("counterparty_name"),
                remittance_information=t.get("remittance_information"),
                category=None,
                source=None,
                auto_mapping=False,
                llm_mapping=False,
                manual_mapping=False,
                raw_json=t.get("raw_json"),
            )
        )
        imported += 1

    import_row.imported_count = imported
    import_row.parsed_at = datetime.utcnow()
    import_row.parsed_source_hash = "csv-import"
    db.commit()
    try:
        audit_log(
            db,
            tenant_id=tenant_id,
            user_id=str(current_user.id),
            action="bank.csv.upload",
            entity_type="bank_csv_import",
            entity_id=str(import_row.id),
            details={"filename": str(import_row.filename or ""), "imported": imported, "file_sha256": file_sha256},
        )
        db.commit()
    except Exception:
        db.rollback()
    return {"imported": imported}


@app.get("/api/bank/import-csv/transactions", response_model=list[BankTransactionOut])
def list_bank_csv_transactions(
    limit: int = Query(default=200, ge=1, le=20000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    # Import CSV view is admin-only; normal users should use Bank/Budget.
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)
    account = _get_or_create_csv_import_account(db, tenant_id)
    rows = (
        db.query(BankTransaction)
        .filter(BankTransaction.tenant_id == tenant_id, BankTransaction.bank_account_id == account.id)
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
    tenant_id = _tenant_id_for_user(current_user)
    progress_user_id = str(current_user.id)
    account = _get_or_create_csv_import_account(db, tenant_id)
    rows = (
        db.query(BankTransaction)
        .filter(BankTransaction.tenant_id == tenant_id, BankTransaction.bank_account_id == account.id)
        .order_by(BankTransaction.booking_date.asc(), BankTransaction.created_at.asc())
        .all()
    )
    tx_payload = [bank_transaction_to_out(r) for r in rows]
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

    out_settings = settings_to_out(db, tenant_id=tenant_id)
    runtime = get_runtime_settings(db, tenant_id=tenant_id)
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
    cached = db.query(BankBudgetAnalysisRun).filter(BankBudgetAnalysisRun.tenant_id == tenant_id, BankBudgetAnalysisRun.source_hash == source_hash).first()
    if cached:
        if csv_import_ids:
            db.query(BankCsvImport).filter(BankCsvImport.tenant_id == tenant_id, BankCsvImport.id.in_(csv_import_ids)).update(
                {
                    BankCsvImport.parsed_at: datetime.utcnow(),
                    BankCsvImport.parsed_source_hash: source_hash,
                },
                synchronize_session=False,
            )
            db.commit()
        cached_rows = (
            db.query(BankBudgetAnalysisTx)
            .filter(BankBudgetAnalysisTx.tenant_id == tenant_id, BankBudgetAnalysisTx.run_id == cached.id)
            .order_by(BankBudgetAnalysisTx.booking_date.asc(), BankBudgetAnalysisTx.created_at.asc())
            .all()
        )
        if tx_payload and not cached_rows:
            # Corrupt/incomplete cache run: ignore and recompute.
            cached = None
        if cached is None:
            cached_summary = []
        else:
            try:
                loaded = json.loads(cached.summary_json or "[]")
                if isinstance(loaded, list):
                    cached_summary = loaded
            except Exception:
                cached_summary = []
            cached_failed = any("fallback actief" in str(p or "").lower() for p in cached_summary)
            if not cached_failed:
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
                                "source": r.source,
                            }
                            for r in cached_rows
                        ],
                    },
                    mappings if isinstance(mappings, list) else [],
                    preferred_categories=preferred_categories,
                )
                merged["transactions"] = _enrich_budget_transactions_with_doc_links(db, merged.get("transactions") or [])
                _persist_bank_tx_classification(db, tenant_id, merged.get("transactions") or [])
                _sync_budget_categories_to_mapping_settings(db, tenant_id, merged.get("transactions"))
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
    llm_failed = False
    unresolved_payload: list[dict] = []
    for tx in tx_payload:
        flow = "income" if float(tx.get("amount") or 0) >= 0 else "expense"
        if _mapping_category_for_tx(tx, mappings if isinstance(mappings, list) else [], flow):
            continue
        unresolved_payload.append(tx)
    try:
        if unresolved_payload:
            llm_data = analyze_budget_transactions_with_llm(
                transactions=unresolved_payload,
                prompt_template=prompt,
                mappings=mappings if isinstance(mappings, list) else [],
                runtime=runtime,
                known_categories=preferred_categories,
                progress_callback=lambda processed, total: _set_budget_progress(
                    progress_user_id,
                    running=True,
                    processed=min(processed + (len(tx_payload) - len(unresolved_payload)), len(tx_payload)),
                    total=len(tx_payload),
                    done=False,
                ),
            )
        else:
            llm_data = {"summary_points": ["Alle transacties vielen onder expliciete mappings."], "transaction_categories": []}
    except Exception as ex:
        llm_failed = True
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
    _persist_bank_tx_classification(db, tenant_id, merged.get("transactions") or [])
    _sync_budget_categories_to_mapping_settings(db, tenant_id, merged.get("transactions"))
    run = BankBudgetAnalysisRun(
        tenant_id=tenant_id,
        source_hash=source_hash,
        provider=provider,
        model=model,
        prompt_hash=prompt_hash,
        mappings_hash=mappings_hash,
        transactions_hash=tx_hash,
        tx_count=len(tx_payload),
        summary_json=json.dumps(merged.get("summary_points") or [], ensure_ascii=False),
    )
    if not llm_failed:
        db.add(run)
        db.commit()
        db.refresh(run)
        for item in merged.get("transactions") or []:
            db.add(
                BankBudgetAnalysisTx(
                    tenant_id=tenant_id,
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
            db.query(BankCsvImport).filter(BankCsvImport.tenant_id == tenant_id, BankCsvImport.id.in_(csv_import_ids)).update(
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
        "generated_at": (run.updated_at or run.created_at) if not llm_failed else datetime.utcnow(),
        "prompt_used": bool(prompt),
        "mappings_count": len(mappings) if isinstance(mappings, list) else 0,
        "summary_points": merged.get("summary_points") or [],
        "transactions": merged.get("transactions") or [],
        "category_totals": merged.get("category_totals") or [],
        "year_totals": merged.get("year_totals") or [],
        "month_totals": merged.get("month_totals") or [],
    }


@app.post("/api/bank/budget/analyze/start")
def start_analyze_bank_budget(
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    db = SessionLocal()
    try:
        running = _find_running_async_job_db(db, tenant_id=tenant_id, job_type="budget-analyze")
    finally:
        db.close()
    if running:
        return {"job_id": running["id"], "status": running.get("status"), "reused": True}

    db = SessionLocal()
    try:
        job_id = _create_async_job_db(db, job_type="budget-analyze", tenant_id=tenant_id, user_id=str(current_user.id))
    finally:
        db.close()

    def _worker(progress_cb):
        db = SessionLocal()
        try:
            # Progress for budget analyze already exists per user; copy to async job too.
            user = db.get(User, current_user.id)
            if not user:
                raise RuntimeError("Gebruiker niet gevonden")
            account = _get_or_create_csv_import_account(db, tenant_id)
            tx_total = (
                db.query(func.count(BankTransaction.id))
                .filter(BankTransaction.tenant_id == tenant_id, BankTransaction.bank_account_id == account.id)
                .scalar()
                or 0
            )
            progress_cb(0, int(tx_total))
            stop_event = Event()

            def _mirror_progress():
                while not stop_event.wait(0.7):
                    p = _get_budget_progress(str(current_user.id))
                    progress_cb(int(p.get("processed") or 0), int(p.get("total") or tx_total))

            mirror = Thread(target=_mirror_progress, daemon=True)
            mirror.start()
            result = analyze_bank_budget(db=db, current_user=user)
            stop_event.set()
            prog = _get_budget_progress(str(current_user.id))
            progress_cb(int(prog.get("processed") or 0), int(prog.get("total") or 0))
            return result
        finally:
            db.close()

    _start_async_job(job_id, _worker)
    return {"job_id": job_id, "status": "queued", "reused": False}


@app.get("/api/bank/budget/analyze/progress")
def get_budget_analyze_progress(current_user: User = Depends(get_current_user_dep)):
    return _get_budget_progress(str(current_user.id))


@app.get("/api/bank/budget/latest", response_model=BudgetAnalysisOut)
def get_latest_bank_budget_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    candidate_runs = (
        db.query(BankBudgetAnalysisRun)
        .filter(BankBudgetAnalysisRun.tenant_id == tenant_id)
        .order_by(BankBudgetAnalysisRun.created_at.desc())
        .limit(30)
        .all()
    )
    latest_run = None
    for run in candidate_runs:
        has_rows = (
            db.query(BankBudgetAnalysisTx.id)
            .filter(BankBudgetAnalysisTx.tenant_id == tenant_id, BankBudgetAnalysisTx.run_id == run.id)
            .first()
            is not None
        )
        if has_rows:
            latest_run = run
            break
    if not latest_run:
        raise HTTPException(status_code=404, detail="Nog geen budget analyse beschikbaar")

    tx_rows = (
        db.query(BankBudgetAnalysisTx)
        .filter(BankBudgetAnalysisTx.tenant_id == tenant_id, BankBudgetAnalysisTx.run_id == latest_run.id)
        .order_by(BankBudgetAnalysisTx.booking_date.asc(), BankBudgetAnalysisTx.created_at.asc())
        .all()
    )
    summary_points: list[str] = []
    try:
        parsed = json.loads(latest_run.summary_json or "[]")
        if isinstance(parsed, list):
            summary_points = [str(x) for x in parsed]
    except Exception:
        summary_points = []

    transactions = [
        {
            "external_transaction_id": r.external_transaction_id,
            "booking_date": r.booking_date,
            "amount": r.amount,
            "currency": r.currency,
            "counterparty_name": r.counterparty_name,
            "remittance_information": r.remittance_information,
            "flow": r.flow,
            "category": r.category,
            "source": r.source,
            "reason": r.reason,
            "created_at": r.created_at,
        }
        for r in tx_rows
    ]
    transactions = _enrich_budget_transactions_with_doc_links(db, transactions)
    out_settings = settings_to_out(db, tenant_id=tenant_id)
    mappings = out_settings.get("bank_csv_mappings") if isinstance(out_settings, dict) else []
    prompt = str(out_settings.get("bank_csv_prompt") or "").strip() if isinstance(out_settings, dict) else ""
    preferred_categories = _preferred_budget_categories(mappings if isinstance(mappings, list) else [])

    merged = _build_budget_analysis_payload(
        transactions,
        {
            "summary_points": summary_points,
            "transaction_categories": [
                {
                    "external_transaction_id": r.external_transaction_id,
                    "category": r.category,
                    "flow": r.flow,
                    "reason": r.reason,
                    "source": r.source,
                }
                for r in tx_rows
            ],
        },
        mappings if isinstance(mappings, list) else [],
        preferred_categories=preferred_categories,
    )
    merged["transactions"] = _enrich_budget_transactions_with_doc_links(db, merged.get("transactions") or [])
    return {
        "provider": latest_run.provider,
        "model": latest_run.model,
        "generated_at": latest_run.updated_at or latest_run.created_at,
        "prompt_used": bool(prompt),
        "mappings_count": len(mappings) if isinstance(mappings, list) else 0,
        "summary_points": merged.get("summary_points") or [],
        "transactions": merged.get("transactions") or [],
        "category_totals": merged.get("category_totals") or [],
        "year_totals": merged.get("year_totals") or [],
        "month_totals": merged.get("month_totals") or [],
    }


@app.post("/api/bank/budget/refresh", response_model=BudgetAnalysisOut)
def refresh_bank_budget_from_mappings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    account = _get_or_create_csv_import_account(db, tenant_id)
    rows = (
        db.query(BankTransaction)
        .filter(BankTransaction.tenant_id == tenant_id, BankTransaction.bank_account_id == account.id)
        .order_by(BankTransaction.booking_date.asc(), BankTransaction.created_at.asc())
        .all()
    )
    tx_payload = [bank_transaction_to_out(r) for r in rows]
    tx_payload = _enrich_budget_transactions_with_doc_links(db, tx_payload)
    tx_payload = _attach_budget_document_context(db, tx_payload)
    csv_import_ids = sorted({str(r.csv_import_id) for r in rows if r.csv_import_id})

    out_settings = settings_to_out(db, tenant_id=tenant_id)
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

    cached = db.query(BankBudgetAnalysisRun).filter(BankBudgetAnalysisRun.tenant_id == tenant_id, BankBudgetAnalysisRun.source_hash == source_hash).first()
    if cached:
        if csv_import_ids:
            db.query(BankCsvImport).filter(BankCsvImport.tenant_id == tenant_id, BankCsvImport.id.in_(csv_import_ids)).update(
                {
                    BankCsvImport.parsed_at: datetime.utcnow(),
                    BankCsvImport.parsed_source_hash: source_hash,
                },
                synchronize_session=False,
            )
            db.commit()
        cached_rows = (
            db.query(BankBudgetAnalysisTx)
            .filter(BankBudgetAnalysisTx.tenant_id == tenant_id, BankBudgetAnalysisTx.run_id == cached.id)
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
                        "source": r.source,
                    }
                    for r in cached_rows
                ],
            },
            mappings if isinstance(mappings, list) else [],
            preferred_categories=preferred_categories,
        )
        merged["transactions"] = _enrich_budget_transactions_with_doc_links(db, merged.get("transactions") or [])
        _persist_bank_tx_classification(db, tenant_id, merged.get("transactions") or [])
        _sync_budget_categories_to_mapping_settings(db, tenant_id, merged.get("transactions"))
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
            BankBudgetAnalysisRun.tenant_id == tenant_id,
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
            .filter(BankBudgetAnalysisTx.tenant_id == tenant_id, BankBudgetAnalysisTx.run_id == previous_llm_run.id)
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
    _persist_bank_tx_classification(db, tenant_id, merged.get("transactions") or [])
    _sync_budget_categories_to_mapping_settings(db, tenant_id, merged.get("transactions"))
    run = BankBudgetAnalysisRun(
        tenant_id=tenant_id,
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
                tenant_id=tenant_id,
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
        db.query(BankCsvImport).filter(BankCsvImport.tenant_id == tenant_id, BankCsvImport.id.in_(csv_import_ids)).update(
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
    tenant_id = _tenant_id_for_user(current_user)
    parsed_ids = [
        r[0]
        for r in db.query(BankTransaction.csv_import_id)
        .filter(BankTransaction.tenant_id == tenant_id, BankTransaction.csv_import_id.is_not(None))
        .distinct()
        .all()
        if r and r[0]
    ]
    if parsed_ids:
        db.query(BankCsvImport).filter(
            BankCsvImport.tenant_id == tenant_id,
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
    rows = db.query(BankCsvImport).filter(BankCsvImport.tenant_id == tenant_id).order_by(BankCsvImport.created_at.desc()).limit(limit).all()
    import_ids = [str(r.id) for r in rows if r and r.id]
    meta_by_import: dict[str, dict[str, str]] = {}
    if import_ids:
        tx_rows = (
            db.query(BankTransaction.csv_import_id, BankTransaction.raw_json)
            .filter(
                BankTransaction.csv_import_id.in_(import_ids),
                BankTransaction.tenant_id == tenant_id,
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
    tenant_id = _tenant_id_for_user(current_user)
    row = db.query(BankCsvImport).filter(BankCsvImport.id == import_id, BankCsvImport.tenant_id == tenant_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="CSV import niet gevonden")

    db.query(BankTransaction).filter(BankTransaction.tenant_id == tenant_id, BankTransaction.csv_import_id == row.id).delete()
    db.delete(row)
    db.commit()
    try:
        audit_log(
            db,
            tenant_id=tenant_id,
            user_id=str(current_user.id),
            action="bank.csv.delete",
            entity_type="bank_csv_import",
            entity_id=str(import_id),
            details={"filename": str(row.filename or "")},
        )
        db.commit()
    except Exception:
        db.rollback()
    return {"ok": True}


@app.post("/api/bank/import-csv/mark-parsed")
def mark_bank_csv_as_parsed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    account = _get_or_create_csv_import_account(db, tenant_id)
    import_ids = [
        r[0]
        for r in (
            db.query(BankTransaction.csv_import_id)
            .filter(
                BankTransaction.bank_account_id == account.id,
                BankTransaction.tenant_id == tenant_id,
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
        .filter(BankCsvImport.tenant_id == tenant_id, BankCsvImport.id.in_(import_ids), BankCsvImport.parsed_at.is_(None))
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
    tenant_id = _tenant_id_for_user(current_user)
    external_id = str(payload.external_transaction_id or "").strip()
    category = str(payload.category or "").strip()
    if not external_id or not category:
        raise HTTPException(status_code=400, detail="external_transaction_id en category zijn verplicht")

    account = _get_or_create_csv_import_account(db, tenant_id)
    tx = (
        db.query(BankTransaction)
        .filter(
            BankTransaction.bank_account_id == account.id,
            BankTransaction.tenant_id == tenant_id,
            BankTransaction.external_transaction_id == external_id,
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transactie niet gevonden")

    tx.category = category
    tx.source = "manual"
    tx.auto_mapping = False
    tx.llm_mapping = False
    tx.manual_mapping = True

    latest_run = (
        db.query(BankBudgetAnalysisRun)
        .filter(BankBudgetAnalysisRun.tenant_id == tenant_id)
        .order_by(BankBudgetAnalysisRun.created_at.desc())
        .first()
    )
    if latest_run:
        latest_row = (
            db.query(BankBudgetAnalysisTx)
            .filter(
                BankBudgetAnalysisTx.tenant_id == tenant_id,
                BankBudgetAnalysisTx.run_id == latest_run.id,
                BankBudgetAnalysisTx.external_transaction_id == external_id,
            )
            .first()
        )
        if latest_row:
            latest_row.category = category
            latest_row.source = "manual"
            latest_row.reason = "Manueel aangepast door gebruiker"
    db.commit()
    try:
        audit_log(
            db,
            tenant_id=tenant_id,
            user_id=str(current_user.id),
            action="bank.tx.manual_category",
            entity_type="bank_transaction",
            entity_id=external_id,
            details={"category": category},
        )
        db.commit()
    except Exception:
        db.rollback()
    return {"ok": True, "external_transaction_id": external_id, "category": category, "source": "manual"}


@app.post("/api/documents", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    if not file.content_type or not allowed_content_type(file.content_type):
        raise HTTPException(status_code=400, detail="Unsupported bestandstype")

    member_group_ids = user_group_ids(current_user) if GROUPS_ENABLED else []
    auto_group_id = sorted(member_group_ids)[0] if member_group_ids else None
    if not GROUPS_ENABLED:
        # Keep a stable group_id for labels/tenancy even when group access control is disabled.
        grp = _ensure_tenant_user_group(db, tenant_id)
        if not grp.id:
            db.flush()
        auto_group_id = grp.id

    ext = Path(file.filename or "document").suffix or ".bin"
    document_id = str(uuid.uuid4())
    storage_name = f"{document_id}{ext}"
    file_path = Path(settings.uploads_dir) / storage_name

    data = await file.read()
    content_sha256 = _document_content_sha256(data)

    duplicate = (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
            Document.content_sha256 == content_sha256,
        )
        .order_by(Document.created_at.desc())
        .first()
    )
    file_path.write_bytes(data)

    doc = Document(
        id=document_id,
        tenant_id=tenant_id,
        filename=file.filename or storage_name,
        content_type=file.content_type,
        file_path=str(file_path),
        group_id=auto_group_id,
        uploaded_by_user_id=current_user.id,
        content_sha256=content_sha256,
        duplicate_of_document_id=str(duplicate.id) if duplicate else None,
        duplicate_reason="file_sha256" if duplicate else None,
        duplicate_resolved=False if duplicate else True,
        paid=False,
        ocr_processed=False,
        ai_processed=False,
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        audit_log(
            db,
            tenant_id=tenant_id,
            user_id=str(current_user.id),
            action="documents.upload",
            entity_type="document",
            entity_id=str(doc.id),
            details={
                "filename": str(doc.filename or ""),
                "content_type": str(doc.content_type or ""),
                "duplicate_of_document_id": str(getattr(doc, "duplicate_of_document_id", "") or ""),
                "duplicate_reason": str(getattr(doc, "duplicate_reason", "") or ""),
            },
        )
        db.commit()
    except Exception:
        db.rollback()

    # For duplicates we first ask user whether to keep as separate version or delete.
    if not duplicate:
        background_tasks.add_task(process_document_job, document_id, None)
    return document_to_out(doc)


@app.post("/api/documents/{document_id}/duplicate/keep", response_model=DocumentOut)
async def keep_duplicate_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.tenant_id == tenant_id, Document.deleted_at.is_(None))
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document niet gevonden")

    doc.duplicate_resolved = True
    db.commit()
    db.refresh(doc)

    try:
        audit_log(
            db,
            tenant_id=tenant_id,
            user_id=str(current_user.id),
            action="documents.duplicate.keep",
            entity_type="document",
            entity_id=str(doc.id),
            details={
                "duplicate_of_document_id": str(getattr(doc, "duplicate_of_document_id", "") or ""),
                "duplicate_reason": str(getattr(doc, "duplicate_reason", "") or ""),
            },
        )
        db.commit()
    except Exception:
        db.rollback()

    # Start parsing only if it was not processed yet.
    if doc.status == "uploaded" and not bool(getattr(doc, "ocr_processed", False)):
        background_tasks.add_task(process_document_job, str(doc.id), None)
    return document_to_out(doc)


@app.post("/api/documents/{document_id}/duplicate/delete")
async def delete_duplicate_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    from app.db import upsert_search_index

    tenant_id = _tenant_id_for_user(current_user)
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.tenant_id == tenant_id, Document.deleted_at.is_(None))
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document niet gevonden")

    doc.deleted_at = datetime.utcnow()
    db.commit()
    upsert_search_index(str(doc.id), "")

    try:
        audit_log(
            db,
            tenant_id=tenant_id,
            user_id=str(current_user.id),
            action="documents.duplicate.delete",
            entity_type="document",
            entity_id=str(doc.id),
            details={
                "duplicate_of_document_id": str(getattr(doc, "duplicate_of_document_id", "") or ""),
                "duplicate_reason": str(getattr(doc, "duplicate_reason", "") or ""),
            },
        )
        db.commit()
    except Exception:
        db.rollback()
    return {"ok": True}


@app.get("/api/documents", response_model=list[DocumentOut])
def list_documents(
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    # Groups are currently disabled for access control: all users within a tenant can see all documents.
    can_see_all = True if not GROUPS_ENABLED else _current_user_can_see_all_groups(current_user)
    group_ids = user_group_ids(current_user) if GROUPS_ENABLED else []
    _purge_expired_deleted_docs(db, tenant_id)

    q = db.query(Document).filter(Document.tenant_id == tenant_id, Document.deleted_at.is_(None))
    if not can_see_all:
        q = q.filter(Document.group_id.in_(group_ids))
    docs = q.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()

    # Sync bank mapping categories into labels and attach labels on already verified paid documents.
    try:
        _ensure_bank_category_labels(db, tenant_id)
    except Exception:
        db.rollback()

    # Backfill bank category fields from linked transaction when needed (bulk query).
    ext_ids = [
        str(d.bank_match_external_transaction_id or "").strip()
        for d in docs
        if getattr(d, "bank_paid_verified", False) and (not (getattr(d, "bank_paid_category", None))) and str(getattr(d, "bank_match_external_transaction_id", "") or "").strip()
    ]
    if ext_ids:
        tx_rows = (
            db.query(BankTransaction.external_transaction_id, BankTransaction.category, BankTransaction.source)
            .filter(BankTransaction.tenant_id == tenant_id, BankTransaction.external_transaction_id.in_(ext_ids))
            .all()
        )
        tx_map = {str(eid): {"category": cat, "source": src} for eid, cat, src in tx_rows if eid}
        changed = False
        for d in docs:
            if not getattr(d, "bank_paid_verified", False):
                continue
            if getattr(d, "bank_paid_category", None):
                continue
            eid = str(getattr(d, "bank_match_external_transaction_id", "") or "").strip()
            if not eid:
                continue
            hit = tx_map.get(eid)
            if not hit:
                continue
            d.bank_paid_category = str(hit.get("category") or "").strip() or None
            d.bank_paid_category_source = str(hit.get("source") or "").strip().lower() or None
            if d.bank_paid_category:
                _ensure_doc_has_label(db, d, d.bank_paid_category)
                # If this is an explicit mapping, it may overwrite MAN/AI on documents.
                if str(d.bank_paid_category_source or "").strip().lower() == "mapping":
                    d.budget_category = d.bank_paid_category
                    d.budget_category_source = "mapping"
            changed = True
        if changed:
            db.commit()
            for d in docs:
                d = db.get(Document, d.id) or d

    # Ensure label is attached for paid docs even when bank_paid_category was already stored.
    try:
        changed = False
        for d in docs:
            if not getattr(d, "bank_paid_verified", False):
                continue
            cat = str(getattr(d, "bank_paid_category", "") or "").strip()
            if not cat:
                continue
            if not any(str(l.name or "").strip().lower() == cat.lower() for l in (d.labels or [])):
                _ensure_doc_has_label(db, d, cat)
                changed = True
        if changed:
            db.commit()
    except Exception:
        db.rollback()

    # Backfill document budget labels (MAP/AI) for older docs that were processed before this feature existed.
    try:
        from app.services.pipeline import _apply_bank_mapping_labels as _apply_doc_budget_labels

        changed = False
        for d in docs:
            if d.deleted_at is not None:
                continue
            if str(getattr(d, "status", "") or "") != "ready":
                continue
            if str(getattr(d, "budget_category", "") or "").strip():
                continue
            ocr_text = str(getattr(d, "ocr_text", "") or "").strip()
            if not ocr_text:
                continue
            _apply_doc_budget_labels(db, doc=d, ocr_text=ocr_text)
            if str(getattr(d, "budget_category", "") or "").strip():
                changed = True
            # Enforce single label invariant.
            if _ensure_doc_single_label(db, d):
                changed = True
        if changed:
            db.commit()
    except Exception:
        db.rollback()

    return [document_to_out(d) for d in docs]


def _check_documents_against_bank_csv_core(
    db: Session,
    current_user: User,
    *,
    progress_callback=None,
) -> dict:
    from app.db import upsert_search_index

    tenant_id = _tenant_id_for_user(current_user)
    can_see_all = _current_user_can_see_all_groups(current_user)
    group_ids = set(user_group_ids(current_user))

    docs_q = db.query(Document).filter(
        Document.tenant_id == tenant_id,
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
        .filter(BankTransaction.tenant_id == tenant_id, BankTransaction.amount.is_not(None), BankTransaction.amount < 0)
        .all()
    )
    runtime = get_runtime_settings(db, tenant_id=tenant_id)

    updated_ids: list[str] = []
    matches: list[dict] = []
    now = datetime.utcnow().strftime("%Y-%m-%d")
    total_docs = len(docs)
    for idx, doc in enumerate(docs):
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
            if progress_callback:
                progress_callback(idx + 1, total_docs)
            continue

        doc.paid = True
        doc.bank_paid_verified = True
        doc.bank_match_score = int(best_score)
        doc.bank_match_confidence = str(best_confidence or "")
        doc.bank_match_reason = str(best_reason or "")
        doc.bank_match_external_transaction_id = str(best_tx.external_transaction_id or "")
        doc.paid_on = str(best_tx.booking_date or doc.paid_on or now)
        doc.bank_paid_category = str(best_tx.category or "").strip() or None
        doc.bank_paid_category_source = str(best_tx.source or "").strip().lower() or None
        if doc.bank_paid_category:
            # Synchronize mapping categories into labels and attach label to this document.
            try:
                _ensure_bank_category_labels(db, tenant_id)
                _ensure_doc_has_label(db, doc, doc.bank_paid_category)
                # Explicit mapping from bank settings may overwrite MAN/AI on documents.
                if str(doc.bank_paid_category_source or "").strip().lower() == "mapping":
                    doc.budget_category = doc.bank_paid_category
                    doc.budget_category_source = "mapping"
            except Exception:
                db.rollback()
        bank_remark = _build_bank_check_remark(best_tx, confidence=best_confidence, reason=best_reason)
        current_remark = str(doc.remark or "").strip()
        if bank_remark not in current_remark:
            doc.remark = f"{current_remark}\n{bank_remark}".strip() if current_remark else bank_remark
        doc.searchable_text = _build_searchable_text(doc)
        updated_ids.append(doc.id)
        matches.append(
            {
                "document_id": doc.id,
                "external_transaction_id": str(best_tx.external_transaction_id or ""),
                "score": int(best_score),
                "confidence": str(best_confidence or ""),
                "reason": str(best_reason or ""),
            }
        )
        if progress_callback:
            progress_callback(idx + 1, total_docs)

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
        "matches": matches,
    }


@app.post("/api/documents/check-bank")
def check_documents_against_bank_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    return _check_documents_against_bank_csv_core(db, current_user)


@app.post("/api/documents/check-bank/start")
def start_check_documents_against_bank_csv(
    current_user: User = Depends(get_current_user_dep),
):
    require_admin_access(current_user)
    tenant_id = _tenant_id_for_user(current_user)
    db = SessionLocal()
    try:
        running = _find_running_async_job_db(db, tenant_id=tenant_id, job_type="check-bank")
    finally:
        db.close()
    if running:
        return {"job_id": running["id"], "status": running.get("status"), "reused": True}

    db = SessionLocal()
    try:
        job_id = _create_async_job_db(db, job_type="check-bank", tenant_id=tenant_id, user_id=str(current_user.id))
    finally:
        db.close()

    def _worker(progress_cb):
        db = SessionLocal()
        try:
            user = db.get(User, current_user.id)
            if not user:
                raise RuntimeError("Gebruiker niet gevonden")
            return _check_documents_against_bank_csv_core(db, user, progress_callback=progress_cb)
        finally:
            db.close()

    _start_async_job(job_id, _worker)
    return {"job_id": job_id, "status": "queued", "reused": False}


@app.get("/api/jobs/{job_id}")
def get_async_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    row = _get_async_job_db(db, job_id)
    if not row or str(row.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Job niet gevonden")
    if str(row.get("user_id")) != str(current_user.id) and not user_is_admin(current_user):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze job")
    return row


@app.get("/api/documents/trash", response_model=list[DocumentOut])
def list_deleted_documents(
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    can_see_all = _current_user_can_see_all_groups(current_user)
    group_ids = user_group_ids(current_user)
    if not can_see_all and not group_ids:
        return []
    _purge_expired_deleted_docs(db, tenant_id)

    q = db.query(Document).filter(Document.tenant_id == tenant_id, Document.deleted_at.is_not(None))
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
    if count:
        try:
            audit_log(
                db,
                tenant_id=_tenant_id_for_user(current_user),
                user_id=str(current_user.id),
                action="documents.delete",
                entity_type="document",
                entity_id=None,
                details={"count": count, "document_ids": payload.document_ids[:50]},
            )
            db.commit()
        except Exception:
            db.rollback()
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
        if str(doc.tenant_id or "") != _tenant_id_for_user(current_user):
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
        if doc and str(doc.tenant_id or "") == _tenant_id_for_user(current_user) and doc.deleted_at is None and doc.searchable_text:
            upsert_search_index(doc.id, doc.searchable_text or "")

    if count:
        try:
            audit_log(
                db,
                tenant_id=_tenant_id_for_user(current_user),
                user_id=str(current_user.id),
                action="documents.restore",
                entity_type="document",
                entity_id=None,
                details={"count": count, "document_ids": payload.document_ids[:50]},
            )
            db.commit()
        except Exception:
            db.rollback()

    return {"count": count}


@app.get("/api/documents/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    doc = ensure_doc_access(db.get(Document, document_id), current_user)
    try:
        if _ensure_doc_single_label(db, doc):
            db.commit()
            db.refresh(doc)
    except Exception:
        db.rollback()
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
    before = {
        "subject": doc.subject,
        "issuer": doc.issuer,
        "category": doc.category,
        "document_date": doc.document_date,
        "due_date": doc.due_date,
        "total_amount": doc.total_amount,
        "currency": doc.currency,
        "iban": doc.iban,
        "structured_reference": doc.structured_reference,
        "paid": doc.paid,
        "paid_on": doc.paid_on,
        "remark": doc.remark,
        "line_items": doc.line_items,
        "labels": [str(l.id) for l in (doc.labels or [])],
    }

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
        doc.bank_match_score = None
        doc.bank_match_confidence = None
        doc.bank_match_reason = None
        doc.bank_match_external_transaction_id = None

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
            resolved = _resolve_category(db, doc.tenant_id, raw_category, [doc.group_id] if doc.group_id else None)
            if resolved:
                doc.category = resolved

    if payload.label_ids is not None:
        labels = []
        if payload.label_ids:
            chosen_ids = [str(x) for x in payload.label_ids if str(x).strip()][:1]
            if chosen_ids:
                if GROUPS_ENABLED:
                    labels = db.query(Label).filter(Label.id.in_(chosen_ids), Label.group_id == doc.group_id).all()
                else:
                    labels = db.query(Label).filter(Label.id.in_(chosen_ids), Label.tenant_id == doc.tenant_id).all()
        if labels:
            chosen = str(labels[0].name or "").strip()
            if chosen:
                doc.budget_category = chosen
                doc.budget_category_source = "manual"
            # Enforce single label association row
            _ensure_doc_single_label(db, doc)
        else:
            # Clear labels + budget_category when user clears selection
            db.execute(text("DELETE FROM document_labels WHERE document_id = :doc_id"), {"doc_id": str(doc.id)})
            doc.labels = []
            doc.budget_category = None
            doc.budget_category_source = None

    doc.searchable_text = _build_searchable_text(doc)
    db.commit()
    db.refresh(doc)
    upsert_search_index(doc.id, doc.searchable_text or "")

    after = {
        "subject": doc.subject,
        "issuer": doc.issuer,
        "category": doc.category,
        "document_date": doc.document_date,
        "due_date": doc.due_date,
        "total_amount": doc.total_amount,
        "currency": doc.currency,
        "iban": doc.iban,
        "structured_reference": doc.structured_reference,
        "paid": doc.paid,
        "paid_on": doc.paid_on,
        "remark": doc.remark,
        "line_items": doc.line_items,
        "labels": [str(l.id) for l in (doc.labels or [])],
    }
    changed = [k for k in before.keys() if before.get(k) != after.get(k)]
    if changed:
        try:
            audit_log(
                db,
                tenant_id=_tenant_id_for_user(current_user),
                user_id=str(current_user.id),
                action="documents.update",
                entity_type="document",
                entity_id=str(doc.id),
                details={"changed_fields": changed},
            )
            db.commit()
        except Exception:
            db.rollback()
    return document_to_out(doc)


def _build_fts_query(raw_query: str) -> str:
    value = str(raw_query or "").replace('"', " ").strip()
    if not value:
        return ""
    tokens = [t for t in re.split(r"\s+", value) if t]
    if not tokens:
        return ""
    if len(tokens) == 1:
        tok = re.sub(r"[^A-Za-z0-9_\-]+", "", tokens[0])
        if not tok:
            return ""
        return f'{tok}* OR "{tok}"'
    token_terms = []
    for t in tokens[:8]:
        tok = re.sub(r"[^A-Za-z0-9_\-]+", "", t)
        if tok:
            token_terms.append(f"{tok}*")
    phrase = " ".join(tokens[:8]).strip()
    parts = []
    if token_terms:
        parts.append(" AND ".join(token_terms))
    if phrase:
        parts.append(f'"{phrase}"')
    return " OR ".join(parts)


@app.get("/api/search", response_model=list[DocumentOut])
def search_documents(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
):
    tenant_id = _tenant_id_for_user(current_user)
    can_see_all = _current_user_can_see_all_groups(current_user)
    group_ids = user_group_ids(current_user)
    if not can_see_all and not group_ids:
        return []

    raw_query = q.replace('"', " ").strip()
    query = _build_fts_query(raw_query)
    if not query:
        return []
    try:
        with engine.begin() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT document_id, bm25(document_search) AS rank
                    FROM document_search
                    WHERE content MATCH :q
                    ORDER BY rank ASC
                    LIMIT :limit
                    """
                ),
                {"q": query, "limit": limit * 3},
            ).mappings().all()
    except Exception:
        rows = []

    doc_ids = [r["document_id"] for r in rows]
    if not doc_ids:
        fallback_like = f"%{raw_query.strip().lower()}%"
        q2 = db.query(Document).filter(
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
            Document.searchable_text.is_not(None),
            func.lower(Document.searchable_text).like(fallback_like),
        )
        if not can_see_all:
            q2 = q2.filter(Document.group_id.in_(group_ids))
        docs = q2.order_by(Document.updated_at.desc()).limit(limit).all()
        return [document_to_out(d) for d in docs]

    q = db.query(Document).filter(Document.tenant_id == tenant_id, Document.id.in_(doc_ids), Document.deleted_at.is_(None))
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
