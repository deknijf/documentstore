from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


Path(settings.data_dir).mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{settings.sqlite_path}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return any(r["name"] == column_name for r in rows)


def _ensure_document_columns() -> None:
    with engine.begin() as conn:
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


def _ensure_user_columns() -> None:
    with engine.begin() as conn:
        if not _column_exists(conn, "users", "avatar_path"):
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_path VARCHAR(500)"))


def _ensure_category_catalog_columns() -> None:
    with engine.begin() as conn:
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


def _ensure_integration_columns() -> None:
    with engine.begin() as conn:
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


def _ensure_bank_columns() -> None:
    with engine.begin() as conn:
        if not _column_exists(conn, "bank_accounts", "provider"):
            conn.execute(text("ALTER TABLE bank_accounts ADD COLUMN provider VARCHAR(32)"))
            conn.execute(text("UPDATE bank_accounts SET provider = 'vdk' WHERE provider IS NULL OR TRIM(provider) = ''"))
        if not _column_exists(conn, "bank_transactions", "csv_import_id"):
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN csv_import_id VARCHAR(36)"))
        if not _column_exists(conn, "bank_csv_imports", "parsed_at"):
            conn.execute(text("ALTER TABLE bank_csv_imports ADD COLUMN parsed_at DATETIME"))
        if not _column_exists(conn, "bank_csv_imports", "parsed_source_hash"):
            conn.execute(text("ALTER TABLE bank_csv_imports ADD COLUMN parsed_source_hash VARCHAR(64)"))
        if not _column_exists(conn, "bank_category_mappings", "visible_in_budget"):
            conn.execute(text("ALTER TABLE bank_category_mappings ADD COLUMN visible_in_budget BOOLEAN DEFAULT 1"))
            conn.execute(
                text(
                    "UPDATE bank_category_mappings SET visible_in_budget = 1 "
                    "WHERE visible_in_budget IS NULL"
                )
            )


def init_db() -> None:
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
        MailIngestSeen,
        SessionToken,
        User,
    )

    Base.metadata.create_all(bind=engine)
    _ensure_user_columns()
    _ensure_document_columns()
    _ensure_category_catalog_columns()
    _ensure_category_prompt_templates()
    _ensure_integration_columns()
    _ensure_bank_columns()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS document_search
                USING fts5(document_id UNINDEXED, content);
                """
            )
        )


def ensure_bootstrap_admin() -> None:
    from app.models import Group, User
    from app.services.auth import hash_password

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin").first()
        if user:
            if not user.is_bootstrap_admin:
                user.is_bootstrap_admin = True
                db.commit()
        else:
            user = User(
                email="admin",
                name="Admin",
                password_hash=hash_password(settings.admin_default_password),
                is_bootstrap_admin=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        group = db.query(Group).filter(Group.name == "Administrators").first()
        if not group:
            group = Group(name="Administrators")
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
