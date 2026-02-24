from datetime import datetime

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    content_type: str
    thumbnail_path: str | None
    group_id: str | None
    status: str
    error_message: str | None
    category: str | None
    issuer: str | None
    subject: str | None
    document_date: str | None
    due_date: str | None
    total_amount: float | None
    currency: str | None
    iban: str | None
    structured_reference: str | None
    duplicate_of_document_id: str | None = None
    duplicate_reason: str | None = None
    duplicate_resolved: bool = True
    paid: bool
    paid_on: str | None
    bank_paid_verified: bool
    bank_match_score: int | None = None
    bank_match_confidence: str | None = None
    bank_match_reason: str | None = None
    bank_match_external_transaction_id: str | None = None
    bank_paid_category: str | None = None
    bank_paid_category_source: str | None = None
    budget_category: str | None = None
    budget_category_source: str | None = None
    remark: str | None
    ocr_text: str | None
    ocr_processed: bool
    ai_processed: bool
    deleted_at: datetime | None
    line_items: str | None
    extra_fields: dict[str, str] = Field(default_factory=dict)
    field_confidence: dict[str, dict] = Field(default_factory=dict)
    low_confidence_fields: list[str] = Field(default_factory=list)
    label_ids: list[str] = Field(default_factory=list)
    label_names: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LoginIn(BaseModel):
    email: str
    password: str


class SignupIn(BaseModel):
    name: str
    email: str
    password: str


class ForgotPasswordIn(BaseModel):
    email: str


class ResetPasswordIn(BaseModel):
    email: str
    token: str
    password: str
    confirm_password: str


class UserOut(BaseModel):
    id: str
    tenant_id: str
    tenant_name: str | None = None
    email: str
    name: str
    avatar_path: str | None = None
    role: str = "gebruiker"
    is_bootstrap_admin: bool
    is_admin: bool = False
    group_ids: list[str] = Field(default_factory=list)


class AuthOut(BaseModel):
    token: str
    user: UserOut


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str
    is_active: bool = False
    users_count: int = 0
    admins_count: int = 0
    groups_count: int = 0
    documents_count: int = 0
    transactions_count: int = 0


class CreateTenantIn(BaseModel):
    name: str
    slug: str | None = None


class SwitchTenantIn(BaseModel):
    tenant_id: str


class UpdateTenantIn(BaseModel):
    name: str


class UpdateMeIn(BaseModel):
    email: str
    name: str
    password: str | None = None


class SavedViewOut(BaseModel):
    id: str
    name: str
    filters: dict
    created_at: datetime
    updated_at: datetime


class CreateSavedViewIn(BaseModel):
    name: str
    filters: dict


class AuditLogOut(BaseModel):
    id: str
    created_at: datetime
    user_id: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    ip: str | None = None
    user_agent: str | None = None
    details: dict = Field(default_factory=dict)


class GroupOut(BaseModel):
    id: str
    name: str
    user_ids: list[str] = Field(default_factory=list)


class CreateUserIn(BaseModel):
    email: str
    name: str
    password: str
    role: str | None = None
    group_ids: list[str] = Field(default_factory=list)


class UpdateUserIn(BaseModel):
    email: str
    name: str
    password: str | None = None
    role: str | None = None
    group_id: str | None = None


class CreateGroupIn(BaseModel):
    name: str
    user_ids: list[str] = Field(default_factory=list)


class LabelOut(BaseModel):
    id: str
    name: str
    group_id: str


class CreateLabelIn(BaseModel):
    name: str
    group_id: str | None = None


class SetDocumentLabelsIn(BaseModel):
    label_ids: list[str] = Field(default_factory=list)


class UpdateDocumentIn(BaseModel):
    subject: str | None = None
    issuer: str | None = None
    category: str | None = None
    document_date: str | None = None
    due_date: str | None = None
    total_amount: float | None = None
    currency: str | None = None
    iban: str | None = None
    structured_reference: str | None = None
    paid: bool | None = None
    paid_on: str | None = None
    remark: str | None = None
    line_items: str | None = None
    extra_fields: dict[str, str] | None = None
    label_ids: list[str] | None = None


class BulkDocumentIdsIn(BaseModel):
    document_ids: list[str] = Field(default_factory=list)


class CategoryParamOut(BaseModel):
    key: str
    visible_in_overview: bool = True


class CategoryOut(BaseModel):
    id: str | None = None
    name: str
    prompt_template: str | None = None
    parse_fields: list[str] = Field(default_factory=list)
    parse_config: list[CategoryParamOut] = Field(default_factory=list)
    paid_default: bool | None = None


class CreateCategoryIn(BaseModel):
    name: str


class UpdateCategoryIn(BaseModel):
    name: str
    prompt_template: str | None = None
    parse_fields: list[str] = Field(default_factory=list)
    parse_config: list[CategoryParamOut] = Field(default_factory=list)
    paid_default: bool | None = None


class IntegrationSettingsOut(BaseModel):
    aws_region: str
    aws_access_key_id: str
    has_aws_secret_access_key: bool
    ai_provider: str
    has_openrouter_api_key: bool
    has_openai_api_key: bool
    has_google_api_key: bool
    openrouter_model: str
    openrouter_ocr_model: str
    openai_model: str
    openai_ocr_model: str
    google_model: str
    google_ocr_model: str
    vdk_base_url: str
    vdk_client_id: str
    has_vdk_api_key: bool
    has_vdk_password: bool
    kbc_base_url: str
    kbc_client_id: str
    has_kbc_api_key: bool
    has_kbc_password: bool
    bnp_base_url: str
    bnp_client_id: str
    has_bnp_api_key: bool
    has_bnp_password: bool
    bank_provider: str
    vdk_xs2a: bool
    bnp_xs2a: bool
    kbc_xs2a: bool
    mail_ingest_enabled: bool
    mail_imap_host: str
    mail_imap_port: int
    mail_imap_username: str
    has_mail_imap_password: bool
    mail_imap_folder: str
    mail_imap_use_ssl: bool
    mail_ingest_frequency_minutes: int
    mail_ingest_group_id: str
    mail_ingest_attachment_types: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    has_smtp_password: bool
    smtp_sender_email: str
    bank_csv_prompt: str
    bank_csv_mappings: list[dict[str, str | bool]] = Field(default_factory=list)
    default_ocr_provider: str


class UpdateIntegrationSettingsIn(BaseModel):
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    ai_provider: str | None = None
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None
    openrouter_ocr_model: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_ocr_model: str | None = None
    google_api_key: str | None = None
    google_model: str | None = None
    google_ocr_model: str | None = None
    vdk_base_url: str | None = None
    vdk_client_id: str | None = None
    vdk_api_key: str | None = None
    vdk_password: str | None = None
    kbc_base_url: str | None = None
    kbc_client_id: str | None = None
    kbc_api_key: str | None = None
    kbc_password: str | None = None
    bnp_base_url: str | None = None
    bnp_client_id: str | None = None
    bnp_api_key: str | None = None
    bnp_password: str | None = None
    bank_provider: str | None = None
    mail_ingest_enabled: bool | None = None
    mail_imap_host: str | None = None
    mail_imap_port: int | None = None
    mail_imap_username: str | None = None
    mail_imap_password: str | None = None
    mail_imap_folder: str | None = None
    mail_imap_use_ssl: bool | None = None
    mail_ingest_frequency_minutes: int | None = None
    mail_ingest_group_id: str | None = None
    mail_ingest_attachment_types: str | None = None
    smtp_server: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender_email: str | None = None
    bank_csv_prompt: str | None = None
    bank_csv_mappings: list[dict[str, str | bool]] | None = None
    default_ocr_provider: str | None = None


class BankAccountOut(BaseModel):
    id: str
    name: str
    provider: str
    iban: str | None = None
    external_account_id: str
    is_active: bool
    created_at: datetime


class CreateBankAccountIn(BaseModel):
    name: str
    provider: str = "vdk"
    iban: str | None = None
    external_account_id: str


class BankTransactionOut(BaseModel):
    id: str
    bank_account_id: str
    external_transaction_id: str
    dedupe_hash: str | None = None
    csv_import_id: str | None = None
    csv_filename: str | None = None
    booking_date: str | None = None
    value_date: str | None = None
    amount: float | None = None
    currency: str | None = None
    counterparty_name: str | None = None
    remittance_information: str | None = None
    movement_type: str | None = None
    category: str | None = None
    source: str | None = None
    auto_mapping: bool = False
    llm_mapping: bool = False
    manual_mapping: bool = False
    raw_json: str | None = None
    linked_document_id: str | None = None
    linked_document_title: str | None = None
    created_at: datetime


class ImportTransactionsOut(BaseModel):
    imported: int
    duplicate_file: bool = False
    no_new_transactions: bool = False
    existing_filename: str | None = None


class BudgetQuickCategoryMapIn(BaseModel):
    external_transaction_id: str
    category: str


class BankCsvImportOut(BaseModel):
    id: str
    filename: str
    imported_count: int
    account_number: str | None = None
    account_name: str | None = None
    filter_date_from: str | None = None
    filter_date_to: str | None = None
    parsed_at: datetime | None = None
    parsed_source_hash: str | None = None
    created_at: datetime


class BudgetAnalyzedTransactionOut(BaseModel):
    external_transaction_id: str
    csv_import_id: str | None = None
    csv_filename: str | None = None
    booking_date: str | None = None
    value_date: str | None = None
    amount: float = 0
    currency: str | None = None
    counterparty_name: str | None = None
    remittance_information: str | None = None
    movement_type: str | None = None
    raw_json: str | None = None
    flow: str
    category: str
    source: str
    auto_mapping: bool = False
    llm_mapping: bool = False
    manual_mapping: bool = False
    reason: str | None = None
    linked_document_id: str | None = None
    linked_document_title: str | None = None
    created_at: datetime | None = None


class BudgetCategoryTotalOut(BaseModel):
    category: str
    income: float = 0
    expense: float = 0


class BudgetPeriodTotalOut(BaseModel):
    period: str
    income: float = 0
    expense: float = 0


class BudgetAnalysisOut(BaseModel):
    provider: str
    model: str
    generated_at: datetime
    prompt_used: bool
    mappings_count: int
    summary_points: list[str] = Field(default_factory=list)
    transactions: list[BudgetAnalyzedTransactionOut] = Field(default_factory=list)
    category_totals: list[BudgetCategoryTotalOut] = Field(default_factory=list)
    year_totals: list[BudgetPeriodTotalOut] = Field(default_factory=list)
    month_totals: list[BudgetPeriodTotalOut] = Field(default_factory=list)
