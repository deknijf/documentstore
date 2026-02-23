# AGENTS.md

This file defines a reusable, framework-agnostic engineering baseline for building and operating high-quality SaaS applications.

## 1. Core Engineering Principles

- Build for correctness first, then optimize.
- Prefer explicitness over implicit magic.
- Keep features composable and testable.
- Fail safely: degrade gracefully, never silently corrupt data.
- Treat security, migrations, and observability as first-class requirements.

## 2. Architecture Baseline

- Use clear boundaries:
  - `API / transport` layer
  - `application/service` layer
  - `data access` layer
  - `background jobs/workers`
- Keep domain logic out of controllers/routes.
- Make side effects (email, OCR, payments, LLM calls, webhooks) injectable behind interfaces.
- Add idempotency for all ingest/import and async job triggers.
- Prefer append-only audit/event tables for critical changes.

## 3. Data Modeling and Migrations

- Every schema change must be migration-driven and backward-compatible during rollout.
- Never ship code that requires manual DB edits in production.
- Use strong constraints:
  - foreign keys
  - unique indexes for de-duplication keys
  - check constraints for finite enums/states
- Include:
  - `created_at`, `updated_at` (UTC)
  - `deleted_at` for soft-delete where restore is needed
  - source/provenance columns when enrichment/AI is used
- Keep migration history in DB (`schema_migrations` or equivalent) and enforce startup migration checks.

## 4. Multi-Tenant and Authorization

- Tenant isolation is mandatory in read/write paths (DB queries, cache keys, job payloads, file paths).
- Prefer role-based access control with explicit permissions.
- Typical roles:
  - `superadmin` (cross-tenant operations)
  - `admin` (tenant-scoped administration)
  - `user` (tenant-scoped operational use)
- Enforce authz on server side only; UI visibility is not security.
- Log all permission-sensitive actions.

## 5. User and Identity Management

- Passwords:
  - hash with strong adaptive algorithm (Argon2/bcrypt/scrypt)
  - never store plaintext or reversible passwords
- Session/token security:
  - signed, expiring tokens
  - rotation and revocation support
- Password reset:
  - single-use token
  - short expiry
  - do not leak whether account exists
- Support profile management with secure update flows.

## 6. Security Baseline

- Secrets:
  - from environment/runtime secret store
  - never committed
  - rotateable
- Input validation on all boundaries (API, files, CSV, webhooks, integrations).
- Enforce least privilege for all integrations (read-only by default).
- Add CSRF/XSS/SQLi defenses appropriate to stack.
- Rate-limit sensitive endpoints (auth, password reset, expensive jobs, AI endpoints).
- Track dependency vulnerabilities and patch on a fixed cadence.

## 7. Integrations (OCR/AI/Email/Bank/etc.)

- Keep providers pluggable with a provider registry and normalized response contracts.
- Add provider-specific config validation before enabling runtime usage.
- Mark secret fields as write-only in APIs/UI.
- Persist integration health and last error for troubleshooting.
- Add retry with jitter and max-attempt caps.
- For AI:
  - keep deterministic fallback logic
  - persist source of decision (`manual`, `mapping`, `llm`)
  - avoid reprocessing unchanged inputs

## 8. File Ingest and De-Duplication

- Use content hash for binary dedup.
- Add semantic dedup where relevant (extracted structured fields / normalized text).
- Keep unresolved duplicates as explicit user decisions (keep/delete).
- Keep import state machine explicit (`uploaded`, `processing`, `ready`, `failed`, etc.).
- Make file processing idempotent and restart-safe.

## 9. Background Jobs and Reliability

- Long-running tasks must be asynchronous and observable.
- Track job status and progress counters in DB.
- Make jobs retry-safe and idempotent.
- Separate transient failure from permanent failure.
- Provide operational controls:
  - requeue
  - cancel (if safe)
  - dead-letter handling

## 10. API and Frontend Contract Quality

- Keep API response schemas versioned and explicit.
- Never break consumers without migration path.
- Return machine-usable error codes and human-readable messages.
- Keep frontend state normalized; avoid hidden coupling.
- Ensure mobile and desktop parity for critical workflows.

## 11. Observability and Audit

- Structured logs with request/job correlation IDs.
- Metrics for:
  - latency
  - error rate
  - queue depth
  - provider call counts/costly operations
- Audit log at minimum:
  - login/logout
  - create/update/delete of domain entities
  - settings/integration/security changes
  - import/upload/delete events
  - role/permission changes

## 12. Versioning and Release Management

- Use semantic versioning (`MAJOR.MINOR.PATCH`).
- Store app version in code and expose in runtime diagnostics.
- Tie release artifacts to git tags.
- Build immutable artifacts (container images) tagged with version and commit SHA.
- Keep DB migration compatibility rules documented per release.

## 13. CI/CD Baseline

- CI gates before merge:
  - lint
  - type checks
  - unit tests
  - migration sanity checks
  - security scans (dependencies, image)
- Release pipeline on tag:
  - build
  - test
  - scan
  - push image
  - publish release notes/changelog
- Block release on high/critical vulnerabilities unless explicitly waived.

## 14. Deployment and Runtime Ops

- Production config must be environment-driven and reproducible.
- Support both local dev (`localhost`) and production domain config.
- Add health/readiness endpoints.
- Include startup checks:
  - required envs present
  - DB reachable
  - migrations current
- Keep rollback plan for each release.

## 15. Performance and Cost Controls

- Cache only where correctness is unaffected.
- Add cache-busting/versioning for generated assets when needed.
- Avoid duplicate heavy processing (OCR/LLM/import parsing).
- Persist computed intermediates to avoid repeated expensive calls.
- Add per-feature budget guards (max batch size, rate limits, request timeouts).

## 16. Testing Strategy

- Unit tests for domain logic and mapping rules.
- Integration tests for DB queries, migrations, and provider adapters.
- End-to-end tests for key workflows:
  - auth
  - upload/import
  - search/filter
  - role/tenant boundaries
- Regression tests for previously fixed bugs.

## 17. Documentation and Developer Experience

- Keep `.env.example` complete and non-sensitive.
- Document all feature flags and default values.
- Document operational tasks:
  - backup/restore
  - migration
  - rotate secrets
  - incident triage
- Keep runbooks for common failures (provider down, job backlog, migration failure).

## 18. Non-Negotiable Guardrails

- No plaintext secrets in repo.
- No destructive bulk operation without explicit confirmation and audit.
- No cross-tenant data leakage.
- No schema drift outside migrations.
- No production release without passing CI + migration safety.
