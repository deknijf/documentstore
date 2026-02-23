# Document Store (OCR + AI)

Een moderne, lichte document store applicatie voor:
- Facturen
- Rekeningen
- Medische documenten
- Aankoopbewijzen
- Belastingsdocumenten
- Overige documenten

Met automatische OCR, AI-catalogisering, thumbnails en centrale full-text search.

## Belangrijkste features

- Upload van `PDF` en `image` bestanden
- OCR parsing via:
  - `AWS Textract`
  - `OpenRouter Vision`
- AI metadata-extractie (OpenRouter):
  - opsteller (`issuer`)
  - documentdatum
  - onderwerp
  - totaalbedrag + valuta
  - uiterste betaaldatum
  - IBAN
  - gestructureerde mededeling
  - categorie
- Thumbnail generatie voor dashboard-overzicht
- Direct doorzoekbare OCR-data via centrale zoekbalk (SQLite FTS5)
- Multi-tenant model met gebruikers en groepen
- Documenten enkel zichtbaar binnen dezelfde groep
- Enkel bootstrap admin kan gebruikers en groepen beheren
- Lichte moderne UI (geen donkere achtergrond)
- Docker + Docker Compose deploy

## Architectuur

- Backend: FastAPI + SQLAlchemy + SQLite (FTS5)
- Auth: token-based login (Bearer)
- Multi-tenancy: users ↔ groups (many-to-many), document per groep
- OCR providers: AWS Textract / OpenRouter Vision
- AI extractor: OpenRouter chat completion met JSON output
- Frontend: statische SPA (`/static`) met drag-drop upload en detaildialog
- Storage:
  - originele bestanden: `data/uploads`
  - thumbnails: `data/thumbnails`
  - DB: `data/documentstore.db`

## Snel starten

1. Maak env file:
```bash
cp .env.example .env
```

2. Vul minimaal in `.env`:
- `OPENROUTER_API_KEY` (voor AI-extractie en/of OCR via OpenRouter)
- `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `AWS_REGION` (voor Textract)

3. Start met Docker Compose:
```bash
docker compose up --build
```

4. Open:
- [http://localhost:8000](http://localhost:8000)

5. Login:
- Gebruik je eigen account (Signup), of een bestaande admin gebruiker (indien aanwezig).

## Versioning & DB upgrades

- App versions volgen semantic versioning en matchen git tags (bv. `v0.5.0`).
- Bij startup schrijft Docstore zijn app-versie en DB schema-versie weg in `schema_migrations` (SQLite).
- Bij toekomstige upgrades met DB-wijzigingen wordt de migratielogica uitgebreid en de schema-versie verhoogd.

## API-overzicht

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/groups`
- `GET /api/admin/users` (bootstrap admin)
- `POST /api/admin/users` (bootstrap admin)
- `GET /api/admin/groups` (bootstrap admin)
- `POST /api/admin/groups` (bootstrap admin)
- `POST /api/documents?ocr_provider=textract|openrouter` (`group_id` verplicht in multipart form)
- `GET /api/documents`
- `GET /api/documents/{id}`
- `GET /api/search?q=...`
- `GET /api/meta/providers`
- `GET /files/{id}`

## Vergelijking met Paperless-ngx en Paperless-AI

Gekeken naar officiële documentatie/repos:
- Paperless-ngx: [docs.paperless-ngx.com](https://docs.paperless-ngx.com/) en [GitHub repo](https://github.com/paperless-ngx/paperless-ngx)
- Paperless-AI: [GitHub repo](https://github.com/clusterzx/paperless-ai)

Feature-pariteit in deze MVP:
- Aanwezig:
  - OCR pipeline
  - AI classificatie/extractie
  - thumbnail dashboard
  - full-text search
  - OpenRouter integratie
- Nog niet aanwezig (roadmap richting Paperless-ngx niveau):
  - tags/correspondents/types met uitgebreide filter UI
  - e-mail ingest/consume workflows
  - uitgebreide rules/matching engine
  - audittrail + geavanceerde RBAC
  - bulk actions, export/import, retentie/policies

## Roadmap (aanbevolen)

1. Geavanceerde rollen naast bootstrap admin
2. Tagging/saved filters + geavanceerde query syntax
3. Retry queue + observability (jobs, metrics, tracing)
4. Encryptie-at-rest en secrets hardening
5. Integratie met object storage (S3/MinIO)
6. Background worker apart (Celery/RQ) voor schaalbaarheid
