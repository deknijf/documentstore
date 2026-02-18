from sqlalchemy.orm import Session

import json

from app.config import settings
from app.models import BankCategoryMapping, IntegrationSettings
from app.services.security import decrypt_secret, encrypt_secret


BANK_PROVIDERS = {"vdk", "kbc", "bnp"}
DEFAULT_BANK_CSV_PROMPT = """Bankverrichtingen

Je bent een financieel analist voor persoonlijke budgetten.
Analyseer banktransacties en categoriseer elke transactie exact 1 keer.

Gebruik handmatige mappings uit "Mapping inkomsten / uitgaven" met hoogste prioriteit.
Bij meerdere matches: kies de meest specifieke (langste keywordmatch).
Gebruik bestaande categorieën maximaal; maak enkel een nieuwe categorie als geen bestaande categorie logisch past.

Doel:
1) Totale inkomsten, uitgaven, netto, transactietelling
2) Evolutie per maand en per jaar
3) Categorieverdeling met focus op uitgaven
4) Samenvatting in maximaal 10 concrete kernpunten

Vaste categorieregels:
- Gebruik "Loon" als standaard voor terugkerende inkomsten van werkgever.
- Gebruik primair "Tegenpartij naam" (counterparty_name) en aanvullend "Mededeling" (remittance_information) om de categorie te bepalen.
- Gebruik "Soort beweging" (movement_type) als extra sterk signaal voor de categorie.
- Als "Soort beweging" wijst op "Aanrekening beheerskost" of gelijkaardige beheerskosten: categoriseer als "Bankkosten".
- Als er gelinkte documentcontext beschikbaar is, gebruik die context als extra aanwijzing.
- Als een transactie een inkomen is en in tegenpartij/mededeling termen bevat zoals "werkgever" of "werknemer", categoriseer als "Loon".
- Maak aparte categorie "Bankkosten" voor bankgerelateerde kosten.
- Maak aparte categorie "Kaartuitgaven (VISA/MASTERCARD)" voor Visa/Mastercard/Maestro kaartuitgaven.
- Deze categorieen zijn altijd uitgaven en nooit inkomsten:
  Restaurants / horeca, Boodschappen, Ontspanning, Reizen / transport, Brandstof,
  Huur / lening, Energie, Telecom, Verzekeringen, Belastingen, Bankkosten,
  Kaartuitgaven (VISA/MASTERCARD), Overige uitgaven.

Technisch:
- Positief bedrag = inkomen, negatief bedrag = uitgave.
- Groepeer op kalendermaand (YYYY-MM).
- Werk robuust bij ontbrekende velden.
"""


def _migrate_plaintext_secrets(row: IntegrationSettings, db: Session) -> None:
    changed = False

    if row.aws_secret_access_key and not row.aws_secret_access_key_encrypted:
        row.aws_secret_access_key_encrypted = encrypt_secret(row.aws_secret_access_key)
        row.aws_secret_access_key = None
        changed = True

    if row.openrouter_api_key and not row.openrouter_api_key_encrypted:
        row.openrouter_api_key_encrypted = encrypt_secret(row.openrouter_api_key)
        row.openrouter_api_key = None
        changed = True

    if changed:
        db.commit()


def _normalize_bank_provider(value: str | None) -> str:
    provider = str(value or "vdk").strip().lower()
    return provider if provider in BANK_PROVIDERS else "vdk"


def get_or_create_settings(db: Session) -> IntegrationSettings:
    row = db.get(IntegrationSettings, 1)
    if row:
        _migrate_plaintext_secrets(row, db)
        return row

    row = IntegrationSettings(
        id=1,
        aws_region=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        ai_provider=settings.ai_provider,
        openrouter_model=settings.openrouter_model,
        openrouter_ocr_model=settings.openrouter_ocr_model,
        openai_model=settings.openai_model,
        openai_ocr_model=settings.openai_ocr_model,
        google_model=settings.google_model,
        google_ocr_model=settings.google_ocr_model,
        vdk_base_url=settings.vdk_base_url,
        vdk_client_id=settings.vdk_client_id,
        kbc_base_url=settings.kbc_base_url,
        kbc_client_id=settings.kbc_client_id,
        bnp_base_url=settings.bnp_base_url,
        bnp_client_id=settings.bnp_client_id,
        bank_provider=_normalize_bank_provider(settings.bank_provider),
        mail_ingest_enabled=bool(settings.mail_ingest_enabled),
        mail_imap_host=settings.mail_imap_host,
        mail_imap_port=int(settings.mail_imap_port or 993),
        mail_imap_username=settings.mail_imap_username,
        mail_imap_folder=settings.mail_imap_folder or "INBOX",
        mail_imap_use_ssl=bool(settings.mail_imap_use_ssl),
        mail_ingest_frequency_minutes=int(settings.mail_ingest_frequency_minutes or 0),
        mail_ingest_group_id=settings.mail_ingest_group_id,
        mail_ingest_attachment_types=settings.mail_ingest_attachment_types or "pdf",
        default_ocr_provider=settings.ocr_provider,
    )

    if settings.aws_secret_access_key:
        row.aws_secret_access_key_encrypted = encrypt_secret(settings.aws_secret_access_key)
    if settings.openrouter_api_key:
        row.openrouter_api_key_encrypted = encrypt_secret(settings.openrouter_api_key)
    if settings.openai_api_key:
        row.openai_api_key_encrypted = encrypt_secret(settings.openai_api_key)
    if settings.google_api_key:
        row.google_api_key_encrypted = encrypt_secret(settings.google_api_key)
    if settings.vdk_api_key:
        row.vdk_api_key_encrypted = encrypt_secret(settings.vdk_api_key)
    if settings.vdk_password:
        row.vdk_password_encrypted = encrypt_secret(settings.vdk_password)
    if settings.kbc_api_key:
        row.kbc_api_key_encrypted = encrypt_secret(settings.kbc_api_key)
    if settings.kbc_password:
        row.kbc_password_encrypted = encrypt_secret(settings.kbc_password)
    if settings.bnp_api_key:
        row.bnp_api_key_encrypted = encrypt_secret(settings.bnp_api_key)
    if settings.bnp_password:
        row.bnp_password_encrypted = encrypt_secret(settings.bnp_password)
    if settings.mail_imap_password:
        row.mail_imap_password_encrypted = encrypt_secret(settings.mail_imap_password)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_runtime_settings(db: Session) -> dict[str, str | None]:
    row = get_or_create_settings(db)

    aws_secret = decrypt_secret(row.aws_secret_access_key_encrypted) or settings.aws_secret_access_key
    openrouter_key = decrypt_secret(row.openrouter_api_key_encrypted) or settings.openrouter_api_key
    openai_key = decrypt_secret(row.openai_api_key_encrypted) or settings.openai_api_key
    google_key = decrypt_secret(row.google_api_key_encrypted) or settings.google_api_key

    vdk_api_key = decrypt_secret(row.vdk_api_key_encrypted) or settings.vdk_api_key
    vdk_password = decrypt_secret(row.vdk_password_encrypted) or settings.vdk_password
    kbc_api_key = decrypt_secret(row.kbc_api_key_encrypted) or settings.kbc_api_key
    kbc_password = decrypt_secret(row.kbc_password_encrypted) or settings.kbc_password
    bnp_api_key = decrypt_secret(row.bnp_api_key_encrypted) or settings.bnp_api_key
    bnp_password = decrypt_secret(row.bnp_password_encrypted) or settings.bnp_password
    mail_password = decrypt_secret(row.mail_imap_password_encrypted) or settings.mail_imap_password

    ai_provider = str(row.ai_provider or settings.ai_provider or "openrouter").strip().lower()
    if ai_provider == "gemini":
        ai_provider = "google"

    bank_provider = _normalize_bank_provider(row.bank_provider or settings.bank_provider)

    runtime: dict[str, str | None] = {
        "aws_region": row.aws_region or settings.aws_region,
        "aws_access_key_id": row.aws_access_key_id or settings.aws_access_key_id,
        "aws_secret_access_key": aws_secret,
        "ai_provider": ai_provider,
        "openrouter_api_key": openrouter_key,
        "openrouter_model": row.openrouter_model or settings.openrouter_model,
        "openrouter_ocr_model": row.openrouter_ocr_model or settings.openrouter_ocr_model,
        "openai_api_key": openai_key,
        "openai_model": row.openai_model or settings.openai_model,
        "openai_ocr_model": row.openai_ocr_model or settings.openai_ocr_model,
        "google_api_key": google_key,
        "google_model": row.google_model or settings.google_model,
        "google_ocr_model": row.google_ocr_model or settings.google_ocr_model,
        "vdk_base_url": row.vdk_base_url or settings.vdk_base_url,
        "vdk_client_id": row.vdk_client_id or settings.vdk_client_id,
        "vdk_api_key": vdk_api_key,
        "vdk_password": vdk_password,
        "kbc_base_url": row.kbc_base_url or settings.kbc_base_url,
        "kbc_client_id": row.kbc_client_id or settings.kbc_client_id,
        "kbc_api_key": kbc_api_key,
        "kbc_password": kbc_password,
        "bnp_base_url": row.bnp_base_url or settings.bnp_base_url,
        "bnp_client_id": row.bnp_client_id or settings.bnp_client_id,
        "bnp_api_key": bnp_api_key,
        "bnp_password": bnp_password,
        "bank_provider": bank_provider,
        "default_ocr_provider": row.default_ocr_provider or settings.ocr_provider,
        "mail_ingest_enabled": bool(row.mail_ingest_enabled if row.mail_ingest_enabled is not None else settings.mail_ingest_enabled),
        "mail_imap_host": row.mail_imap_host or settings.mail_imap_host or "",
        "mail_imap_port": row.mail_imap_port or settings.mail_imap_port or 993,
        "mail_imap_username": row.mail_imap_username or settings.mail_imap_username or "",
        "mail_imap_password": mail_password or "",
        "mail_imap_folder": row.mail_imap_folder or settings.mail_imap_folder or "INBOX",
        "mail_imap_use_ssl": bool(row.mail_imap_use_ssl if row.mail_imap_use_ssl is not None else settings.mail_imap_use_ssl),
        "mail_ingest_frequency_minutes": int(row.mail_ingest_frequency_minutes or settings.mail_ingest_frequency_minutes or 0),
        "mail_ingest_group_id": row.mail_ingest_group_id or settings.mail_ingest_group_id or "",
        "mail_ingest_attachment_types": row.mail_ingest_attachment_types or settings.mail_ingest_attachment_types or "pdf",
    }

    runtime["bank_base_url"] = runtime.get(f"{bank_provider}_base_url")
    runtime["bank_client_id"] = runtime.get(f"{bank_provider}_client_id")
    runtime["bank_api_key"] = runtime.get(f"{bank_provider}_api_key")
    runtime["bank_password"] = runtime.get(f"{bank_provider}_password")
    return runtime


def settings_to_out(db: Session) -> dict[str, str | bool]:
    row = get_or_create_settings(db)
    ai_provider = str(row.ai_provider or settings.ai_provider or "openrouter").strip().lower()
    if ai_provider == "gemini":
        ai_provider = "google"
    default_ocr = str(row.default_ocr_provider or settings.ocr_provider or "textract").strip().lower()
    if default_ocr == "openrouter":
        default_ocr = "llm_vision"
    bank_csv_mappings: list[dict[str, str | bool]] = []
    table_rows = (
        db.query(BankCategoryMapping)
        .filter(BankCategoryMapping.is_active.is_(True))
        .order_by(BankCategoryMapping.priority.asc(), BankCategoryMapping.created_at.asc())
        .all()
    )
    if table_rows:
        bank_csv_mappings = [
            {
                "keyword": str(item.keyword or "").strip(),
                "flow": str(item.flow or "all").strip().lower(),
                "category": str(item.category or "").strip(),
                "visible_in_budget": bool(item.visible_in_budget),
            }
            for item in table_rows
            if str(item.keyword or "").strip() or str(item.category or "").strip()
        ]
    elif row.bank_csv_mapping_json:
        # Backward-compatible one-time lazy migration from legacy JSON field.
        try:
            loaded = json.loads(row.bank_csv_mapping_json)
            if isinstance(loaded, list):
                for idx, item in enumerate(loaded):
                    if not isinstance(item, dict):
                        continue
                    keyword = str(item.get("keyword") or "").strip()
                    flow = str(item.get("flow") or "").strip().lower()
                    category = str(item.get("category") or "").strip()
                    if not keyword and not category:
                        continue
                    if flow not in {"income", "expense", "all"}:
                        flow = "all"
                    visible_in_budget = bool(item.get("visible_in_budget", True))
                    db.add(
                        BankCategoryMapping(
                            keyword=keyword,
                            flow=flow,
                            category=category,
                            visible_in_budget=visible_in_budget,
                            priority=idx,
                            is_active=True,
                        )
                    )
                    bank_csv_mappings.append(
                        {
                            "keyword": keyword,
                            "flow": flow,
                            "category": category,
                            "visible_in_budget": visible_in_budget,
                        }
                    )
                db.commit()
        except Exception:
            bank_csv_mappings = []
    return {
        "aws_region": row.aws_region or settings.aws_region,
        "aws_access_key_id": row.aws_access_key_id or settings.aws_access_key_id or "",
        "has_aws_secret_access_key": bool(row.aws_secret_access_key_encrypted),
        "ai_provider": ai_provider,
        "openrouter_model": row.openrouter_model or settings.openrouter_model,
        "openrouter_ocr_model": row.openrouter_ocr_model or settings.openrouter_ocr_model,
        "openai_model": row.openai_model or settings.openai_model,
        "openai_ocr_model": row.openai_ocr_model or settings.openai_ocr_model,
        "google_model": row.google_model or settings.google_model,
        "google_ocr_model": row.google_ocr_model or settings.google_ocr_model,
        "vdk_base_url": row.vdk_base_url or settings.vdk_base_url or "",
        "vdk_client_id": row.vdk_client_id or settings.vdk_client_id or "",
        "has_vdk_api_key": bool(row.vdk_api_key_encrypted),
        "has_vdk_password": bool(row.vdk_password_encrypted),
        "kbc_base_url": row.kbc_base_url or settings.kbc_base_url or "",
        "kbc_client_id": row.kbc_client_id or settings.kbc_client_id or "",
        "has_kbc_api_key": bool(row.kbc_api_key_encrypted),
        "has_kbc_password": bool(row.kbc_password_encrypted),
        "bnp_base_url": row.bnp_base_url or settings.bnp_base_url or "",
        "bnp_client_id": row.bnp_client_id or settings.bnp_client_id or "",
        "has_bnp_api_key": bool(row.bnp_api_key_encrypted),
        "has_bnp_password": bool(row.bnp_password_encrypted),
        "bank_provider": _normalize_bank_provider(row.bank_provider or settings.bank_provider),
        "vdk_xs2a": bool(settings.vdk_xs2a),
        "bnp_xs2a": bool(settings.bnp_xs2a),
        "kbc_xs2a": bool(settings.kbc_xs2a),
        "mail_ingest_enabled": bool(row.mail_ingest_enabled if row.mail_ingest_enabled is not None else settings.mail_ingest_enabled),
        "mail_imap_host": row.mail_imap_host or settings.mail_imap_host or "",
        "mail_imap_port": int(row.mail_imap_port or settings.mail_imap_port or 993),
        "mail_imap_username": row.mail_imap_username or settings.mail_imap_username or "",
        "has_mail_imap_password": bool(row.mail_imap_password_encrypted) or bool(settings.mail_imap_password),
        "mail_imap_folder": row.mail_imap_folder or settings.mail_imap_folder or "INBOX",
        "mail_imap_use_ssl": bool(row.mail_imap_use_ssl if row.mail_imap_use_ssl is not None else settings.mail_imap_use_ssl),
        "mail_ingest_frequency_minutes": int(row.mail_ingest_frequency_minutes or settings.mail_ingest_frequency_minutes or 0),
        "mail_ingest_group_id": row.mail_ingest_group_id or settings.mail_ingest_group_id or "",
        "mail_ingest_attachment_types": row.mail_ingest_attachment_types or settings.mail_ingest_attachment_types or "pdf",
        "bank_csv_prompt": row.bank_csv_prompt or DEFAULT_BANK_CSV_PROMPT,
        "bank_csv_mappings": bank_csv_mappings,
        "has_openrouter_api_key": bool(row.openrouter_api_key_encrypted),
        "has_openai_api_key": bool(row.openai_api_key_encrypted),
        "has_google_api_key": bool(row.google_api_key_encrypted),
        "default_ocr_provider": default_ocr,
    }


def update_settings(
    db: Session,
    *,
    aws_region: str | None,
    aws_access_key_id: str | None,
    aws_secret_access_key: str | None,
    ai_provider: str | None,
    openrouter_api_key: str | None,
    openrouter_model: str | None,
    openrouter_ocr_model: str | None,
    openai_api_key: str | None,
    openai_model: str | None,
    openai_ocr_model: str | None,
    google_api_key: str | None,
    google_model: str | None,
    google_ocr_model: str | None,
    vdk_base_url: str | None,
    vdk_client_id: str | None,
    vdk_api_key: str | None,
    vdk_password: str | None,
    kbc_base_url: str | None,
    kbc_client_id: str | None,
    kbc_api_key: str | None,
    kbc_password: str | None,
    bnp_base_url: str | None,
    bnp_client_id: str | None,
    bnp_api_key: str | None,
    bnp_password: str | None,
    bank_provider: str | None,
    mail_ingest_enabled: bool | None,
    mail_imap_host: str | None,
    mail_imap_port: int | None,
    mail_imap_username: str | None,
    mail_imap_password: str | None,
    mail_imap_folder: str | None,
    mail_imap_use_ssl: bool | None,
    mail_ingest_frequency_minutes: int | None,
    mail_ingest_group_id: str | None,
    mail_ingest_attachment_types: str | None,
    bank_csv_prompt: str | None,
    bank_csv_mappings: list[dict[str, str | bool]] | None,
    default_ocr_provider: str | None,
) -> dict[str, str | bool]:
    row = get_or_create_settings(db)

    if aws_region is not None:
        row.aws_region = aws_region
    if aws_access_key_id is not None:
        row.aws_access_key_id = aws_access_key_id

    if ai_provider is not None:
        provider = str(ai_provider).strip().lower()
        if provider in {"openrouter", "openai", "google", "gemini"}:
            row.ai_provider = "google" if provider == "gemini" else provider

    # Secrets are write-only: only update when non-empty value is provided.
    if aws_secret_access_key is not None and aws_secret_access_key.strip():
        row.aws_secret_access_key_encrypted = encrypt_secret(aws_secret_access_key.strip())
        row.aws_secret_access_key = None

    if openrouter_api_key is not None and openrouter_api_key.strip():
        row.openrouter_api_key_encrypted = encrypt_secret(openrouter_api_key.strip())
        row.openrouter_api_key = None

    if openrouter_model is not None:
        row.openrouter_model = openrouter_model
    if openrouter_ocr_model is not None:
        row.openrouter_ocr_model = openrouter_ocr_model
    if openai_api_key is not None and openai_api_key.strip():
        row.openai_api_key_encrypted = encrypt_secret(openai_api_key.strip())
    if openai_model is not None:
        row.openai_model = openai_model
    if openai_ocr_model is not None:
        row.openai_ocr_model = openai_ocr_model
    if google_api_key is not None and google_api_key.strip():
        row.google_api_key_encrypted = encrypt_secret(google_api_key.strip())
    if google_model is not None:
        row.google_model = google_model
    if google_ocr_model is not None:
        row.google_ocr_model = google_ocr_model

    if vdk_base_url is not None:
        row.vdk_base_url = vdk_base_url
    if vdk_client_id is not None:
        row.vdk_client_id = vdk_client_id
    if vdk_api_key is not None and vdk_api_key.strip():
        row.vdk_api_key_encrypted = encrypt_secret(vdk_api_key.strip())
    if vdk_password is not None and vdk_password.strip():
        row.vdk_password_encrypted = encrypt_secret(vdk_password.strip())

    if kbc_base_url is not None:
        row.kbc_base_url = kbc_base_url
    if kbc_client_id is not None:
        row.kbc_client_id = kbc_client_id
    if kbc_api_key is not None and kbc_api_key.strip():
        row.kbc_api_key_encrypted = encrypt_secret(kbc_api_key.strip())
    if kbc_password is not None and kbc_password.strip():
        row.kbc_password_encrypted = encrypt_secret(kbc_password.strip())

    if bnp_base_url is not None:
        row.bnp_base_url = bnp_base_url
    if bnp_client_id is not None:
        row.bnp_client_id = bnp_client_id
    if bnp_api_key is not None and bnp_api_key.strip():
        row.bnp_api_key_encrypted = encrypt_secret(bnp_api_key.strip())
    if bnp_password is not None and bnp_password.strip():
        row.bnp_password_encrypted = encrypt_secret(bnp_password.strip())

    if bank_provider is not None:
        row.bank_provider = _normalize_bank_provider(bank_provider)
    if mail_ingest_enabled is not None:
        row.mail_ingest_enabled = bool(mail_ingest_enabled)
    if mail_imap_host is not None:
        row.mail_imap_host = str(mail_imap_host or "").strip() or None
    if mail_imap_port is not None:
        row.mail_imap_port = int(mail_imap_port) if int(mail_imap_port) > 0 else 993
    if mail_imap_username is not None:
        row.mail_imap_username = str(mail_imap_username or "").strip() or None
    if mail_imap_password is not None and mail_imap_password.strip():
        row.mail_imap_password_encrypted = encrypt_secret(mail_imap_password.strip())
    if mail_imap_folder is not None:
        row.mail_imap_folder = str(mail_imap_folder or "").strip() or "INBOX"
    if mail_imap_use_ssl is not None:
        row.mail_imap_use_ssl = bool(mail_imap_use_ssl)
    if mail_ingest_frequency_minutes is not None:
        row.mail_ingest_frequency_minutes = max(0, int(mail_ingest_frequency_minutes))
    if mail_ingest_group_id is not None:
        row.mail_ingest_group_id = str(mail_ingest_group_id or "").strip() or None
    if mail_ingest_attachment_types is not None:
        normalized_types = ",".join(
            sorted(
                {
                    x.strip().lower()
                    for x in str(mail_ingest_attachment_types or "").split(",")
                    if x.strip()
                }
            )
        )
        row.mail_ingest_attachment_types = normalized_types or "pdf"
    if bank_csv_prompt is not None:
        row.bank_csv_prompt = bank_csv_prompt
    if bank_csv_mappings is not None:
        cleaned: list[dict[str, str | bool]] = []
        for item in bank_csv_mappings:
            if not isinstance(item, dict):
                continue
            keyword = str(item.get("keyword") or "").strip()
            flow = str(item.get("flow") or "all").strip().lower()
            category = str(item.get("category") or "").strip()
            visible_in_budget = bool(item.get("visible_in_budget", True))
            if not keyword and not category:
                continue
            if flow not in {"income", "expense", "all"}:
                flow = "all"
            cleaned.append(
                {
                    "keyword": keyword,
                    "flow": flow,
                    "category": category,
                    "visible_in_budget": visible_in_budget,
                }
            )
        row.bank_csv_mapping_json = json.dumps(cleaned, ensure_ascii=False)
        db.query(BankCategoryMapping).delete()
        for idx, item in enumerate(cleaned):
            db.add(
                BankCategoryMapping(
                    keyword=item["keyword"],
                    flow=item["flow"],
                    category=item["category"],
                    visible_in_budget=bool(item.get("visible_in_budget", True)),
                    priority=idx,
                    is_active=True,
                )
            )

    if default_ocr_provider is not None:
        ocr_provider = str(default_ocr_provider).strip().lower()
        if ocr_provider in {"textract", "llm_vision", "openrouter"}:
            row.default_ocr_provider = "llm_vision" if ocr_provider == "openrouter" else ocr_provider

    db.commit()
    return settings_to_out(db)
