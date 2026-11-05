# MediSync AI upgrade plan

## Vercel Hobby deployment preparation (2026-11-05)

### Decision

Prepared a single-project Vercel Services configuration for the existing
Next.js and FastAPI applications, with same-origin routing and a protected daily
cleanup Cron endpoint. This uses no copied application code and requires no
database migration. Vercel Services is currently documented as Beta on all
plans, and the Vercel Python runtime documents FastAPI/ASGI and response
streaming. Neither Vercel nor Neon was available in this workspace, so the
configuration is not deployment-verified. **No deploy was made.** Keep patient
data processing and external AI disabled.

### Implemented locally

- Added root `vercel.json` with separate service roots, FastAPI `app.main:app`
  entrypoint, frontend/API/health routing, and a once-daily 03:00 UTC cleanup
  schedule. Preserved Next.js standalone output for the existing Docker image;
  the Next config disables that output only on Vercel.
- Added Python 3.12 selection for the backend Function and same-origin
  production API client behavior while retaining localhost API defaults for
  development.
- Added an exact Vercel preview-origin allowance using the system-provided
  deployment host. Production still requires its explicitly configured
  `FRONTEND_URL`.
- Added protected `/api/cron/cleanup` requiring constant-time `CRON_SECRET`
  comparison and a distinct `CLEANUP_DATABASE_URL`. Cleanup runs with the
  restricted cleanup role, not the API runtime role.
- Implemented a Python TLS context for `verify-full`, using system trust roots
  (or explicitly configured `PGSSLROOTCERT`) with hostname validation. Applied
  this to API, cleanup, and Alembic/migration connections. Migration remains a
  separate manually controlled release operation, never API startup/build.
- Added backend tests for Cron authorization and database separation, TLS
  verification settings, and exact preview-origin scoping. Updated local
  environment examples and documented Vercel/Neon configuration and blockers.

### Verification and blockers

- Backend: `python -m pytest -q` — **89 passed**; Python `compileall` passed.
- Frontend: `npm run lint`, `npm run typecheck`, and production builds passed
  with both `VERCEL` unset (Docker standalone) and `VERCEL=1` (Vercel mode;
  Next.js 16.4.2).
- `vercel.json` parsed and its service roots/entrypoint were checked; `git diff
  --check` passed. Vercel CLI, Docker CLI and `psql` are unavailable, so this
  did not validate Vercel's build/routing or any database connection.
- No Vercel CLI/project or Neon database credentials were available. The
  Vercel build and Services routing, Function bundle size, real `verify-full`
  handshake, actual Cron invocation, and cleanup-role grants remain unverified.
- Doctor photo upload/read still uses local filesystem storage and is not durable
  on Vercel Functions. Configure and test approved object storage before
  depending on that admin workflow. Patient PDF upload remains disabled.
- Confirm that the Vercel Services account/runtime isolates backend secrets from
  frontend code. Project-level environment variables may be shared across
  services; do not expose secrets via `NEXT_PUBLIC_*` or frontend responses.
- Hobby Cron is daily with a broad execution window. Function limits can end
  long SSE responses or cleanup. No staging, privacy, regulatory, clinical, or
  production-readiness assertion is made.

The reproducible project settings and commands are in
[`VERCEL_DEPLOYMENT.md`](./VERCEL_DEPLOYMENT.md).

## Phase 7 infrastructure provisioning and staging (2026-11-05)

### Current decision

**Staging is BLOCKED; NO-GO for real patient data.** Infrastructure discovery
found no Docker/Compose, PostgreSQL client, cloud-provider or Render CLI, staging
URL/CA, staging credentials, cloud account, backup/KMS, audit sink or monitoring
endpoint. No service was provisioned and no connection was made to an unknown
database. All testing used synthetic data or unit fakes. External LLM and patient
data processing remain disabled.

### Implemented locally, but not staging-verified

- Compose now requires separate runtime (`DATABASE_URL`), migration
  (`MIGRATION_DATABASE_URL`) and cleanup (`CLEANUP_DATABASE_URL`) URLs. It has no
  migration/runtime fallback and no longer passes API credentials to cleanup.
- Added password-free, idempotent role setup at
  `backend/db-init/00-create-roles.sql`. It creates fixed roles as `NOLOGIN`, gives
  runtime DML/default grants, gives migration schema CREATE, and avoids putting
  role passwords in SQL. The README directs operators to set passwords
  interactively with `psql \password` and then enable LOGIN.
- `backend/init_db.py` now grants cleanup DELETE only on session, conversation,
  usage and operator-audit tables plus SELECT only on their expiry predicate
  columns after migrations. Production migration fails closed when the cleanup
  role is missing. Unit tests cover privilege scope and the missing-role failure
  path.
- Root `.env.example` now contains separate URL placeholders. Role SQL is mounted
  for PostgreSQL first initialization; it does not execute automatically against
  an existing Docker volume. Existing databases need a DBA-reviewed, non-destructive
  ownership/grant procedure. Do not delete volumes to force this script to run.
- No provider infrastructure was invented for TLS, append-only audit, encrypted
  backups, KMS, monitoring or alerts. Render remains unsupported under current
  production settings: it omits `DATABASE_SSL_MODE=verify-full` and a release
  migration job. A better target must provide a release job, trusted DB CA and
  hostname validation, secret manager, encrypted PITR, immutable audit sink and
  privacy-safe monitoring.

### Phase 7 local verification

- Backend: `backend/.venv/Scripts/python.exe -m pytest` — **83 passed** on Windows /
  Python 3.14.10. Python `compileall` passed.
- Frontend: `npm run lint`, `npm run typecheck`, and `npm run build` passed.
- Compose YAML parsing passed and `git diff --check` passed with the repository's
  existing CRLF normalization warnings.
- Role grant tests use a fake SQLAlchemy connection; they validate the generated
  grant scope and production fail-closed branch, not actual PostgreSQL role ACLs.
- Compose build/start, SQL role provisioning, database migration with distinct
  roles, TLS positive/negative tests, audit sink, backup/restore, outage/restart,
  scheduler and alert tests were **not run** because their required tools and
  staging services are unavailable.

The detailed evidence matrix and exact staging procedure are in
[`PHASE6_DEPLOYMENT_READINESS.md`](./PHASE6_DEPLOYMENT_READINESS.md). To continue,
provide an approved staging access path and a Docker-capable runner; do not send
secrets in chat. The report lists required provider/role scopes. No staging or
production readiness claim is made.

## Phase 6 staging deployment verification (2026-11-05)

### Result

**Staging not available; deployment readiness is NO-GO for real patient data.**
No Docker executable/engine, PostgreSQL client tools, staging-specific
environment variables, staging CA, staging database URL, cloud account, backup
target, KMS, audit sink, log sink or alert destination is available in this
workspace. A sanitized parse of local `backend/.env` (values withheld) showed a
local/container DB endpoint, development environment, default TLS preference and
AI gates defaulting false; it is not staging configuration. No production or
patient data was used. No infrastructure or secret was provisioned.

### Verified locally

- Backend: `backend/.venv/Scripts/python.exe -m pytest` — 81 passed on Windows /
  Python 3.14.10.
- Frontend: `npm run lint`, `npm run typecheck`, and `npm run build` passed.
- `compose.yaml` parses as YAML; `git diff --check` was clean aside from existing
  CRLF normalization notices. Docker Compose interpolation, builds, health, service
  ordering, restart and outage behavior were not run.
- Static configuration review confirms single-origin CORS, exact-origin CSRF
  checks, secure cookies required for production, `/health/ready`, disabled
  external provider calls, default-off AI patient data, local-only Compose port
  binds, disabled SQL echo, and disabled Uvicorn access logging in Docker launch
  paths. These are code/config findings, not staging runtime evidence.
- Previous Phase 5 evidence records PostgreSQL 18 migration `0007 -> 0008`,
  rollback/re-upgrade and disposable dump/restore. Phase 6 did not repeat this
  because PostgreSQL client tools and a staging database were unavailable.

### Deployment findings

- Compose bootstrap uses `POSTGRES_USER`; API and cleanup share `DATABASE_URL`.
  Migration gets a separate URL only if configured, otherwise it falls back to
  the runtime URL. There is no independent cleanup role. Least privilege is not
  validated.
- The operator audit table is in the main DB, and API code can update event state;
  cleanup can delete expired records. No independently controlled append-only
  sink or tamper-resistant audit control exists.
- Production requires `DATABASE_SSL_MODE=verify-full`; no real TLS handshake,
  CA validation, hostname-negative test or `pg_stat_ssl` observation was possible.
- Render sets `APP_ENV=production` but does not set the required SSL mode (default
  remains `prefer`) and does not configure a separate migration job. Its blueprint
  is not verified to start under current production settings and is not approved
  for patient information.
- No encrypted automated backups, PITR/WAL policy, key management, retention,
  backup monitoring, restore evidence, monitoring sink, structured error platform,
  alert rules or on-call route are configured.
- Docker base images use mutable tags and pip is upgraded unpinned in the backend
  image build. CI actions use mutable major tags. No image/dependency scanning job
  is configured. These are supply-chain hardening gaps, not proof of a known
  vulnerability.

Detailed status evidence and reproducible setup/verification steps are in
[`PHASE6_DEPLOYMENT_READINESS.md`](./PHASE6_DEPLOYMENT_READINESS.md). README now
links the disposition and reiterates the staging gates. No Phase 6 controls that
depend on unavailable infrastructure are described as implemented.

### Remaining blockers

1. Provision isolated synthetic-data staging and provide secure, scoped access,
   database hostname and trusted CA for `verify-full` validation.
2. Create separate migration/runtime/cleanup credentials, tighten grants, and
   test expected access plus denied DDL in staging.
3. Implement and test a separately controlled append-only operator audit sink.
4. Configure encrypted scheduled backups/PITR and prove an isolated restore with
   approved recovery objectives and key custody.
5. Install/run Docker Compose E2E, including migration ordering, health, API and
   frontend behavior, cleanup fixture deletion, restarts and DB outage/recovery.
6. Configure privacy-safe monitoring/alerts and run an alert-delivery drill.
7. Review cloud ingress/egress, proxy/platform logs, secret management and
   environment separation. Keep AI patient-data and external-provider switches
   disabled pending independent privacy/security approval.

Phase 6 is not a production-readiness or regulatory-compliance assertion.

## Phase 5 security and infrastructure (2026-11-04)

### Completed in repository

- Added migration `0008_operator_audit` and a fail-closed FastAPI dependency for
  privileged admin API routes and admin doctor mutations. It records only actor
  user ID, method, route template, outcome, and timestamps; path values, query
  strings, request bodies, prompts, and patient content are excluded. Audit
  retention defaults to 365 days and cannot be configured below 180 days. If
  audit insertion fails, the privileged handler is not run. A failed outcome
  update leaves the committed `started` attempt visible for later review.
- The daily cleanup worker now deletes expired authentication sessions in
  addition to expired conversations, old aggregate usage events, and aged
  operator audit events. Conversation FK cascades remove messages and feedback;
  aggregate usage remains non-identifying and is deleted only by its age policy.
- Added `DATABASE_SSL_MODE`; asyncpg receives the configured TLS mode. Production
  requires `verify-full`, secure session cookies, and keeps AI patient-data and
  external provider processing disabled. This enforces a configuration gate;
  TLS negotiation, server identity, host encryption, and managed key controls
  must still be verified against the actual deployment.
- Split Compose migration execution into a one-shot `migrate` service. The API
  receives only `DATABASE_URL`; `MIGRATION_DATABASE_URL` is passed only to the
  migration service. Compose may fall back to `DATABASE_URL` for local setup, so
  operators must configure distinct least-privilege credentials before any
  non-local deployment.
- Disabled Uvicorn access logs in the checked-in Docker launch paths because the
  default request line can include query strings. Reverse proxy, platform, and
  database logs need independent configuration and review.
- Added tests for audit event minimization/outcomes/fail-closed behavior, audit
  retention configuration, production TLS configuration, and coverage of admin
  routes and doctor mutations by the audit dependency. No new runtime package
  was added.
- Updated README and added `PRIVACY_DATA_FLOWS.md` with current data paths,
  retention/deletion semantics, third-party processing state, India legal review
  points and official references, backup design and deployment blockers. Updated
  `AI_RAG_ARCHITECTURE.md` with an explicit pgvector/model/source/evaluation
  readiness assessment and setup gates.
- Removed Uvicorn request access logs from the repository Docker launch paths so
  default request-line logging cannot expose query-string values. This does not
  control platform ingress or database logging.

### Verification and observed limitations

- Backend tests: `backend/.venv/Scripts/python.exe -m pytest` — 81 passed on
  Windows/Python 3.14.10. The system Python did not have pytest installed; this
  is why the repository virtual environment was used.
- Frontend checks: `npm run lint`, `npm run typecheck`, and `npm run build` all
  passed. Python `compileall` and `git diff --check` passed (Git reported only
  existing LF-to-CRLF normalization warnings).
- Migration `0007 -> 0008` was applied online with Alembic to the pre-existing
  disposable PostgreSQL 18 restore database, including a prior conversation.
  Downgrade to `0007` removed only the audit table and preserved the conversation;
  re-upgrade created the table, accepted a started-to-completed audit lifecycle,
  and retained the conversation. A custom-format dump restored into a second
  disposable DB with revision `0008_operator_audit`, one audit row, and one
  conversation. The database was using `ssl=off` and the `postgres` superuser;
  this does not verify a secure role/TLS deployment. Backup encryption and
  recovery objectives were not tested.
- PostgreSQL configuration inspection returned `SHOW ssl = off`, current-session
  `pg_stat_ssl.ssl = false`, and current role `postgres` with superuser/create-role/
  create-database privileges. These are facts about the disposable test instance,
  not a target deployment assessment.
- No production database or cloud account is configured. Compose initializes
  the local database with a bootstrap superuser and does not provision separate
  app, cleanup, and migration roles. Operator audit rows are in the same
  database and can be modified by the app's database role; they are not
  tamper-resistant. An external append-only audit sink and narrower grants are
  deployment requirements.
- No database host/volume encryption, KMS integration, backup target/scheduler,
  backup key lifecycle, or restore SLA is configured in this repository. The
  Phase 4 local dump/restore validated mechanics only. Proposed recovery goals
  (subject to service-owner approval): RPO 15 minutes and RTO 4 hours; daily
  encrypted snapshots retained 35 days plus WAL/PITR where available. None is
  currently achieved or verified.
- Conversation text remains PostgreSQL plaintext. Real patient-data processing
  is disabled. External LLM calls remain disabled. Secure patient documents are
  not implemented. Semantic RAG remains blocked by missing pgvector, a pinned
  local embedding artifact, licensed/curated source snapshots, ingestion
  operations, and retrieval evaluation.
- Indian privacy/data-flow analysis is in `PRIVACY_DATA_FLOWS.md`; it is an
  engineering inventory, not a legal-compliance opinion. Applicable laws,
  phased commencement, incident duties, contracts, and retention need counsel
  and deployment-owner review before real patient data is used.

### Deployment blockers

1. Provision PostgreSQL with verified TLS and hostname/CA validation compatible
   with `verify-full`, encrypted storage/backups and documented key ownership;
   run `SHOW ssl`, inspect `pg_stat_ssl`, role flags, grants, network allowlists,
   and provider encryption/key documentation in the target environment.
2. Create separate least-privilege runtime, cleanup, and migration roles. Verify
   runtime cannot create/drop schema objects or mutate audit events, and route
   audit copies to a separately controlled append-only destination.
3. Configure encrypted, access-restricted backups, retention and monitoring;
   set approved RPO/RTO; schedule isolated restores and retain evidence.
4. Configure environment-specific secret management, ingress/network restrictions,
   log retention/redaction, incident response, and independent security review.
5. Complete privacy/legal review and documented approval before enabling any
   identifiable patient data; provider calls remain off until provider contracts,
   retention, residency, safeguards, secrets, and egress have been verified.
6. Complete pgvector/model/source-license/freshness/evaluation provisioning and
   validation before describing any feature as semantic RAG.

Phase 5 has no tested production deployment and no production-readiness claim.

The current Render Blueprint does not prove these controls and does not configure
production database TLS or a separate migration job. Its API must not be deployed
with real patient data as-is.

## Audit findings

- FastAPI uses async SQLAlchemy, PostgreSQL, Alembic, Pydantic settings, cookie sessions, and double-submit CSRF. Patient routes enforce ownership for appointments and medical history; admin routes use an admin dependency.
- The current symptom endpoint is `/api/v1/patient/symptom-check`; it ranks specialties with TF-IDF and Multinomial Naive Bayes trained from synthetic examples, then matches existing doctors. Its UI is `/symptoms` and uses the shared patient workspace.
- Existing doctor search, booking, cancellation, and medical-history screens are available. Booking is already a patient-confirmed POST and cancellation is an explicit POST.
- There is no LLM integration, conversation model, RAG corpus, embedding/vector extension, patient document storage, AI telemetry, or user feedback workflow for AI.
- Compose persists PostgreSQL and doctor photos only. Render docs describe ephemeral uploads and explicitly limit its free setup to testing; no approved external AI data-processing safeguards are configured.
- Backend tests cover existing APIs/security/models/symptom behavior. Frontend scripts are `lint`, `typecheck`, and `build`.

## Implementation plan

1. Preserve existing services and APIs. Add isolated assistant schemas, services, models, routes, and an Alembic migration.
2. Begin with an offline, source-backed assistant: curated public health references, deterministic emergency screening, guarded medical advice, transparent specialty matching to existing doctors, and no external transmission of patient text.
3. Persist patient-owned conversations and messages, expose authenticated CRUD and streaming responses, and apply bounded input and per-user rate limits.
4. Add `/ai-assistant` using the established patient workspace and design tokens, with history, streaming, citations, safety notices, doctor cards, and appointment navigation.
5. Document provider, pgvector, ingestion, privacy, and deployment gates. External LLMs, embeddings, and medical file uploads remain disabled until approved safeguards and durable access-controlled storage exist.
6. Add targeted tests and run the requested backend and frontend checks; report infrastructure-dependent limitations explicitly.

## Current deployment gate

Do not transmit identifiable health information to an external provider or enable medical document uploads until MediSync has a reviewed data-processing agreement, configured provider-specific retention controls, and secure durable patient-scoped object storage. pgvector is also not installed or provisioned in the current Compose configuration; the initial retrieval layer therefore uses curated local references without claiming vector semantics.

## Phase 2 progress (2026-11-03)

### Completed first: Windows test collection and migration validation

- Changed database engine setup to lazy initialization. Importing FastAPI modules, model metadata, and tests that override the database no longer imports the blocked `asyncpg` native extension. Real DB operations still require an allowed asyncpg installation; this change does not substitute a fake driver for runtime operations.
- Added a cookie-presence guard ahead of protected patient/admin/assistant DB dependencies. Missing-session requests now fail with 401 before opening a database session. Session validation itself remains in the existing DB-backed `get_current_user` dependency.
- Full backend suite: 50 passed on Python 3.14.10 after the current changes. Tests retain their endpoint/auth assertions and use fake DB sessions only where already configured or where a DB result is not the behavior under test.
- Created a disposable PostgreSQL 18 cluster under the OS temporary directory. Generated SQL for the exact `0003 -> 0004` Alembic revision range and applied it with PostgreSQL `psql`; verified row creation, orphan user FK rejection, message retention, user delete cascade, migration version update, then applied exact `0004 -> 0003` downgrade SQL and verified both tables were removed and revision returned to `0003`.
- The full-chain offline migration generator cannot render revision `0001` because that existing migration inspects the live database; bounded revision ranges were applied against a minimal predecessor schema. Online Alembic execution with asyncpg remains unavailable under this host's application-control policy. The disposable server was stopped; the command policy rejected removal of its stopped temporary files.

### Not started: privacy- or infrastructure-gated work

- No reviewed provider DPA, provider retention configuration, approved PHI safeguards, server-managed key store, or production privacy approval is configured. External LLM calls remain disabled.
- No validated secure, durable, patient-scoped object store exists. Medical PDF upload/extraction remains disabled.
- pgvector is not provisioned. No approved local embedding model or curated/ingested source corpus has been deployed. Existing public health authority links are references only, not semantic RAG evidence; the assistant must not describe them as retrieved citations.
- Conversation history is persisted and owner-filtered, but the local rules responder does not use prior turns as generative context. The current SSE route chunks a completed local response; it does not stream provider tokens. Distributed rate limiting remains unfinished.

### Completed after the initial validation

- Added migration `0005_ai_usage_feedback`, non-identifying usage records (provider, success, latency, optional token counts only), patient-owned thumbs-up/down ratings, an admin aggregate analytics endpoint, and assistant-response feedback controls in the chat UI.
- Local usage records deliberately leave token counts null. They do not store message text, prompt text, or patient identifiers. Feedback records tie a rating to an assistant message and patient owner; admin reporting returns only aggregate counts.
- Added regression tests for missing authentication, cross-patient conversation lookups, feedback ownership, stream setup failures, safety handling, and token-usage availability.
- Applied Alembic SQL ranges `0003 -> 0004` and `0003 -> 0005` to a disposable PostgreSQL 18 database. Validated FK rejection, cascade behavior, unique feedback, nullable local token usage, and downgrades `0004 -> 0003` and `0005 -> 0004`.
- Backend suite result after this phase: 50 passed. Frontend lint, typecheck, and production build passed.

### Next implementation sequence

1. Validate privacy/vendor controls and key management before enabling a provider or processing PHI externally.
2. Provision pgvector (or another approved vector store) and an approved local embedding runtime. Select and document authoritative source licenses, URLs, owners, review dates, ingestion checksums, and freshness policy; then implement ingestion, retrieval evaluation, and source-bound citations.
3. Add bounded, owner-scoped context construction and streaming cancellation/error semantics, with authentication and cross-patient isolation tests.
4. Validate durable encrypted patient-scoped PDF storage and malware/content controls before implementing document uploads.

### Current local sources

The assistant now uses the Government of India ERSS 112 page for India-specific emergency guidance, plus NHS Conditions A to Z and MedlinePlus Medicines as general reference links. Links were opened on 2026-11-03. The assistant instructs users outside India to use their local emergency number. These are links only; page text is not ingested or cited as retrieved evidence.

## Phase 3 architecture and threat review (2026-11-03)

### Threat boundaries reviewed

- **Patient data:** conversation messages are stored in PostgreSQL; queries constrain conversation IDs by authenticated user before context is read. Context sent to the provider interface is capped by message count and total characters. History API output is capped at the newest 100 messages.
- **External data egress:** no network provider adapter is registered, there is no API key setting, and `AI_EXTERNAL_CALLS_ENABLED=true` is rejected during settings validation. External provider work is not permitted until privacy/legal safeguards are reviewed.
- **Prompt injection:** current local response rules only inspect the current user turn; prior turns are passed as bounded user/assistant context, never as system instructions. The regex screen is limited and must not be treated as a clinical or general-purpose prompt-injection defense for a future model.
- **Evidence integrity:** citations are currently links, not evidence. `rag.py` defines source metadata and passage-checksum/similarity/freshness citation checks; there is no active embedder, vector store, source ingestion job, or corpus.
- **Availability:** rate limiting is now a single PostgreSQL upsert bucket per user and UTC minute, shared among API workers. It is a fixed-window limit (20 requests/minute), not a distributed Redis service; database availability is required for chat.
- **Secrets and logs:** no provider secret exists. AI logs contain failure type/status only, not prompts, message text, patient identifiers, or keys. Conversation retention remains indefinite and needs a product/privacy policy.

### Phase 3 work completed

- Added bounded persisted context loading after conversation ownership verification and a context-aware follow-up behavior in the local responder.
- Added provider protocol/service with provider selection, request/context bounds, timeout, bounded retries for transient failures, output-token contract, and generic 503 handling. Only `local_rules` is registered; config rejects external calls. Local mode has no tokenizer, so token limits and token analytics are not meaningful for it.
- Added a RAG architecture document and contracts for local embedder/vector-store adapters. Citations require a curated source record, current review date, HTTPS canonical URL, exact passage ID, similarity threshold, and matching source/passage checksums. Active retrieval is still gated on pgvector and a pinned local embedding model.
- Added an admin AI analytics page under `/admin/ai` using aggregate API metrics and no patient-level content.
- Replaced the process-local rate map with migration `0006_ai_shared_rate_limits` and an atomic PostgreSQL upsert. Validated increment within a minute and reset at the next minute in a disposable PostgreSQL 18 instance.
- Emergency fallback now says India callers should dial 112 and callers elsewhere should use their local number. The Government of India ERSS source is [112.gov.in](https://112.gov.in/).
- Tests cover bounded context, patient-scoped context lookup, provider retries/timeouts/failures, external-call gate, RAG citation checks, emergency routing, prompt-injection behavior, and shared rate-limit SQL.
- Phase 3 checks: backend `python -m pytest` — 59 passed; frontend `npm run lint`, `npm run typecheck`, and `npm run build` passed; Python compilation and `git diff --check` passed.

### Remaining blockers and risks

- External LLM integration/API secrets remain disabled pending an approved DPA, retention controls, data residency/access assessment, PHI safeguards, key-management review, and end-to-end egress verification.
- A true semantic RAG runtime is not active: pgvector availability, local model provenance/licensing, source snapshots/licenses, ingestion operations, quality evaluation, and rollback are not verified.
- Context is now used by local deterministic follow-up rules, but this is not multi-turn generative reasoning. SSE still chunks a completed local response; provider-token streaming/cancellation is not implemented.
- Full authentication/runtime behavior against PostgreSQL is not verified with the blocked Windows asyncpg extension. Alembic SQL was applied to PostgreSQL; rate-limit query semantics are covered by generated SQL assertion plus matching database upsert validation.
- PDF handling remains disabled until encrypted durable patient-scoped storage and malware/content controls are validated. No production readiness claim is made.

## Phase 4 privacy and hardening (2026-11-04)

### Completed

- Added migration `0007_ai_retention` with a non-null, indexed `expires_at` value.
  Existing conversations were backfilled to `updated_at + 90 days`; the configured
  default is 90 days and new conversation activity slides the expiry forward.
- Added `AI_CONVERSATION_RETENTION_DAYS` and `AI_ANALYTICS_RETENTION_DAYS` settings.
  `backend/app/cleanup_ai_data.py` deletes expired conversations and old aggregate
  usage events. Compose includes a daily cleanup worker. Conversation deletion uses
  existing FK cascades for messages and feedback. Usage events have no patient key,
  so individual deletion cannot remove a user's contribution; the aggregate retention
  policy removes those events by age. Backups may retain deleted records until
  backup rotation.
- Added patient UI for deleting every AI conversation after explicit browser
  confirmation, in addition to per-conversation deletion.
- Added an async-iterator streaming method to the provider contract and service.
  The route relays native provider chunks through SSE, persists the message only on
  successful completion, and reports a generic stream error after output begins.
  The current rules provider has no incremental generator, so it emits one complete
  `response` event tagged `buffered`; it does not fake 32-character token deltas. No
  generative provider is registered, so real-time generated tokens remain unavailable.
- Disabled SQLAlchemy SQL echo in every environment because it can log bind values
  containing patient content. Existing AI logs report only failure class/status and
  do not include message text, user IDs, or API credentials.
- Added `/health/ready`, which returns 503 on database failure; the API container
  healthcheck now checks readiness. `/health` remains a liveness endpoint.
- Added `AI_PATIENT_DATA_ENABLED=false` as the default. Production settings reject
  enabling AI patient-data processing until privacy/security approval; chat, streaming,
  and feedback routes return 503 unless explicitly enabled in a non-production
  environment. Conversation read/delete routes remain available for patient access
  and deletion.
- Audited session cookies (HttpOnly, SameSite=Lax, configured Secure in production),
  double-submit CSRF plus strict Origin validation for writes, hashed DB session
  tokens, configured session expiry, ownership-scoped AI queries, admin dependency,
  and doctor-photo file routing. There is no patient document upload route or patient
  file store. Expired auth-session rows are removed when used; a global session
  cleanup job is not configured.
- PostgreSQL 18 disposable-cluster verification: bounded Alembic upgrade `0003 ->
  0004 -> head` completed at `0007_ai_retention`; a pre-existing conversation was
  backfilled to a future expiry. Deleting an owned conversation removed its messages
  and feedback. Expiry SQL removed an expired row. Downgrade `0007 -> 0006` completed
  and returned the revision to `0006_ai_shared_rate_limits`.
- PostgreSQL concurrency check ran 40 atomic upserts from 8 concurrent worker
  processes; all 40 increments were preserved. Moving the stored bucket to the prior
  minute caused the next request to reset count to 1.
- Ran `pg_dump -Fc` and restored into a separate disposable PostgreSQL database;
  restored Alembic revision and expected conversation row were verified. This tests
  the mechanics only; it is not a configured production backup service or a restore
  SLA.

### Phase 4 verification

- Final Phase 4 backend suite: `python -m pytest` — 75 passed; Python `compileall`
  passed. Frontend `npm run lint`, `npm run typecheck`, and `npm run build` all passed.
  `git diff --check` passed with only the repository's existing CRLF normalization
  warnings.
- The database checks above used real PostgreSQL 18 binaries on a disposable local
  cluster; no production database was accessed. The disposable server has been
  stopped. Test dump and data files remain in the OS temporary directory.
- No Docker command, pgvector extension, local embedding library/model artifact,
  source corpus or source licensing record is present. No pgvector migration, fake
  embedder, fabricated evidence, or unapproved model download was added. Active RAG,
  embedding/retrieval evaluation, and passage-citation end-to-end tests remain blocked.

### Security risks and deployment blockers

- Conversation text is stored as ordinary PostgreSQL text. The repository does not
  implement database volume encryption, field-level encryption, managed key rotation,
  or an operator access audit. Real patient data must remain disabled until host and
  database encryption, access controls, privacy review, and incident procedures are
  verified.
- Provider calls remain disabled by a settings validator. There is no external secret
  or provider adapter. The privacy gate still requires approved data-processing terms,
  provider retention/residency and access review, managed secrets, and verified egress
  controls.
- RAG requires a provisioned/validated pgvector-enabled PostgreSQL image, a pinned
  local model with provenance/license/checksum and a deployment artifact, an approved
  authoritative source corpus with rights/review metadata, ingestion/freshness
  operations, retrieval evaluation cases/thresholds, and rollback procedures.
- Production backups need an encrypted target, secret/key management, schedule,
  retention policy, access monitoring, and tested recovery objectives. The local
  backup/restore check does not verify any deployed storage or key-management setup.
- A supported streaming LLM adapter and end-to-end cancellation/error tests are still
  needed before calling responses real-time. PDF uploads remain out of scope until secure,
  durable patient-scoped storage and content scanning are verified.
- No production-readiness or clinical-validation claim is made.
