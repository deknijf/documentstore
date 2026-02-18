from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Document Store"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    data_dir: str = "data"
    uploads_dir: str = "data/uploads"
    thumbnails_dir: str = "data/thumbnails"
    avatars_dir: str = "data/avatars"
    sqlite_path: str = "data/documentstore.db"

    ocr_provider: str = "textract"
    ai_provider: str = "openrouter"

    aws_region: str = "eu-west-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_ocr_model: str = "openai/gpt-4o-mini"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_ocr_model: str = "gpt-4o-mini"
    google_api_key: str | None = None
    google_model: str = "gemini-1.5-flash"
    google_ocr_model: str = "gemini-1.5-flash"
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
    bank_provider: str = "vdk"
    vdk_xs2a: bool = False
    bnp_xs2a: bool = False
    kbc_xs2a: bool = False
    mail_ingest_enabled: bool = False
    mail_imap_host: str | None = None
    mail_imap_port: int = 993
    mail_imap_username: str | None = None
    mail_imap_password: str | None = None
    mail_imap_folder: str = "INBOX"
    mail_imap_use_ssl: bool = True
    mail_ingest_frequency_minutes: int = 0
    mail_ingest_group_id: str | None = None
    mail_ingest_attachment_types: str = "pdf"
    integration_master_key: str = "change-this-in-production"
    admin_default_password: str = "admin"


settings = Settings()
