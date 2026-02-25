from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # "development" or "production"
    environment: str = "development"

    app_name: str = "Document Store"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    # Public base URL (used for absolute links in emails, etc.)
    # Example: https://docstore.deknijf.eu
    public_base_url: str | None = None
    # App version metadata (stored in DB for upgrade tracking; typically equals the git tag without leading "v")
    # Example: 0.6.1
    app_version: str = "0.6.1"
    # Optional git tag/commit metadata for diagnostics. Example: v0.6.1
    git_tag: str | None = None

    # Security / deployment
    # Comma-separated list (or empty) of allowed Host headers.
    # Example: "docstore.deknijf.eu,localhost,127.0.0.1"
    allowed_hosts: str = ""
    # Optional comma-separated CIDR ranges for local/dev host access.
    # Example: "10.10.1.0/24"
    allowed_host_cidrs: str = ""
    # Comma-separated list (or empty) of CORS allow origins.
    # Example: "https://docstore.deknijf.eu"
    cors_allow_origins: str = ""
    # When behind a reverse proxy (nginx/traefik/caddy), set true to trust
    # X-Forwarded-* headers (scheme/host/client ip).
    trust_proxy_headers: bool = False

    # Session / auth
    # Default 30 days.
    session_ttl_days: int = 30

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
    smtp_server: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender_email: str | None = None
    integration_master_key: str = "change-this-in-production"
    admin_default_password: str = "admin"


settings = Settings()
