# Vercel Hobby deployment preparation

## Status and fit

This repository is configured for one Vercel project using the Vercel Services
model. The project root remains the repository root; Vercel builds the existing
`frontend/` Next.js application and `backend/` FastAPI application separately.
The top-level routes send `/api/*` and health paths to FastAPI and all other
paths to Next.js. The browser therefore uses one origin for API calls, cookies,
CSRF and SSE, without copying either application into another directory.

Vercel currently documents Services as Beta on all plans. The Python runtime
supports FastAPI/ASGI and streamed responses, but Vercel Services and this
repository have not been deployed or built with the Vercel CLI here. Check that
Services is available to the target account before proceeding. Hobby Cron is
limited to one run per day with minute-level scheduling variance; the configured
schedule is 03:00 UTC. These platform capabilities do not constitute a deployment
or security verification.

The backend uses Python 3.12 in `backend/.python-version`. Vercel's Python
function bundle limit and the resulting dependency bundle must be validated by
an actual Vercel build. FastAPI's async endpoints, including SSE, run within
Vercel Function duration and concurrency limits. A function timeout may terminate
a long stream or cleanup request. The current local-rules responder is buffered;
its SSE transport does not imply token streaming.

## Vercel project settings

1. Create a project from this repository and keep **Root Directory** at `.` (the
   repository root). Do not point the project at `frontend/`; the root
   `vercel.json` declares both services.
2. Use the current **Services** configuration with the Next.js service rooted
   at `frontend/` and FastAPI service at `backend/`. Vercel should detect Next.js
   and Python from the package metadata/`requirements.txt`; the backend entrypoint
   is `app.main:app`.
3. Keep the project framework/build settings at their detected defaults. Do not
   set a project-wide build command or output directory. The frontend service
   builds with its existing `frontend/package.json`; the backend service uses
   `backend/requirements.txt` and `.python-version`.
4. Assign a stable HTTPS production domain. Set `FRONTEND_URL` to that exact
   origin (scheme and host, no path or trailing slash). Preview origins are
   limited to the exact host Vercel supplies as `VERCEL_URL`; broad `*.vercel.app`
   origins are not allowed.
5. Configure Production and Preview environment variables separately. Preview
   must use a dedicated synthetic-data Neon branch and distinct credentials; do
   not point previews at a production database.
6. Keep automatic production deployment disabled until credentials, migration,
   database TLS, doctor-photo storage and platform access have been reviewed.

If Services is unavailable in the Vercel account, the fallback is two Vercel
projects connected to this same repository: one Root Directory `frontend`, one
Root Directory `backend`, with the backend project configured for FastAPI and
entrypoint `app.main:app`. This still avoids duplicated source code, but the
current host-only CSRF cookie and same-origin assumptions make a cross-origin
split unsupported without additional cookie-domain/security work. Do not use
that fallback for authenticated workflows until cross-origin behavior is
implemented and tested.

## Environment variables

Set the following in Vercel **Project Settings → Environment Variables**. Use
the secret manager UI or another approved secret-management path; never commit
values or paste them into logs.

| Variable | Production value | Preview value |
| --- | --- | --- |
| `APP_ENV` | `production` | `production` |
| `DATABASE_URL` | Neon pooled connection URL for `medisync_runtime` | Pooled URL for an isolated synthetic-data branch/runtime role |
| `DATABASE_SSL_MODE` | `verify-full` | `verify-full` |
| `PGSSLROOTCERT` | Unset for a publicly trusted Neon certificate; configure only when an approved CA bundle is shipped and validated | Same rule |
| `SESSION_COOKIE_SECURE` | `true` | `true` |
| `FRONTEND_URL` | Exact production HTTPS origin | Safe stable origin; the exact preview origin is additionally derived from Vercel's `VERCEL_URL` |
| `CLEANUP_DATABASE_URL` | Neon pooled connection URL for the restricted `medisync_cleanup` role | Restricted cleanup role on the synthetic-data branch |
| `CRON_SECRET` | Random header-safe value, at least 16 characters | Separate random value; Vercel Cron only invokes production |
| `AI_PROVIDER` | `local_rules` | `local_rules` |
| `AI_EXTERNAL_CALLS_ENABLED` | `false` | `false` |
| `AI_PATIENT_DATA_ENABLED` | `false` | `false` |

Leave `NEXT_PUBLIC_API_URL` unset for this same-origin Services deployment. The
frontend uses relative API paths in production and `http://localhost:8000` in
local development. `NEXT_PUBLIC_API_URL` is public build-time configuration and
must never contain credentials. Do **not** configure `MIGRATION_DATABASE_URL`
in the Vercel project: only the controlled migration operator/job receives it.

The database URL may contain Neon's documented `sslmode=require` query value;
the application explicitly supplies a TLS context that requires trusted-chain
and hostname validation (`verify-full`). Set `DATABASE_SSL_MODE=verify-full` in
both production and preview. With no explicit CA file, Python uses the host
system CA trust store. A TLS handshake, positive/negative hostname test, and
`pg_stat_ssl` check against the actual Neon branch are required before use.

The three Neon roles are distinct. Use a Neon owner/admin connection only for
initial role provisioning and the controlled migration operation. Provision
`medisync_runtime`, `medisync_migrator`, and `medisync_cleanup` using
`backend/db-init/00-create-roles.sql` as a DBA-reviewed starting point; assign
separate passwords interactively, set LOGIN, and verify grants on the actual
Neon database. `init_db.py` applies only the defined cleanup grants after
migrations. Existing database ownership/grants must be reviewed; never assume
the Compose bootstrap script has provisioned Neon.

## Controlled migration and deployment commands

Migrations are not called from FastAPI startup or the Vercel build. Run the
existing Alembic head as a release operation using the migration role's secret
from the approved secret store. The following PowerShell sequence assumes that
the secret store injected `MIGRATION_DATABASE_URL` into the current process; it
does not print the value:

```powershell
Set-Location backend
$env:APP_ENV = "production"
$env:DATABASE_SSL_MODE = "verify-full"
$env:SESSION_COOKIE_SECURE = "true"
$env:DATABASE_URL = $env:MIGRATION_DATABASE_URL
python init_db.py
Remove-Item Env:DATABASE_URL
```

Do not place a migration credential in Vercel runtime variables. Check that the
migration job completed and validate schema/grants before deploying an API build.
The current migration script also grants cleanup privileges and expects the
`medisync_cleanup` role to exist in production.

From the repository root, after project linking and environment configuration:

```powershell
vercel link
vercel dev -L
vercel build
vercel deploy --prod
```

These are operator-run commands; this change does not deploy or provision cloud
resources. Run the migration before `vercel deploy --prod`. `vercel dev -L`
requires local frontend/backend dependencies and a configured test database.
After deployment, check `/health`, `/health/ready`, authentication and CSRF,
doctor/appointment flows, an SSE response, unauthorized and authorized cleanup
requests, and the Cron Jobs dashboard/logs. Do not use real patient information
for these checks.

## Cleanup Cron

`vercel.json` schedules `GET /api/cron/cleanup` daily. The endpoint requires an
exact `Authorization: Bearer <CRON_SECRET>` header and fails closed if the secret
or `CLEANUP_DATABASE_URL` is absent. It creates an async engine with
`DATABASE_SSL_MODE` verification and the separate cleanup role; it does not use
the API runtime role to delete data. Vercel sends `CRON_SECRET` in the
authorization header for configured Cron jobs. The cleanup is transactional and
idempotent for expired rows, but actual function timeout behavior, Cron delivery,
and cleanup grants have not been tested on Vercel/Neon.

## Known blockers and security limits

### Local verification completed

- Backend: `python -m pytest -q` — **89 passed**; Python `compileall` passed.
- Frontend: `npm run lint`, `npm run typecheck`, and `npm run build` passed.
  Production build passed both with `VERCEL` unset (existing Docker standalone
  mode) and with `VERCEL=1` (Vercel Next runtime mode).
- The Vercel configuration parses as JSON and was structurally reviewed;
  `git diff --check` passed.
- Vercel CLI, Docker CLI, `psql`, Vercel credentials and Neon credentials were
  unavailable. No Vercel build, preview, Neon connection, TLS handshake, or
  remote Cron run was executed.

- No Vercel project, Vercel CLI build, Neon branch, role, credential, or TLS
  handshake was available. This is configuration preparation, not verified
  Vercel compatibility or a production deployment.
- Doctor photo uploads and reads use the API's local filesystem at
  `uploads/doctors`. Vercel Function files are not durable writable storage, so
  existing admin photo upload/persistence is not supported by this configuration.
  Provision and test an approved durable object store and adapt the photo service
  before relying on those workflows. Patient PDF upload remains disabled.
- Vercel project variables are project-scoped. The Services model deploys both
  services in one project; verify the platform's service-level environment
  isolation before storing database credentials. The frontend service must not
  reference server secrets, and no secret may use a `NEXT_PUBLIC_` name. If the
  account cannot isolate backend secrets from frontend runtime/build, separate
  project/service deployment needs a reviewed same-site cookie and CSRF design.
- Do not enable patient-data use or external LLM calls. Vercel/Neon terms,
  processing locations, retention, access controls, backups, breach handling,
  and applicable Indian privacy requirements still require organizational review.
- Hobby Cron is once daily and can run within a 59-minute window; this is not a
  precise scheduler or a monitored durable worker. Scale/retention workload,
  Function duration, database connection limits, SSE interruption and alerting
  remain to be tested against real infrastructure.
- No new database migration was required for Vercel routing or Cron. Existing
  migrations remain unchanged.
