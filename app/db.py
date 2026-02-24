from pathlib import Path

import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings
from app import __db_schema_version__


Path(settings.data_dir).mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{settings.sqlite_path}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


DEFAULT_TENANT_SLUG = "default"
DEFAULT_TENANT_NAME = "Default Tenant"


def _ensure_schema_migrations(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                schema_version INTEGER NOT NULL,
                app_version TEXT NOT NULL,
                git_tag TEXT,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )


def _current_schema_version(conn) -> int:
    # If the table doesn't exist yet (older installs), treat as 0.
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations' LIMIT 1")
    ).mappings().first()
    if not row:
        return 0
    try:
        v = conn.execute(text("SELECT schema_version FROM schema_migrations WHERE id = 1")).mappings().first()
        return int(v["schema_version"]) if v and v.get("schema_version") is not None else 0
    except Exception:
        return 0


def _apply_pending_migrations(conn) -> None:
    """
    Minimal migration framework:
    - Keep an integer DB schema version in the DB.
    - Increment app.__db_schema_version__ when DB schema changes.
    - Add a callable in MIGRATIONS for each new schema version.
    All migrations must be idempotent.
    """
    current = _current_schema_version(conn)
    target = int(__db_schema_version__)
    if current >= target:
        return

    def _migration_v2(c) -> None:
        # Document extraction confidence + training hints.
        if not _column_exists(c, "documents", "field_confidence_json"):
            c.execute(text("ALTER TABLE documents ADD COLUMN field_confidence_json TEXT"))
        c.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS extraction_hints (
                    tenant_id VARCHAR(36) NOT NULL,
                    id VARCHAR(36) PRIMARY KEY,
                    document_id VARCHAR(36) NOT NULL,
                    field_key VARCHAR(64) NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    hint_kind VARCHAR(32) NOT NULL DEFAULT 'manual_correction',
                    hint_text TEXT,
                    category VARCHAR(120),
                    created_by_user_id VARCHAR(36),
                    created_at DATETIME NOT NULL
                )
                """
            )
        )
        c.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_tenant ON extraction_hints(tenant_id)"))
        c.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_document ON extraction_hints(document_id)"))
        c.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_field ON extraction_hints(field_key)"))
        c.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_user ON extraction_hints(created_by_user_id)"))
        c.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_created ON extraction_hints(created_at)"))

    # Future-proof: add explicit migration steps here.
    MIGRATIONS: dict[int, callable] = {
        # 1: baseline (introduced schema_migrations table)
        2: _migration_v2,
    }

    for v in range(current + 1, target + 1):
        fn = MIGRATIONS.get(v)
        if fn:
            fn(conn)


def _record_schema_state(conn) -> None:
    _ensure_schema_migrations(conn)
    app_version = str(getattr(settings, "app_version", "") or "").strip() or "0.0.0"
    git_tag = str(getattr(settings, "git_tag", "") or "").strip() or None
    conn.execute(
        text(
            """
            INSERT INTO schema_migrations(id, schema_version, app_version, git_tag, updated_at)
            VALUES (1, :schema_version, :app_version, :git_tag, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
              schema_version = excluded.schema_version,
              app_version = excluded.app_version,
              git_tag = excluded.git_tag,
              updated_at = CURRENT_TIMESTAMP
            """
        ),
        {
            "schema_version": int(__db_schema_version__),
            "app_version": app_version,
            "git_tag": git_tag,
        },
    )


def _ensure_default_tenant(conn) -> str:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(80) NOT NULL UNIQUE,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )
    row = conn.execute(
        text("SELECT id FROM tenants WHERE slug = :slug LIMIT 1"),
        {"slug": DEFAULT_TENANT_SLUG},
    ).mappings().first()
    if row and row.get("id"):
        return str(row["id"])
    tenant_id = conn.execute(text("SELECT lower(hex(randomblob(16))) AS id")).mappings().first()["id"]
    conn.execute(
        text(
            """
            INSERT INTO tenants(id, name, slug, created_at, updated_at)
            VALUES (:id, :name, :slug, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        ),
        {"id": tenant_id, "name": DEFAULT_TENANT_NAME, "slug": DEFAULT_TENANT_SLUG},
    )
    return str(tenant_id)


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return any(r["name"] == column_name for r in rows)


def _ensure_document_columns() -> None:
    with engine.begin() as conn:
        default_tenant_id = _ensure_default_tenant(conn)
        if not _column_exists(conn, "documents", "tenant_id"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN tenant_id VARCHAR(36)"))
        conn.execute(
            text(
                """
                UPDATE documents
                SET tenant_id = COALESCE(
                    tenant_id,
                    (SELECT g.tenant_id FROM groups g WHERE g.id = documents.group_id),
                    :tenant_id
                )
                WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''
                """
            ),
            {"tenant_id": default_tenant_id},
        )
        if not _column_exists(conn, "documents", "group_id"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN group_id VARCHAR(36)"))
        if not _column_exists(conn, "documents", "uploaded_by_user_id"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN uploaded_by_user_id VARCHAR(36)"))
        if not _column_exists(conn, "documents", "paid"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN paid BOOLEAN DEFAULT 0"))
        if not _column_exists(conn, "documents", "paid_on"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN paid_on VARCHAR(32)"))
        if not _column_exists(conn, "documents", "bank_paid_verified"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN bank_paid_verified BOOLEAN DEFAULT 0"))
            conn.execute(text("UPDATE documents SET bank_paid_verified = 0 WHERE bank_paid_verified IS NULL"))
        if not _column_exists(conn, "documents", "content_sha256"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN content_sha256 VARCHAR(64)"))
        if not _column_exists(conn, "documents", "ocr_text_hash"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN ocr_text_hash VARCHAR(64)"))
        if not _column_exists(conn, "documents", "duplicate_of_document_id"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN duplicate_of_document_id VARCHAR(36)"))
        if not _column_exists(conn, "documents", "duplicate_reason"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN duplicate_reason VARCHAR(32)"))
        if not _column_exists(conn, "documents", "duplicate_resolved"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN duplicate_resolved BOOLEAN DEFAULT 1"))
            conn.execute(text("UPDATE documents SET duplicate_resolved = 1 WHERE duplicate_resolved IS NULL"))
        if not _column_exists(conn, "documents", "bank_match_score"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN bank_match_score INTEGER"))
        if not _column_exists(conn, "documents", "bank_match_confidence"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN bank_match_confidence VARCHAR(16)"))
        if not _column_exists(conn, "documents", "bank_match_reason"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN bank_match_reason TEXT"))
        if not _column_exists(conn, "documents", "bank_match_external_transaction_id"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN bank_match_external_transaction_id VARCHAR(255)"))
        if not _column_exists(conn, "documents", "bank_paid_category"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN bank_paid_category VARCHAR(120)"))
        if not _column_exists(conn, "documents", "bank_paid_category_source"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN bank_paid_category_source VARCHAR(32)"))
        if not _column_exists(conn, "documents", "budget_category"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN budget_category VARCHAR(120)"))
        if not _column_exists(conn, "documents", "budget_category_source"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN budget_category_source VARCHAR(32)"))
        if not _column_exists(conn, "documents", "remark"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN remark TEXT"))
        if not _column_exists(conn, "documents", "ocr_processed"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN ocr_processed BOOLEAN DEFAULT 0"))
            conn.execute(
                text(
                    """
                    UPDATE documents
                    SET ocr_processed = 1
                    WHERE status = 'ready' AND ocr_text IS NOT NULL AND TRIM(ocr_text) != ''
                    """
                )
            )
        if not _column_exists(conn, "documents", "ai_processed"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN ai_processed BOOLEAN DEFAULT 0"))
            conn.execute(
                text(
                    """
                    UPDATE documents
                    SET ai_processed = 1
                    WHERE status = 'ready'
                    AND (
                        category IS NOT NULL
                        OR issuer IS NOT NULL
                        OR subject IS NOT NULL
                        OR document_date IS NOT NULL
                        OR due_date IS NOT NULL
                        OR total_amount IS NOT NULL
                        OR iban IS NOT NULL
                        OR structured_reference IS NOT NULL
                    )
                    """
                )
            )
        if not _column_exists(conn, "documents", "deleted_at"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN deleted_at DATETIME"))
        if not _column_exists(conn, "documents", "line_items"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN line_items TEXT"))
        if not _column_exists(conn, "documents", "extra_fields_json"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN extra_fields_json TEXT"))
        if not _column_exists(conn, "documents", "field_confidence_json"):
            conn.execute(text("ALTER TABLE documents ADD COLUMN field_confidence_json TEXT"))

        # Indexes for dedupe detection
        if _column_exists(conn, "documents", "ocr_text_hash"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_ocr_text_hash ON documents(ocr_text_hash)"))
        if _column_exists(conn, "documents", "duplicate_of_document_id"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_duplicate_of ON documents(duplicate_of_document_id)"))


def _ensure_extraction_hints_table() -> None:
    with engine.begin() as conn:
        _ensure_default_tenant(conn)
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS extraction_hints (
                    tenant_id VARCHAR(36) NOT NULL,
                    id VARCHAR(36) PRIMARY KEY,
                    document_id VARCHAR(36) NOT NULL,
                    field_key VARCHAR(64) NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    hint_kind VARCHAR(32) NOT NULL DEFAULT 'manual_correction',
                    hint_text TEXT,
                    category VARCHAR(120),
                    created_by_user_id VARCHAR(36),
                    created_at DATETIME NOT NULL
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_tenant ON extraction_hints(tenant_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_document ON extraction_hints(document_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_field ON extraction_hints(field_key)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_user ON extraction_hints(created_by_user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_extraction_hints_created ON extraction_hints(created_at)"))


def _ensure_user_columns() -> None:
    with engine.begin() as conn:
        default_tenant_id = _ensure_default_tenant(conn)
        if not _column_exists(conn, "users", "tenant_id"):
            conn.execute(text("ALTER TABLE users ADD COLUMN tenant_id VARCHAR(36)"))
        conn.execute(
            text(
                "UPDATE users SET tenant_id = :tenant_id WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''"
            ),
            {"tenant_id": default_tenant_id},
        )
        if not _column_exists(conn, "users", "avatar_path"):
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_path VARCHAR(500)"))
        if not _column_exists(conn, "users", "created_by_user_id"):
            conn.execute(text("ALTER TABLE users ADD COLUMN created_by_user_id VARCHAR(36)"))


def _ensure_session_token_columns() -> None:
    with engine.begin() as conn:
        if not _column_exists(conn, "session_tokens", "expires_at"):
            conn.execute(text("ALTER TABLE session_tokens ADD COLUMN expires_at DATETIME"))


def _ensure_async_jobs_table() -> None:
    # Table is created by SQLAlchemy metadata for new DBs.
    # This function makes sure it exists for older DBs too.
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS async_jobs (
                    tenant_id VARCHAR(36) NOT NULL,
                    id VARCHAR(36) PRIMARY KEY,
                    job_type VARCHAR(64) NOT NULL,
                    status VARCHAR(16) NOT NULL,
                    user_id VARCHAR(36) NOT NULL,
                    processed INTEGER NOT NULL DEFAULT 0,
                    total INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    result_json TEXT,
                    started_at DATETIME,
                    finished_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_async_jobs_tenant ON async_jobs(tenant_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_async_jobs_type ON async_jobs(job_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_async_jobs_status ON async_jobs(status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_async_jobs_user ON async_jobs(user_id)"))


def _ensure_category_catalog_columns() -> None:
    with engine.begin() as conn:
        default_tenant_id = _ensure_default_tenant(conn)
        if not _column_exists(conn, "category_catalog", "tenant_id"):
            conn.execute(text("ALTER TABLE category_catalog ADD COLUMN tenant_id VARCHAR(36)"))
        conn.execute(
            text(
                "UPDATE category_catalog SET tenant_id = :tenant_id WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''"
            ),
            {"tenant_id": default_tenant_id},
        )
        if not _column_exists(conn, "category_catalog", "prompt_template"):
            conn.execute(text("ALTER TABLE category_catalog ADD COLUMN prompt_template TEXT"))
        if not _column_exists(conn, "category_catalog", "parse_fields_json"):
            conn.execute(text("ALTER TABLE category_catalog ADD COLUMN parse_fields_json TEXT"))
        if not _column_exists(conn, "category_catalog", "parse_config_json"):
            conn.execute(text("ALTER TABLE category_catalog ADD COLUMN parse_config_json TEXT"))
        if not _column_exists(conn, "category_catalog", "paid_default"):
            conn.execute(text("ALTER TABLE category_catalog ADD COLUMN paid_default BOOLEAN"))


def _ensure_category_prompt_templates() -> None:
    structured_ref_instruction = (
        "Voor structured_reference (gestructureerde mededeling): herken Belgische vorm ###/####/#####, "
        "vaak in +++...+++ of ***...***. Strip +/* tekens en geef exact ###/####/##### terug. "
        "Als geen valide patroon aanwezig is: null."
    )
    with engine.begin() as conn:
        # Backfill only if prompt is empty or still on old default style.
        conn.execute(
            text(
                """
                UPDATE category_catalog
                SET prompt_template = :prompt
                WHERE lower(name) IN ('factuur', 'rekening')
                  AND (
                    prompt_template IS NULL
                    OR trim(prompt_template) = ''
                    OR (
                      lower(prompt_template) LIKE '%voor factuur/rekening:%'
                      AND lower(prompt_template) NOT LIKE '%###/####/#####%'
                    )
                  )
                """
            ),
            {
                "prompt": (
                    "Extracteer relevante documentvelden voor deze categorie. "
                    "Geef strikte JSON terug met minstens deze velden: "
                    "category, issuer, subject, document_date, due_date, total_amount, currency, iban, "
                    "structured_reference, summary. "
                    "Voor factuur/rekening: probeer afzender, documentdatum, vervaldatum, totaalbedrag, valuta, "
                    "IBAN en gestructureerde mededeling te herkennen. "
                    f"{structured_ref_instruction} "
                    "Zet onzekere velden op null."
                )
            },
        )

        # Attest: official certificate/proof documents for taxes/government.
        # Only fill defaults when category exists but has no config yet.
        conn.execute(
            text(
                """
                UPDATE category_catalog
                SET
                  prompt_template = COALESCE(NULLIF(trim(prompt_template), ''), :prompt),
                  parse_fields_json = COALESCE(NULLIF(trim(parse_fields_json), ''), :fields_json),
                  parse_config_json = COALESCE(NULLIF(trim(parse_config_json), ''), :config_json),
                  paid_default = COALESCE(paid_default, 0)
                WHERE lower(name) = 'attest'
                """
            ),
            {
                "prompt": (
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
                "fields_json": json.dumps(
                    [
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
                    ],
                    ensure_ascii=True,
                ),
                "config_json": json.dumps(
                    [
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
                    ],
                    ensure_ascii=True,
                ),
            },
        )


def _ensure_integration_columns() -> None:
    with engine.begin() as conn:
        default_tenant_id = _ensure_default_tenant(conn)
        if not _column_exists(conn, "integration_settings", "tenant_id"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN tenant_id VARCHAR(36)"))
        conn.execute(
            text(
                "UPDATE integration_settings SET tenant_id = :tenant_id WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''"
            ),
            {"tenant_id": default_tenant_id},
        )
        if not _column_exists(conn, "integration_settings", "aws_secret_access_key_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN aws_secret_access_key_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "openrouter_api_key_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN openrouter_api_key_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "openai_api_key_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN openai_api_key_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "openai_model"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN openai_model VARCHAR(128)"))
        if not _column_exists(conn, "integration_settings", "openai_ocr_model"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN openai_ocr_model VARCHAR(128)"))
        if not _column_exists(conn, "integration_settings", "google_api_key_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN google_api_key_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "google_model"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN google_model VARCHAR(128)"))
        if not _column_exists(conn, "integration_settings", "google_ocr_model"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN google_ocr_model VARCHAR(128)"))
        if not _column_exists(conn, "integration_settings", "ai_provider"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN ai_provider VARCHAR(32)"))
        if not _column_exists(conn, "integration_settings", "vdk_base_url"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN vdk_base_url VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "vdk_client_id"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN vdk_client_id VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "vdk_api_key_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN vdk_api_key_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "vdk_password_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN vdk_password_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "kbc_base_url"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN kbc_base_url VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "kbc_client_id"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN kbc_client_id VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "kbc_api_key_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN kbc_api_key_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "kbc_password_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN kbc_password_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "bnp_base_url"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN bnp_base_url VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "bnp_client_id"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN bnp_client_id VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "bnp_api_key_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN bnp_api_key_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "bnp_password_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN bnp_password_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "bank_provider"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN bank_provider VARCHAR(32)"))
        if not _column_exists(conn, "integration_settings", "bank_csv_prompt"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN bank_csv_prompt TEXT"))
        if not _column_exists(conn, "integration_settings", "bank_csv_mapping_json"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN bank_csv_mapping_json TEXT"))
        if not _column_exists(conn, "integration_settings", "mail_ingest_enabled"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_ingest_enabled BOOLEAN DEFAULT 0"))
            conn.execute(text("UPDATE integration_settings SET mail_ingest_enabled = 0 WHERE mail_ingest_enabled IS NULL"))
        if not _column_exists(conn, "integration_settings", "mail_imap_host"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_imap_host VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "mail_imap_port"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_imap_port INTEGER"))
        if not _column_exists(conn, "integration_settings", "mail_imap_username"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_imap_username VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "mail_imap_password_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_imap_password_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "mail_imap_folder"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_imap_folder VARCHAR(128)"))
        if not _column_exists(conn, "integration_settings", "mail_imap_use_ssl"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_imap_use_ssl BOOLEAN DEFAULT 1"))
            conn.execute(text("UPDATE integration_settings SET mail_imap_use_ssl = 1 WHERE mail_imap_use_ssl IS NULL"))
        if not _column_exists(conn, "integration_settings", "mail_ingest_frequency_minutes"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_ingest_frequency_minutes INTEGER"))
        if not _column_exists(conn, "integration_settings", "mail_ingest_group_id"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_ingest_group_id VARCHAR(36)"))
        if not _column_exists(conn, "integration_settings", "mail_ingest_attachment_types"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN mail_ingest_attachment_types VARCHAR(64)"))
        if not _column_exists(conn, "integration_settings", "smtp_server"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN smtp_server VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "smtp_port"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN smtp_port INTEGER"))
        if not _column_exists(conn, "integration_settings", "smtp_username"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN smtp_username VARCHAR(255)"))
        if not _column_exists(conn, "integration_settings", "smtp_password_encrypted"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN smtp_password_encrypted TEXT"))
        if not _column_exists(conn, "integration_settings", "smtp_sender_email"):
            conn.execute(text("ALTER TABLE integration_settings ADD COLUMN smtp_sender_email VARCHAR(255)"))


def _ensure_bank_columns() -> None:
    with engine.begin() as conn:
        default_tenant_id = _ensure_default_tenant(conn)
        for table in [
            "bank_accounts",
            "bank_transactions",
            "bank_csv_imports",
            "bank_category_mappings",
            "bank_budget_analysis_runs",
            "bank_budget_analysis_txs",
            "mail_ingest_seen",
            "labels",
            "groups",
            "session_tokens",
        ]:
            if _column_exists(conn, table, "tenant_id"):
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN tenant_id VARCHAR(36)"))

        conn.execute(
            text(
                "UPDATE groups SET tenant_id = :tenant_id WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''"
            ),
            {"tenant_id": default_tenant_id},
        )
        conn.execute(
            text(
                """
                UPDATE labels
                SET tenant_id = COALESCE(
                    tenant_id,
                    (SELECT g.tenant_id FROM groups g WHERE g.id = labels.group_id),
                    :tenant_id
                )
                WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''
                """
            ),
            {"tenant_id": default_tenant_id},
        )


        # De-duplicate labels tenant-wide (trim + case-insensitive).
        # Older versions created labels in different groups; in the current app labels are tenant-wide.
        # Merge duplicates by keeping 1 canonical label per normalized name and re-pointing associations.
        conn.execute(text("UPDATE labels SET name = TRIM(name) WHERE name IS NOT NULL"))
        dup_keys = conn.execute(
            text(
                """
                SELECT tenant_id AS tenant_id, lower(trim(name)) AS k, COUNT(*) AS c
                FROM labels
                WHERE tenant_id IS NOT NULL AND TRIM(tenant_id) != '' AND name IS NOT NULL AND TRIM(name) != ''
                GROUP BY tenant_id, k
                HAVING c > 1
                """
            )
        ).mappings().all()
        for row in dup_keys:
            tenant_id = str(row["tenant_id"])
            k = str(row["k"])
            keep = conn.execute(
                text(
                    """
                    SELECT id
                    FROM labels
                    WHERE tenant_id = :tenant_id AND lower(trim(name)) = :k
                    ORDER BY datetime(created_at) ASC, id ASC
                    LIMIT 1
                    """
                ),
                {"tenant_id": tenant_id, "k": k},
            ).mappings().first()
            if not keep or not keep.get("id"):
                continue
            keep_id = str(keep["id"])

            dups = conn.execute(
                text(
                    """
                    SELECT id
                    FROM labels
                    WHERE tenant_id = :tenant_id AND lower(trim(name)) = :k AND id != :keep_id
                    """
                ),
                {"tenant_id": tenant_id, "k": k, "keep_id": keep_id},
            ).mappings().all()
            for d in dups:
                dup_id = str(d["id"])
                # Re-point document_labels associations to the kept label.
                conn.execute(
                    text(
                        """
                        INSERT OR IGNORE INTO document_labels(document_id, label_id)
                        SELECT document_id, :keep_id
                        FROM document_labels
                        WHERE label_id = :dup_id
                        """
                    ),
                    {"keep_id": keep_id, "dup_id": dup_id},
                )
                conn.execute(text("DELETE FROM document_labels WHERE label_id = :dup_id"), {"dup_id": dup_id})
                conn.execute(text("DELETE FROM labels WHERE id = :dup_id"), {"dup_id": dup_id})

        # Prevent future duplicates (tenant-wide, trimmed, case-insensitive).
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_labels_tenant_normname
                ON labels(tenant_id, lower(trim(name)))
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE session_tokens
                SET tenant_id = COALESCE(
                    tenant_id,
                    (SELECT u.tenant_id FROM users u WHERE u.id = session_tokens.user_id),
                    :tenant_id
                )
                WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''
                """
            ),
            {"tenant_id": default_tenant_id},
        )
        conn.execute(
            text(
                "UPDATE bank_accounts SET tenant_id = :tenant_id WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''"
            ),
            {"tenant_id": default_tenant_id},
        )
        conn.execute(
            text(
                """
                UPDATE bank_transactions
                SET tenant_id = COALESCE(
                    tenant_id,
                    (SELECT a.tenant_id FROM bank_accounts a WHERE a.id = bank_transactions.bank_account_id),
                    :tenant_id
                )
                WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''
                """
            ),
            {"tenant_id": default_tenant_id},
        )
        conn.execute(
            text(
                "UPDATE bank_csv_imports SET tenant_id = :tenant_id WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''"
            ),
            {"tenant_id": default_tenant_id},
        )
        conn.execute(
            text(
                "UPDATE bank_category_mappings SET tenant_id = :tenant_id WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''"
            ),
            {"tenant_id": default_tenant_id},
        )
        conn.execute(
            text(
                "UPDATE bank_budget_analysis_runs SET tenant_id = :tenant_id WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''"
            ),
            {"tenant_id": default_tenant_id},
        )
        conn.execute(
            text(
                """
                UPDATE bank_budget_analysis_txs
                SET tenant_id = COALESCE(
                    tenant_id,
                    (SELECT r.tenant_id FROM bank_budget_analysis_runs r WHERE r.id = bank_budget_analysis_txs.run_id),
                    :tenant_id
                )
                WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''
                """
            ),
            {"tenant_id": default_tenant_id},
        )
        conn.execute(
            text(
                """
                UPDATE mail_ingest_seen
                SET tenant_id = COALESCE(tenant_id, :tenant_id)
                WHERE tenant_id IS NULL OR TRIM(tenant_id) = ''
                """
            ),
            {"tenant_id": default_tenant_id},
        )

        if not _column_exists(conn, "bank_accounts", "provider"):
            conn.execute(text("ALTER TABLE bank_accounts ADD COLUMN provider VARCHAR(32)"))
            conn.execute(text("UPDATE bank_accounts SET provider = 'vdk' WHERE provider IS NULL OR TRIM(provider) = ''"))
        if not _column_exists(conn, "bank_transactions", "csv_import_id"):
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN csv_import_id VARCHAR(36)"))
        if not _column_exists(conn, "bank_transactions", "dedupe_hash"):
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN dedupe_hash VARCHAR(64)"))
        if not _column_exists(conn, "bank_transactions", "category"):
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN category VARCHAR(120)"))
        if not _column_exists(conn, "bank_transactions", "source"):
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN source VARCHAR(32)"))
        if not _column_exists(conn, "bank_transactions", "auto_mapping"):
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN auto_mapping BOOLEAN DEFAULT 0"))
            conn.execute(text("UPDATE bank_transactions SET auto_mapping = 0 WHERE auto_mapping IS NULL"))
        if not _column_exists(conn, "bank_transactions", "llm_mapping"):
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN llm_mapping BOOLEAN DEFAULT 0"))
            conn.execute(text("UPDATE bank_transactions SET llm_mapping = 0 WHERE llm_mapping IS NULL"))
        if not _column_exists(conn, "bank_transactions", "manual_mapping"):
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN manual_mapping BOOLEAN DEFAULT 0"))
            conn.execute(text("UPDATE bank_transactions SET manual_mapping = 0 WHERE manual_mapping IS NULL"))
        if not _column_exists(conn, "bank_csv_imports", "parsed_at"):
            conn.execute(text("ALTER TABLE bank_csv_imports ADD COLUMN parsed_at DATETIME"))
        if not _column_exists(conn, "bank_csv_imports", "parsed_source_hash"):
            conn.execute(text("ALTER TABLE bank_csv_imports ADD COLUMN parsed_source_hash VARCHAR(64)"))
        if not _column_exists(conn, "bank_csv_imports", "file_sha256"):
            conn.execute(text("ALTER TABLE bank_csv_imports ADD COLUMN file_sha256 VARCHAR(64)"))
        if _column_exists(conn, "bank_csv_imports", "file_sha256"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bank_csv_imports_file_sha256 ON bank_csv_imports(file_sha256)"))
        if not _column_exists(conn, "bank_category_mappings", "visible_in_budget"):
            conn.execute(text("ALTER TABLE bank_category_mappings ADD COLUMN visible_in_budget BOOLEAN DEFAULT 1"))
            conn.execute(
                text(
                    "UPDATE bank_category_mappings SET visible_in_budget = 1 "
                    "WHERE visible_in_budget IS NULL"
                )
            )
        conn.execute(
            text(
                """
                UPDATE bank_transactions
                SET
                  auto_mapping = CASE WHEN auto_mapping IS NULL THEN 0 ELSE auto_mapping END,
                  llm_mapping = CASE WHEN llm_mapping IS NULL THEN 0 ELSE llm_mapping END,
                  manual_mapping = CASE WHEN manual_mapping IS NULL THEN 0 ELSE manual_mapping END
                """
            )
        )
        if _column_exists(conn, "documents", "content_sha256"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_content_sha256 ON documents(content_sha256)"))
        if _column_exists(conn, "documents", "bank_match_external_transaction_id"):
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_documents_bank_match_tx ON documents(bank_match_external_transaction_id)"
                )
            )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bank_transactions_dedupe_hash ON bank_transactions(dedupe_hash)"))
        # Ensure dedupe_hash is truly unique per account to prevent duplicate transactions.
        # Keep the most recent row (highest rowid) when duplicates exist.
        try:
            conn.execute(
                text(
                    """
                    DELETE FROM bank_transactions
                    WHERE dedupe_hash IS NOT NULL
                      AND TRIM(dedupe_hash) != ''
                      AND rowid NOT IN (
                        SELECT MAX(rowid)
                        FROM bank_transactions
                        WHERE dedupe_hash IS NOT NULL AND TRIM(dedupe_hash) != ''
                        GROUP BY bank_account_id, dedupe_hash
                      )
                    """
                )
            )
        except Exception:
            # Best-effort cleanup: if anything fails, continue without hard-failing init.
            pass
        try:
            conn.execute(
                text(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_bank_tx_account_dedupe
                    ON bank_transactions(bank_account_id, dedupe_hash)
                    WHERE dedupe_hash IS NOT NULL AND TRIM(dedupe_hash) != ''
                    """
                )
            )
        except Exception:
            # If duplicates still exist, do not break startup; application-level checks still apply.
            pass
        conn.execute(
            text(
                """
                UPDATE bank_transactions
                SET
                  manual_mapping = CASE WHEN lower(COALESCE(source, '')) = 'manual' THEN 1 ELSE manual_mapping END,
                  auto_mapping = CASE WHEN lower(COALESCE(source, '')) = 'mapping' THEN 1 ELSE auto_mapping END,
                  llm_mapping = CASE
                    WHEN lower(COALESCE(source, '')) = 'llm' THEN 1
                    WHEN (COALESCE(category, '') != '' AND COALESCE(auto_mapping, 0) = 0 AND COALESCE(manual_mapping, 0) = 0) THEN 1
                    ELSE llm_mapping
                  END
                WHERE COALESCE(auto_mapping, 0) = 0
                  AND COALESCE(llm_mapping, 0) = 0
                  AND COALESCE(manual_mapping, 0) = 0
                """
            )
        )


def init_db() -> None:
    from app.models import (
        AuditLog,
        BankAccount,
        BankBudgetAnalysisRun,
        BankBudgetAnalysisTx,
        BankCategoryMapping,
        BankCsvImport,
        BankTransaction,
        CategoryCatalog,
        Document,
        ExtractionHint,
        Group,
        MailIngestSeen,
        SavedView,
        SessionToken,
        Tenant,
        User,
    )

    Base.metadata.create_all(bind=engine)
    _ensure_user_columns()
    _ensure_session_token_columns()
    _ensure_async_jobs_table()
    _ensure_bank_columns()
    _ensure_document_columns()
    _ensure_extraction_hints_table()
    _ensure_category_catalog_columns()
    _ensure_category_prompt_templates()
    _ensure_integration_columns()

    with engine.begin() as conn:
        _ensure_default_tenant(conn)
        conn.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS document_search
                USING fts5(document_id UNINDEXED, content);
                """
            )
        )
        # Persist schema/app version in DB to support safe upgrades.
        _apply_pending_migrations(conn)
        _record_schema_state(conn)


def ensure_bootstrap_admin() -> None:
    from app.models import Group, Tenant, User
    from app.services.auth import hash_password

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == DEFAULT_TENANT_SLUG).first()
        if not tenant:
            tenant = Tenant(name=DEFAULT_TENANT_NAME, slug=DEFAULT_TENANT_SLUG)
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

        user = db.query(User).filter(User.email == "admin").first()
        if user:
            changed = False
            if not user.is_bootstrap_admin:
                user.is_bootstrap_admin = True
                changed = True
            if not getattr(user, "tenant_id", None):
                user.tenant_id = tenant.id
                changed = True
            # Only bootstrap the password if it is missing; never override an existing password.
            if not str(getattr(user, "password_hash", "") or "").strip():
                user.password_hash = hash_password(settings.admin_default_password)
                changed = True
            if changed:
                db.commit()
        else:
            user = User(
                tenant_id=tenant.id,
                email="admin",
                name="Admin",
                password_hash=hash_password(settings.admin_default_password),
                is_bootstrap_admin=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        group = db.query(Group).filter(Group.tenant_id == tenant.id, Group.name == "Administrators").first()
        if not group:
            group = Group(tenant_id=tenant.id, name="Administrators")
            db.add(group)
            db.commit()
            db.refresh(group)

        if user not in group.users:
            group.users.append(user)
            db.commit()
    finally:
        db.close()


def upsert_search_index(document_id: str, content: str) -> None:
    safe_content = content or ""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM document_search WHERE document_id = :id"), {"id": document_id})
        conn.execute(
            text("INSERT INTO document_search(document_id, content) VALUES (:id, :content)"),
            {"id": document_id, "content": safe_content},
        )


def get_default_tenant_id() -> str:
    with engine.begin() as conn:
        return _ensure_default_tenant(conn)


def rebuild_search_index_for_all_documents() -> None:
    from app.models import Document

    db = SessionLocal()
    try:
        docs = db.query(Document).filter(Document.deleted_at.is_(None)).all()
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM document_search"))
            for d in docs:
                content = d.searchable_text or ""
                conn.execute(
                    text("INSERT INTO document_search(document_id, content) VALUES (:id, :content)"),
                    {"id": d.id, "content": content},
                )
    finally:
        db.close()
