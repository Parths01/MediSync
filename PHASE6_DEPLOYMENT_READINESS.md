# Phase 6/7 staging deployment readiness report

## Phase 7 provisioning update (2026-11-05)

### Disposition

**BLOCKED — no staging verification and NO-GO for real patient data.** Available
tools were inspected before changes. Docker/Compose, PostgreSQL clients, cloud
CLIs, Render CLI, staging environment variables, a staging URL/CA, and cloud
credentials/access are unavailable. Local `backend/.env` was checked without
printing values; its endpoint is local/container, `APP_ENV=development`, TLS
defaults to `prefer`, and AI gates are false by default. No connection was made
to an unknown database and no patient data was used.

### Phase 7 status classification

| Requirement | Status | Phase 7 evidence |
| --- | --- | --- |
| Compose credential separation | **PARTIALLY VERIFIED** | Compose now requires independent `DATABASE_URL`, `MIGRATION_DATABASE_URL`, and `CLEANUP_DATABASE_URL`; no fallback aliases them. Role initializer and post-migration scoped grants are implemented, but Docker/PostgreSQL execution and effective credentials are unverified. |
| Production PostgreSQL `verify-full` | **BLOCKED** | App code still requires the mode in production; no staging host, CA or login is available to verify certificate and hostname success/failure. |
| Least-privilege PostgreSQL roles | **PARTIALLY VERIFIED** | Added password-free idempotent `NOLOGIN` role initializer; runtime gets DML, migrator gets schema CREATE, cleanup receives DELETE on four named tables after migrations. Grant logic has unit coverage. Effective DB role attributes/grants and existing-volume behavior are unverified. |
| Separately controlled append-only audit storage | **BLOCKED** | No sink, credentials, infrastructure or integration exists. Current PostgreSQL table is mutable by application role. |
| Encrypted automated backups / retention / keys | **BLOCKED** | No provider, account, KMS/key service, retention policy or restore credentials are available. |
| Compose E2E and migration sequence | **BLOCKED** | Docker unavailable. Only YAML parsing and code-level unit tests are possible here. |
| Restart and database outage recovery | **BLOCKED** | No running Compose services or staging database available. Reproducible synthetic-data checks remain below. |
| Cleanup scheduling | **PARTIALLY VERIFIED** | Cleanup now has a separate connection URL and narrower grants in code/config. Periodic execution, role access, schedule and missed-run handling/alerts are unverified. |
| Monitoring and alert delivery | **BLOCKED** | No central log/metrics destination, alert rules, on-call route or credentials. |
| Render/deployment target | **FAILED for current production configuration** | Render Blueprint sets production but leaves SSL mode at default `prefer`, which violates app startup validation. It also has no release migration job. Security checks were not weakened. A compatible managed container platform/database must be selected and configured. |
| Tests and local checks | **VERIFIED** | Backend suite: 83 passed; `compileall` passed; frontend lint/typecheck/build passed; Compose YAML parsed; `git diff --check` passed with line-ending warnings. Scope is local only, not staging evidence. |

### Repository changes made for Phase 7

- Compose now requires three distinct connection URLs for runtime, migration and
  cleanup. It no longer falls back from the migration URL to the API URL or reuses
  the API URL for cleanup.
- Added `backend/db-init/00-create-roles.sql`. It creates fixed-purpose roles as
  `NOLOGIN`, without placing passwords in SQL or logs; sets runtime DML and
  migration schema privileges; and grants existing objects to the runtime role.
  Operators set each password interactively with `psql \password` and then enable
  login. This avoids embedding role passwords in SQL statements.
- The migration job grants the cleanup role DELETE only on `user_sessions`,
  `ai_conversations`, `ai_usage_events`, and `operator_audit_events` after upgrade.
  It grants SELECT only on those tables' expiry predicate columns. Production
  migration fails if the cleanup role is missing. Unit tests cover exact cleanup
  table/column scope and fail-closed behavior when the role is absent.
- These changes have not been run against PostgreSQL. The role initializer is
  mounted into PostgreSQL's first-initialization directory, so it runs
  automatically only for a new data directory. Existing volumes require a
  reviewed, non-destructive DBA role/ownership process; do not delete a volume to
  force initialization.
- No implementation is claimed for external append-only audit, backup/KMS,
  monitoring or alerting because no infrastructure endpoint exists.

### Better-supported deployment target criteria

The current Render Blueprint is not accepted for production: its internal managed
PostgreSQL path does not satisfy this app's `verify-full` requirement as currently
configured, and its blueprint lacks a separate release migration job. Do not set
`DATABASE_SSL_MODE=require` merely to make it start. Select a managed container
platform with a one-shot/pre-deploy migration job, a managed PostgreSQL endpoint
whose CA and hostname work with asyncpg `verify-full`, a secret manager, encrypted
automated backups/PITR with restore controls, a separately controlled immutable
audit service, and centralized redacted monitoring/alerts. No vendor or account
has been selected or provisioned.

### Access needed to continue

Provide the staging provider/project and authorize access through its approved
CLI/account integration or secret manager (do not paste passwords, private keys,
CA private keys, or raw database URLs into chat). A staging operator must also
make Docker Desktop/Compose available on this host or provide a controlled Linux
runner. Backup/KMS, audit sink, and monitoring admin access must be provisioned
with scoped roles. Once available, use synthetic data only and perform the
verification sequence in this report.

No current Phase 7 staging, TLS, backup, alert or recovery evidence exists.

**Review date:** 2026-11-05 (Asia/Kolkata)  
**Disposition:** **NO-GO for real patient data. Staging deployment not verified.**

This review separates repository checks from controls that require a real staging
environment. No production or patient records were used. AI patient-data processing
and external LLM calls remain disabled.

## Phase 6 baseline evidence (before Phase 7 role wiring)

The following table records Phase 6's baseline review. The Phase 7 update above
is the current status where later repository changes differ.

| Control | Status | Evidence / limitation |
| --- | --- | --- |
| Backend regression suite | **Verified locally** | `backend/.venv/Scripts/python.exe -m pytest`: 81 passed on Windows / Python 3.14.10. This is not a staging integration run. |
| Frontend checks | **Verified locally** | `npm run lint`, `npm run typecheck`, `npm run build` passed. |
| Compose configuration | **Partially verified** | YAML parses. `docker` and `docker-compose` are unavailable, so Compose interpolation, image builds, service dependencies, ports and runtime behavior were not exercised. |
| PostgreSQL migration | **Previously verified on disposable DB; not re-run in Phase 6** | Phase 5 evidence records `0007 → 0008`, rollback/re-upgrade and dump/restore on local PostgreSQL 18. No PostgreSQL client tools or staging URL are available now. |
| PostgreSQL least-privilege roles | **Unverified / blocker** | Compose initializes `POSTGRES_USER` as the database bootstrap owner, and both API and `ai-cleanup` use `DATABASE_URL`. No runtime/cleanup role provisioning is present. The disposable Phase 5 session used `postgres` superuser. |
| PostgreSQL `verify-full` TLS | **Unverified / blocker** | Settings reject production unless `DATABASE_SSL_MODE=verify-full`; asyncpg is configured with the selected SSL mode. No target hostname, CA, staging credentials or DB client is available to establish and inspect a real TLS connection or test bad-CA/hostname rejection. |
| Separate append-only audit storage | **Unverified / unsupported by current infrastructure** | `operator_audit_events` is in the application DB and can be updated/deleted by application credentials. No independent audit sink, WORM store or forwarding integration is configured. |
| Encrypted automated backups | **Unverified / blocker** | No cloud account/backup target/key manager/scheduler is configured. The prior disposable `pg_dump`/restore proves command mechanics only, not encryption, retention, PITR, RPO or RTO. |
| Compose E2E, restart/outage recovery | **Unverified / blocked by Docker absence** | No containers could be built or started; migration ordering, readiness, restart and DB outage behavior were not exercised. |
| Cleanup schedule | **Partially verified** | Code deletes expired rows and Compose declares a daily loop. No container ran; no overdue/failure alert, worker health check or scheduler evidence exists. |
| Monitoring and operational alerts | **Unverified / blocker** | `/health` and `/health/ready` exist; app logging is limited and AI errors omit message text. No metrics exporter, centralized structured-error sink, alert rules, on-call route or dashboard configuration is present. |
| CORS, CSRF, session and authorization | **Partially verified** | Static review: one configured frontend origin, double-submit CSRF plus exact `Origin` check on writes, HttpOnly session cookie, secure cookie required in production, DB-backed session expiry, admin/patient dependencies and API tests. No staging ingress/proxy, browser, cookie or cross-origin test was run. |
| Secrets | **Partially verified** | `.env` files are ignored and `backend/.env` exists locally. Without displaying its values, a sanitized parse classified its DB endpoint as local/container, `APP_ENV=development`, TLS mode default `prefer`, and both AI gates false by default; it is not staging configuration. No `.env` file is tracked and a basic scan found no matching common private-key/cloud-key patterns. No dedicated secret-scanner is configured; provider secret management is unverified. |
| Network exposure | **Partially verified** | Compose publishes DB/API/frontend to `127.0.0.1`; cloud ingress, database allowlists, egress policy, TLS termination and proxy logs are unknown. |
| Patient-data and external-AI gates | **Verified in code/tests, not as a deployment state** | `AI_PATIENT_DATA_ENABLED` defaults false and production rejects enabling it; external calls are rejected by configuration. No AI provider credentials are configured by the repository templates. |

## Deployment audit findings

### Database and migrations

- The Compose database container uses `POSTGRES_USER` as the initial cluster
  owner. Its example runtime URL uses the same account. The API and cleanup worker
  both receive that runtime URL. `MIGRATION_DATABASE_URL` is isolated to the
  one-shot Compose migration service, but falls back to the runtime URL for local
  convenience. This is development scaffolding, not least privilege.
- The API currently writes and updates audit rows, while cleanup deletes them.
  A single API credential therefore cannot be made append-only with ordinary
  table grants. A separately controlled sink needs an adapter and delivery/failure
  semantics; none is implemented.
- Production settings require `verify-full`, but `render.yaml` sets
  `APP_ENV=production` without setting `DATABASE_SSL_MODE`, so it resolves to
  `prefer` and application settings reject startup. The Blueprint also removed
  migration-on-API-start and does not define a separate migration/release job.
  Do not weaken the check to force startup. A target host/database design that
  supports verified TLS and a separately credentialed migration step is required.
- Image bases use moving tags (`python:3.11-slim`, `node:22-alpine`,
  `postgres:16-alpine`); the Docker build also upgrades pip without a version pin.
  This is an image/dependency reproducibility and supply-chain hardening gap.
  CI Actions are referenced by major tags, not immutable commit SHAs; no
  container vulnerability or dependency audit job is defined.

### Authentication, privacy and logging

- CORS is limited to configured `FRONTEND_URL`; writes check CSRF cookie/header
  equality and exact origin. Production requires secure cookies. Validation here
  is code and unit-test evidence only; public ingress/proxy settings are absent.
- SQLAlchemy echo is disabled and AI logs avoid prompt/body/ID/key values.
  Uvicorn access logs are disabled in the Docker paths. Platform, ingress, DB,
  backup and container logs remain deployment-owned and have no verified
  redaction, access policy, location or retention evidence.
- Health checks report liveness and DB readiness, but no alert consumes them.
  The cleanup loop has no health endpoint or overdue-run monitor; a failed daily
  attempt is not wired to an operator notification.
- AI model calls, PHI processing and patient documents remain disabled. No staging
  patient data should be loaded for the following verification procedure.

## Exact prerequisites and reproducible verification

Use a dedicated staging account/project and isolated PostgreSQL database. Populate
only synthetic accounts and appointments. Keep the AI switches false and use no
external provider credentials.

### 1. Provision database identities and verified TLS

Create credentials in the provider's secret manager for separate migration,
runtime, and cleanup roles. The Compose path now accepts distinct connection
URLs and the migration command applies scoped cleanup grants after schema upgrade;
neither has been exercised against a real DB. Confirm the API role cannot
create/drop schema objects and the cleanup role can delete only its four required
tables. Audit-table mutation remains possible while the API writes event
completion state, so it must not be described as immutable.

Configure the DB certificate for the exact staging hostname and mount the trusted
CA bundle into the API and migration containers. Set `APP_ENV=production`,
`DATABASE_SSL_MODE=verify-full`, `PGSSLROOTCERT` to the mounted path, and
`SESSION_COOKIE_SECURE=true`. Never put secrets in the image or frontend build
arguments. Confirm the provider's certificate chain, hostname SAN, encryption at
rest, key ownership and rotation in its control plane.

Connect using the actual application role and run:

```sql
SHOW ssl;
SELECT ssl, version, cipher FROM pg_stat_ssl WHERE pid = pg_backend_pid();
SELECT current_user, rolname, rolsuper, rolcreaterole, rolcreatedb
FROM pg_roles WHERE rolname = current_user;
SELECT grantee, table_schema, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
ORDER BY grantee, table_name, privilege_type;
```

Also verify a connection with the correct CA and hostname succeeds, while an
incorrect CA and a hostname mismatch both fail. A successful settings parse is
not TLS evidence; inspect `pg_stat_ssl` on the connected server session.

### 2. Deploy and exercise Compose using synthetic data

After Docker Desktop is installed and its engine is running, from the repository
root in PowerShell:

```powershell
docker info
docker compose config --quiet
docker compose up --build -d
docker compose ps
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost:8000/health/ready
Invoke-WebRequest http://localhost:3000/
docker compose logs --no-color migrate api frontend ai-cleanup
```

Confirm `migrate` exits successfully before the API starts, the DB/API/frontend
health checks pass, and `ai-cleanup` remains running (it has no health check in
the current Compose file). Verify the resolved Compose config contains no secrets
before sharing diagnostic output.

For recovery checks, create only synthetic records and then exercise:

```powershell
docker compose restart api
Invoke-WebRequest http://localhost:8000/health/ready
docker compose kill -s SIGKILL api
Start-Sleep -Seconds 5
docker compose ps api
Invoke-WebRequest http://localhost:8000/health/ready
docker compose stop db
Invoke-WebRequest http://localhost:8000/health/ready
docker compose start db
docker compose exec api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready')"
docker compose exec ai-cleanup python -m app.cleanup_ai_data
```

Expected: readiness is 503 during DB outage and recovers after PostgreSQL is
healthy; API process restart recovers without data loss; cleanup exits zero and
removes only deliberately expired synthetic fixtures. Also test a migration
failure in a disposable database and confirm API does not start. Compose cleanup
is a 24-hour loop, so validate schedule cadence and missed-run alerting separately.

These commands were not run in this environment because Docker is unavailable.

### 3. Configure backups and restore evidence

Provision the provider's encrypted automated snapshot plus WAL/PITR service.
Approve RPO/RTO, retention, key custody/rotation, restore permissions, and
deletion behavior in backup copies. Restore a recent backup into an isolated
staging account using a restore-only identity. Verify PostgreSQL version,
Alembic revision, expected schema, health checks, and non-sensitive synthetic
invariants. Record the backup timestamp, key identifier (not key value), restore
duration, validation result, and approver. Do not export unencrypted dumps or
copy patient data into a lower environment.

No backup provider, key service, encrypted target, or staging credentials are
available here; actual backup and restore remain blocked.

### 4. Configure privacy-safe monitoring and alerting

Before staging acceptance, provision a redacted structured log sink and alerts
for API readiness/5xx rate, DB connectivity/TLS failures, migration job failure,
cleanup last-success age/failure, backup last-success and restore-test age, and
unexpected external egress. Exclude request/response bodies, query strings,
patient identifiers, credentials, and raw exception messages. Restrict operator
access, define retention/location, test alert delivery to an on-call owner, and
record a synthetic alert drill. None of these destinations or alert rules is
configured in the repository.

## Acceptance decision

Do not enable real patient data or external LLM processing. Required blockers are:

1. Staging account, URL, CA, and credentials for an actual `verify-full` TLS test.
2. Least-privilege runtime/cleanup/migration role design and verified grants.
3. A separately controlled append-only operator audit destination and tested
   delivery/failure behavior.
4. Encrypted automated backup/PITR configuration and an evidenced isolated
   restore against approved RPO/RTO.
5. Docker engine for Compose E2E, restart, outage and cleanup schedule testing.
6. Redacted monitoring/alert destinations and a successful alert drill.
7. Cloud ingress/egress, secret-manager, TLS termination and platform-log review.

This report is not a production-readiness, clinical validation, or regulatory
compliance assertion.
