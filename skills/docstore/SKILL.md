# Docstore Engineering Skill

Use this skill for non-trivial changes to the Docstore application. It captures
the repository's current architecture, product rules and operational runbooks.
It supplements the cross-project principles in `AGENTS.md`.

## Product boundaries

Docstore is a multi-tenant document archive with OCR/AI extraction, search,
bank CSV imports, budgeting, email integrations and a scan-first Android app.

- Backend: FastAPI, SQLAlchemy and SQLite.
- Browser client: static SPA in `static/`.
- Android client: Kotlin/Jetpack Compose in `mobile/android/`.
- Durable runtime volume: `data/`, mounted as `/app/data` in Compose.
- Production target: `https://docstore.deknijf.eu` behind Nginx. Local
  development remains available through `http://localhost:8000`.

Do not assume the README is the current source of truth for authorization or
mobile behavior; verify against code and this skill before changing either.

## Repository map

| Area | Primary locations | Change rule |
| --- | --- | --- |
| API bootstrap | `app/main.py`, `app/routers/` | Add routes through routers where practical. |
| Established API compatibility | `app/legacy_main.py` | Keep contracts stable; extract reusable logic instead of adding route-level business rules. |
| Persistence/migrations | `app/models.py`, `app/db.py` | Schema changes are migration-driven and idempotent. |
| Domain services | `app/services/` | Put OCR, preprocessing, files, integrations, bank import and audit logic here. |
| Browser SPA | `static/app.js`, `static/styles.css`, `static/index.html` | Preserve desktop/mobile parity for critical flows. |
| Deployment | `Dockerfile`, `docker-compose.yml`, `server_config/` | Configuration comes from `.env`; data is volume-backed. |
| Android app | `mobile/android/` | Keep it scan/upload-first unless feature parity is explicitly requested. |
| Release automation | `.github/workflows/docker-tag-release.yml`, `Makefile` | A semantic git tag drives the Docker image and Android APK. |

## Authorization and tenancy

### Roles

- `superadmin`: cross-tenant access; can create and manage tenants and assign
  `superadmin`.
- `admin`: tenant-scoped administration; may create `admin` or `gebruiker`,
  never `superadmin`.
- `gebruiker`: no Admin section; may upload/manage tenant documents and view
  Budget, but may not access Bank Import CSV or Bank Settings.

### Invariants

1. Resolve the active tenant from the authenticated session before every query,
   mutation, file operation, cache key and background job payload.
2. Query by tenant first. Do not fetch by object ID and authorize afterwards
   unless the tenant predicate is in the same query.
3. `GROUPS_ENABLED` in `app/legacy_main.py` is intentionally `False`.
   Documents are shared by all users in the same tenant. Legacy group rows can
   remain for compatibility but are not product access control.
4. Integration settings, labels, category mappings, saved views, CSV imports,
   bank transactions and audit events are all tenant data.
5. UI hiding is usability only. The server must enforce authorization.

## Document ingest and OCR pipeline

### Storage and provenance

- Original files live below `data/uploads/`; preserve them exactly.
- Optional derivatives live below `data/preprocessed/`; they never replace the
  original evidence.
- Thumbnails live below `data/thumbnails/` and are deliberately generated from
  the original upload. Keep the thumbnail orientation aligned with the detail
  viewer without mutating the source document.
- A new image may be converted to PDF for processing, but conversion failure
  must retain the original format and keep the document usable.

### Processing rules

1. Ingest computes an immutable content hash for binary duplicate detection.
2. Document processing is queued and restart-safe. Use the async-job state;
   never do expensive OCR/AI work directly in a request handler.
3. The OCR/AI reprocess action must run the full safe pipeline: derivatives as
   configured, thumbnail from original, OCR, structured AI extraction,
   confidence/provenance and label assignment.
4. OCR text is the source for full-text search. Keep it tenant-scoped.
5. A semantic duplicate discovered after OCR is an unresolved user decision:
   surface keep/delete and leave it pending until a decision is made.

### Orientation and scan quality

- Use EXIF orientation, PDF page rotation, OCR orientation confidence and
  document geometry as independent signals. Do not rely on image dimensions
  alone.
- When signals disagree, preserve the original and choose the least destructive
  rendering; do not crop text to force a page boundary.
- For mobile capture, prefer the native Google ML Kit document scanner. It
  produces a scan/PDF at the source, is cached locally before upload and avoids
  relying on brittle browser camera behavior.
- Avoid automatic "optimized" output in the UI unless it demonstrably improves
  readable evidence. If a derivative exists, it must never hide the original.

### Extracted fields and confidence

- Category profiles define which fields appear in document detail. Do not show
  fields disabled for the selected category.
- Store confidence per populated visible field. Low-confidence values are
  reviewable; clicking a confidence pill records positive validation. Editing a
  field records a manual correction hint.
- Keep hint provenance (`manual`, OCR/AI, configured mapping) available for
  future extraction prompts. Never claim that user data trained an external
  model unless that is actually implemented.
- For Belgian structured references, recognize normalized forms such as
  `775/0248/46569`, optionally surrounded by `+++` or `***`.

## Bank import, matching and budget

### CSV ingestion

- VDK CSV is semicolon-separated and begins with account/filter metadata before
  the transaction headers. Preserve original source fields and normalized values
  separately.
- Common transaction headers include `Uitvoeringsdatum`, `Valutadatum`,
  `Tegenpartij naam`, `Mededeling`, `Bedrag`, `Saldo na beweging`, `Kosten` and
  `Soort beweging`.
- De-duplicate an entire CSV by content hash. If a later file has new rows,
  import only transactions that do not already exist under a stable transaction
  identity/content key.
- CSV metadata such as account number, account holder and date filter must be
  stored with the import and exposed in the import/detail UI.

### Category provenance

Each bank transaction must end with exactly one effective category source:

1. `manual_mapping`: user changed the category. This wins over all automation.
2. `auto_mapping`: a tenant mapping matched normalized counterparty name,
   remittance information or movement type.
3. `llm_mapping`: no direct mapping matched; the LLM inferred a category from
   configured categories, mapping hints, transaction fields and optionally a
   linked document.

Rules:

- Preserve `manual_mapping` during ordinary re-categorization.
- Preserve an existing `llm_mapping` when no new explicit mapping applies.
- A new explicit mapping may replace an earlier LLM decision and becomes
  `auto_mapping`.
- Category mappings survive deletion of CSV source data.
- Normalize category names using trim + case-folding. The budget overview must
  group by this canonical name so the same category is never rendered twice.
- `Aanrekening beheerskost` / bank management charges map to `Bankkosten` when
  no more specific explicit rule applies.

### Document-bank reconciliation

- `PAID` is only for a payment verified from a bank transaction. A receipt or a
  manually checked paid flag is not enough.
- Preferred match: structured reference, amount and IBAN/counterparty evidence.
- Safe fallback: exact amount + IBAN where document date and bank transaction
  date are within three months.
- Lower-confidence fallback: exact amount + date within three months + a shared
  counterparty/remittance token of at least four characters. Store the match
  details and confidence in the document notes.
- A validated match updates paid state, paid date, notes and transaction-link;
  the transaction detail then shows a `DOC` badge/link.

## Integrations and secrets

- Providers are tenant-scoped runtime settings. Credentials are write-only in
  API/UI and encrypted at rest through the integration settings service.
- Supported OCR/AI provider choices include Textract and LLM Vision with
  OpenRouter, OpenAI or Google. Respect configured provider and model values.
- Bank XS2A configuration is read-only only. UI blocks are only shown when the
  relevant `VDK_XS2A`, `BNP_XS2A` or `KBC_XS2A` environment switch is true.
- Mail ingest currently uses IMAP attachments; SMTP is for outbound messages.
  Credentials and app passwords belong in `.env`/a secret store, never in code,
  screenshots, logs or commits.
- Validate provider configuration before a costly job. Record actionable error
  details without exposing secrets.

## Background jobs and audit

- Jobs use persisted `AsyncJob` rows and in-process worker threads today. A
  restart must leave interrupted jobs in an observable state rather than falsely
  reporting success.
- New long-running work needs a job type, tenant and user context, progress
  counters, idempotency rule, terminal status and audit event.
- Maintain audit entries for authentication, uploads/deletes, document edits,
  CSV import/delete, category/mapping edits, tenant/role changes and integration
  changes. Do not log secret material or raw passwords.

## Database change procedure

1. Change the SQLAlchemy model and any response/request schemas.
2. Increment `__db_schema_version__` in `app/__init__.py`.
3. Add an idempotent migration function in `app/db.py` and register it in
   `MIGRATIONS`.
4. Make every new query tenant-scoped and every migration safe on both empty and
   existing databases.
5. Test application startup against a copy of a populated `data/documentstore.db`.
6. Verify `schema_migrations` records the deployed app version and git tag.

Never reset or recreate a production SQLite database to deliver a feature.

## Versioning, APK and release procedure

### Version source

- `VERSION` is defined in `.env` for local runtime and mirrored in
  `.env.example` as a non-secret default.
- `APP_VERSION=${VERSION}` and `GIT_TAG=v${VERSION}` are resolved in config.
- Container fallback metadata in `Dockerfile`, Python fallback in
  `app/__init__.py`, static cache version and Android Gradle version must remain
  consistent with the release version.
- Android `versionCode` is derived from semantic version. Incrementing patch
  releases permits an in-place Android upgrade only when the APK is signed with
  the same stable key.

### Build and release

```bash
# Validate the Android artifact locally.
make mobile-android-build

# Publish a release APK into static/mobile for a container build.
make mobile-android-publish

# Release after tests and migration validation.
git tag vMAJOR.MINOR.PATCH
git push origin main --tags
```

The tag workflow builds `deknijf/docstore:<tag>` and embeds the APK. Configure
these GitHub secrets for update-compatible Android releases:

- `ANDROID_SIGNING_KEYSTORE_BASE64`
- `ANDROID_SIGNING_STORE_PASSWORD`
- `ANDROID_SIGNING_KEY_ALIAS`
- `ANDROID_SIGNING_KEY_PASSWORD`

The workflow can generate an ephemeral key when those values are absent, but
that APK cannot replace an already installed production APK.

## Deployment and incident checks

### Local

```bash
cp .env.example .env
docker compose up --build
```

- Preserve `HOST_PORT` default `8000` for local development.
- Configure `ALLOWED_HOSTS` for localhost and the active LAN address/range when
  testing from a phone. Do not weaken host validation globally.

### Production

- Use `server_config/` as the Nginx/systemd reference.
- Set `PUBLIC_BASE_URL=https://docstore.deknijf.eu`, trusted hosts and proxy
  settings in production `.env`.
- Keep `/home/admin/docstore/data` durable across `docker compose pull/up`.
- Nginx must allow the expected mobile upload size; check conflicting server
  blocks before reloading Nginx.

### Before declaring an incident fixed

1. Check health and container logs.
2. Confirm database schema version/migrations completed.
3. Confirm the affected tenant can read its own data but not another tenant's.
4. Verify original upload, thumbnail and derivative paths independently.
5. For mobile upload failures, verify reverse-proxy body size, allowed hosts,
   CORS/auth behavior and the pending WorkManager queue.

## Verification checklist

Use the smallest relevant set after each change:

```bash
git diff --check
python -m compileall app
docker compose config
make mobile-android-build
```

Also add or update focused tests for tenant isolation, migration behavior,
duplicate detection, bank categorization provenance and document-bank matching
when changing those areas.
