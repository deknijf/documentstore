import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("group_id", String(36), ForeignKey("groups.id"), primary_key=True),
)


document_labels = Table(
    "document_labels",
    Base.metadata,
    Column("document_id", String(36), ForeignKey("documents.id"), primary_key=True),
    Column("label_id", String(36), ForeignKey("labels.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_bootstrap_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    groups = relationship("Group", secondary=user_groups, back_populates="users")


class Group(Base):
    __tablename__ = "groups"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", secondary=user_groups, back_populates="groups")


class Label(Base):
    __tablename__ = "labels"
    __table_args__ = (UniqueConstraint("group_id", "name", name="uq_labels_group_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("groups.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    documents = relationship("Document", secondary=document_labels, back_populates="labels")


class CategoryCatalog(Base):
    __tablename__ = "category_catalog"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    prompt_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_default: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class SessionToken(Base):
    __tablename__ = "session_tokens"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class SavedView(Base):
    __tablename__ = "saved_views"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", "name", name="uq_saved_views_tenant_user_name"),)

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    filters_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class AsyncJob(Base):
    __tablename__ = "async_jobs"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued", index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    processed: Mapped[int] = mapped_column(nullable=False, default=0)
    total: Mapped[int] = mapped_column(nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class IntegrationSettings(Base):
    __tablename__ = "integration_settings"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    aws_region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aws_access_key_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aws_secret_access_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aws_secret_access_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    openrouter_api_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    openrouter_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    openrouter_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    openrouter_ocr_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    openai_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    openai_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    openai_ocr_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    google_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    google_ocr_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    vdk_base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vdk_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vdk_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    vdk_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    kbc_base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kbc_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kbc_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    kbc_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    bnp_base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bnp_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bnp_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    bnp_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bank_csv_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_csv_mapping_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    mail_ingest_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mail_imap_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mail_imap_port: Mapped[int | None] = mapped_column(nullable=True)
    mail_imap_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mail_imap_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    mail_imap_folder: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mail_imap_use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mail_ingest_frequency_minutes: Mapped[int | None] = mapped_column(nullable=True)
    mail_ingest_group_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("groups.id"), nullable=True)
    mail_ingest_attachment_types: Mapped[str | None] = mapped_column(String(64), nullable=True)
    smtp_server: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int | None] = mapped_column(nullable=True)
    smtp_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    smtp_sender_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    default_ocr_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class Document(Base):
    __tablename__ = "documents"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    ocr_text_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Duplicate handling:
    # - file_sha256: detected immediately on upload
    # - ocr_text: detected after OCR extraction (100% match)
    duplicate_of_document_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    duplicate_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duplicate_resolved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    group_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("groups.id"), nullable=True, index=True)
    uploaded_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="uploaded", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issuer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    document_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    total_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(64), nullable=True)
    structured_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    paid_on: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bank_paid_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bank_match_score: Mapped[int | None] = mapped_column(nullable=True)
    bank_match_confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    bank_match_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_match_external_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    searchable_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    line_items: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    labels = relationship("Label", secondary=document_labels, back_populates="documents")


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="vdk")
    iban: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_account_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    __table_args__ = (UniqueConstraint("bank_account_id", "external_transaction_id", name="uq_bank_tx_account_external"),)

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bank_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("bank_accounts.id"), nullable=False, index=True)
    csv_import_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("bank_csv_imports.id"), nullable=True, index=True)
    external_transaction_id: Mapped[str] = mapped_column(String(255), nullable=False)
    dedupe_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    booking_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    value_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    counterparty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remittance_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    auto_mapping: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    llm_mapping: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_mapping: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class BankCsvImport(Base):
    __tablename__ = "bank_csv_imports"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    imported_count: Mapped[int] = mapped_column(nullable=False, default=0)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    parsed_source_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class BankCategoryMapping(Base):
    __tablename__ = "bank_category_mappings"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    flow: Mapped[str] = mapped_column(String(16), nullable=False, default="all")
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    visible_in_budget: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BankBudgetAnalysisRun(Base):
    __tablename__ = "bank_budget_analysis_runs"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    mappings_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    transactions_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    tx_count: Mapped[int] = mapped_column(nullable=False, default=0)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BankBudgetAnalysisTx(Base):
    __tablename__ = "bank_budget_analysis_txs"
    __table_args__ = (UniqueConstraint("run_id", "external_transaction_id", name="uq_budget_run_external_tx"),)

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("bank_budget_analysis_runs.id"), nullable=False, index=True)
    external_transaction_id: Mapped[str] = mapped_column(String(255), nullable=False)
    booking_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    counterparty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remittance_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    flow: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MailIngestSeen(Base):
    __tablename__ = "mail_ingest_seen"
    __table_args__ = (
        UniqueConstraint(
            "mailbox_fingerprint",
            "message_uid",
            "attachment_name",
            name="uq_mail_ingest_seen_mail_uid_attachment",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mailbox_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    message_uid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    attachment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
