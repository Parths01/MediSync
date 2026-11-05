# MediSync

MediSync uses a Next.js frontend, FastAPI backend, and PostgreSQL database. It
implements patient and administrator workflows, including authentication,
appointments, medical history, contact and feedback, doctor management, symptom
recommendations, and administrative heuristic insights.

## Current architecture

| Area | Implementation | Current scope |
| --- | --- | --- |
| Modern frontend | Next.js, React, TypeScript | Public directory, authentication, patient workspace, and administrator workflows |
| Modern API | FastAPI, SQLAlchemy async, PostgreSQL | Authentication, patient and admin workflows, doctor directory and photo uploads, symptom recommendations, and heuristic insights |
| Symptom prototype | scikit-learn TF-IDF and Multinomial Naive Bayes | Specialty rankings trained on a small synthetic dataset; demo only, not clinically validated |
| AI assistant | Authenticated patient-owned conversations, bounded local context, provider interface, local safety rules, PostgreSQL shared rate limit, usage analytics | External providers and active vector retrieval remain disabled pending privacy and infrastructure gates |
| Tests | pytest, pytest-asyncio, httpx | Backend model, security, API, heuristic, and symptom-model tests; frontend lint, typecheck, and production build |

The symptom recommender is now a machine-learning prototype trained only on
synthetic examples. It has not been clinically validated and is not medical
advice or a diagnosis. Admin insights remain unvalidated heuristics.

## AI health assistant status

`/ai-assistant` provides patient-authenticated chat, conversation history, buffered
responses over an SSE transport, basic emergency and prescription/diagnosis safeguards, links to public
health authority pages, and links into the existing doctor and appointment flows.
Conversation messages are stored in PostgreSQL and scoped to the signed-in patient.
Apply Alembic migrations through `0008_operator_audit` before using this feature.

The backend creates its SQLAlchemy async engine at first database use. This keeps
application imports and tests that replace database dependencies from loading
asyncpg's native Windows extension at collection time. It does not remove the
asyncpg runtime requirement for PostgreSQL operations. Run tests from `backend/`
with the project's environment activated (`python -m pytest`).

Migration `0005_ai_usage_feedback` adds privacy-minimized request metrics and
patient ratings. Migration `0006_ai_shared_rate_limits` adds a shared PostgreSQL
fixed-window rate limiter. The `/admin/ai` page exposes aggregate counts and latency; local
token usage is reported as unavailable. Usage events omit patient IDs and message
content. Feedback can only be submitted for assistant messages in the patient's
own conversations.

Migration `0007_ai_retention` adds conversation expiry. The default retention is 90
days after the latest conversation activity (`AI_CONVERSATION_RETENTION_DAYS`), and
aggregate usage events are retained for 365 days by default
(`AI_ANALYTICS_RETENTION_DAYS`). The Compose `ai-cleanup` worker runs daily. Patient
deletion removes conversations, messages, and linked feedback through database
cascades. Usage records are aggregate and contain no patient key, so an individual
deletion cannot select a person's metrics; those records expire under the aggregate
retention policy. Existing backups retain deleted rows until their own retention and
rotation policy removes them.

The current responder is a local rules-based prototype, not a configured LLM. The
SSE endpoint supports provider-native async chunks, but the registered rules provider
delivers one complete buffered response; it does not stream model tokens. AI patient
data processing is disabled by default (`AI_PATIENT_DATA_ENABLED=false`), and production
startup rejects enabling it before privacy/security approval. Provider calls are disabled
in settings and startup rejects enabling them before privacy approval. Source links are curated
authority landing pages; the app does not ingest or semantically index source
documents, and citations do not imply that specific page content was retrieved.
The India emergency fallback points to Government of India ERSS 112 guidance; outside
India the response instructs patients to call their local emergency number.
The ML symptom checker remains experimental and separate. AI document uploads,
external provider calls, embeddings, and pgvector are not enabled. Do not send
identifiable patient data to an external model until privacy review, provider
retention controls, and approved data-processing safeguards are in place. Do not
use the free Render setup for real patient information; uploads are not configured
as durable patient-scoped storage.

## Phase 4 operations

- `/health` is a liveness check; `/health/ready` checks PostgreSQL and is used by the
  API container health check.
- Run `python -m app.cleanup_ai_data` from `backend/` for a one-shot retention cleanup.
  Compose runs it once daily in the `ai-cleanup` worker. Production deployments must
  use an equivalent monitored scheduler and alert on failures.
- Take PostgreSQL backups using the hosting platform's encrypted backup service or
  `pg_dump -Fc`. Verify restore into an isolated database with `pg_restore` and run
  schema and migration checks before relying on backups. A disposable PostgreSQL 18
  dump and restore was exercised for the Phase 4 migration; this repository does not
  configure a production backup target, encryption key management, restore SLA, or
  scheduled backup service.
- Do not enable identifiable patient data until encryption at rest, backup retention,
  operator access, incident response, and applicable privacy review are verified.
  This repository does not implement field-level encryption or key rotation.

## Phase 6 deployment readiness

The Phase 6 review is **NO-GO for real patient data**. Local backend and frontend
checks passed, but no staging account, Docker engine, staging PostgreSQL client
access, verified-TLS endpoint, encrypted backup service, separate audit sink, or
monitoring/alert destination was available. Compose runtime behavior, TLS
`verify-full`, least-privilege DB grants, backup restoration, restart/outage
recovery, and alert delivery are therefore unverified. See
[PHASE6_DEPLOYMENT_READINESS.md](./PHASE6_DEPLOYMENT_READINESS.md) for evidence,
deployment blockers, and reproducible staging verification commands.

Keep `AI_PATIENT_DATA_ENABLED=false` and external AI calls disabled. Do not
interpret configuration checks, local tests, or documentation as staging
security evidence.

## Repository layout

```text
backend/app/           FastAPI app, API routes, SQLAlchemy models, and schemas
backend/tests/         Backend API tests
backend/ml/            Synthetic symptom examples and model evaluation command
backend/migrations/    Alembic PostgreSQL migrations
frontend/app/           Next.js routes and global styles
frontend/components/    Shared frontend components
frontend/lib/           Frontend API client
uploads/doctors/        Preserved doctor images, also served by the modern API
```

## Prerequisites

- Python 3.11 and PostgreSQL 15+ for the FastAPI backend. Use Python 3.11 with
  the pinned backend dependencies.
- Node.js 20.9+ and npm for the Next.js frontend.

## Quick start

Start each service in its own PowerShell terminal. The backend must be configured
and running before the frontend can load live doctor data.

### Run the full stack with Docker Compose

Install Docker Desktop with Compose, then run these commands from the repository
root in PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
docker compose up -d db
docker compose exec db psql -U medisync_bootstrap -d medisync
```

The example Compose database creates three `NOLOGIN` roles in
`backend/db-init/00-create-roles.sql`. At the `psql` prompt set a distinct
password for each role interactively, then enable login:

```sql
\password medisync_runtime
ALTER ROLE medisync_runtime LOGIN;
\password medisync_migrator
ALTER ROLE medisync_migrator LOGIN;
\password medisync_cleanup
ALTER ROLE medisync_cleanup LOGIN;
\q
```

Update the three separate URLs in `.env` (`DATABASE_URL`,
`MIGRATION_DATABASE_URL`, and `CLEANUP_DATABASE_URL`) with those role credentials.
Use unique URL-safe secrets and keep `.env` private. The bootstrap `POSTGRES_USER`
is only for database initialization/administration and must not appear in any
service connection URL. The example roles and grants are for a fresh, isolated
development database; do not reset or remove an existing volume to apply them.
Existing databases require a DBA-reviewed ownership/grant migration.

Then start the application services:

```powershell
docker compose up --build -d
docker compose ps
```

Set a unique, long bootstrap `POSTGRES_PASSWORD` and three distinct role
passwords. Compose starts PostgreSQL, runs Alembic in the one-shot `migrate`
service, grants the cleanup role DELETE on the four expiry-managed tables and
SELECT only on their expiry predicate columns, then starts the API and frontend. Open
`http://localhost:3000`; the API docs are at `http://localhost:8000/docs`.
PostgreSQL data and doctor photo uploads use persistent Docker volumes.

Create the first administrator interactively so the password is not stored in
shell history:

```powershell
docker compose exec api python -m app.create_admin --name "Admin User" --email "admin@example.com" --dob "1990-01-01" --gender Other --contact "0000000000"
```

The checked-in `.env.example` values are development placeholders. Do not expose
this local Compose configuration publicly with its default HTTP URLs or
`SESSION_COOKIE_SECURE=false`.

You can also use the Windows helper scripts from the repository root:

```powershell
.\start_project.bat
.\stop_project.bat
```

After completing role setup, `start_project.bat` checks that Docker Desktop is
available and `.env` exists, then builds and starts the Compose services.
`stop_project.bat` stops the
containers without removing the PostgreSQL or doctor-upload volumes. To remove
those volumes intentionally, run `docker compose down --volumes` manually.

### Deploy with Render

The root [`render.yaml`](./render.yaml) Blueprint defines the API, frontend,
managed PostgreSQL database, and free-tier service plans. In Render, create a
new Blueprint and connect this repository. During the first sync, provide
`FRONTEND_URL` as the frontend's HTTPS origin and `NEXT_PUBLIC_API_URL` as the
API's HTTPS origin (for example, `https://medisync-frontend.onrender.com` and
`https://medisync-api.onrender.com`, without a trailing slash). If Render
assigns different service URLs, use the actual URLs shown in the dashboard.

Free web services spin down after 15 minutes without traffic and can take about
a minute to wake up. Their filesystems are ephemeral, so uploaded doctor photos
are lost when the API restarts, redeploys, or spins down. The free PostgreSQL
database is limited to 1 GB and expires 30 days after creation; after a further
14-day grace period, Render deletes it and its data unless you upgrade. The
Blueprint does not configure a separate migration job; run migrations as a
separately credentialed release operation before deploying the API. This free setup is for testing only:
do not use it for production or store real patient information. This repository
has not been deployed to Render.

### 1. Configure and run the backend

From the repository root:

```powershell
Set-Location backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Set `DATABASE_URL` in `backend/.env` to the connection string for your local
PostgreSQL database. Use the actual database, role, and password configured on
your machine; `.env.example` contains placeholders, not usable credentials.

Apply PostgreSQL migrations as a one-off release step, create the first
administrator, and start the API:

```powershell
python init_db.py
python -m app.create_admin --name "Admin User" --email "admin@example.com" --dob "1990-01-01" --gender Other --contact "0000000000"
python -m uvicorn app.main:app --reload
```

For deployments, supply `MIGRATION_DATABASE_URL` only to the one-off migration
job, and a distinct least-privilege `DATABASE_URL` to the running API. Do not
put the migration credential in the API's persistent environment. The
administrator command prompts for a password without echoing it, requires
at least 14 characters, and refuses to add an administrator if one already
exists. It never promotes an existing patient account. The API is at
`http://localhost:8000`; interactive documentation is at
`http://localhost:8000/docs`. `init_db.py` applies the Alembic migration head;
it does not import data.

### Import records from a MySQL source (optional)

The optional importer reads an external MySQL database and previews conflicts
by default. Back up both databases before importing; PostgreSQL is written only
when `--apply` is supplied. It maps users by normalized email, preserves
related IDs where safe, re-hashes plaintext passwords, and requires referenced
doctor photos to exist in `uploads/doctors`. Legacy `DATETIME` values default
to `Asia/Kolkata`; override this with `--datetime-timezone` when needed.

From the backend directory, preview the source first. The password is prompted
securely if `MYSQL_PASSWORD` is not set:

```powershell
python -m app.migrate_mysql --source-database medisync
```

Review the counts and resolve any reported conflicts before applying:

```powershell
python -m app.migrate_mysql --source-database medisync --apply
```

This imports data only and does not change or delete the MySQL source. The
previously imported snapshot records were cleared from local PostgreSQL at the
user's request. The local MySQL server had no live `medisync` database; no
source dataset is currently included in this repository.

Run backend tests from the `backend` directory with:

```powershell
python -m pytest
```

The symptom recommender is trained from synthetic examples when the API starts.
To evaluate it on the separate synthetic holdout examples, run this from
`backend/`:

```powershell
python -m ml.train_symptom_model
```

The holdout score only measures this small synthetic demo dataset; it is not
evidence of clinical accuracy.

### 2. Run the frontend

In a second terminal, from the repository root:

```powershell
Set-Location frontend
npm install
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm run dev
```

The frontend runs at `http://localhost:3000`. `NEXT_PUBLIC_API_URL` defaults to
`http://localhost:8000`; set it in `frontend/.env.local` if the API uses another
URL. Public pages are available at `/` and `/doctors`; patient pages include
`/login`, `/register`, `/dashboard`, `/appointments/new`, `/history`,
`/profile`, `/contact`, and `/symptoms`; administrator pages include `/admin`,
`/admin/doctors`, `/admin/appointments`, `/admin/reports`, `/admin/feedback`,
and `/admin/insights`.

Frontend checks:

```powershell
npm run lint
npm run typecheck
npm run build
```

## Security and configuration notes

- Keep `.env`, `backend/.env`, and `frontend/.env.local` private; only the
  `.env.example` templates belong in source control. The root `.env.example` is
  for Docker Compose.
- Replace all example placeholders with local values. The backend requires
  `DATABASE_URL` and does not supply fallback database credentials.
- For public deployments, set `APP_ENV=production`, configure
  `SESSION_COOKIE_SECURE=true`, use HTTPS, and store database credentials in the
  hosting provider's secret manager. Production settings require
  `DATABASE_SSL_MODE=verify-full`; provide a trusted CA bundle using
  `PGSSLROOTCERT` when needed and verify the database hostname matches the
  certificate. Configure `FRONTEND_URL` to the exact
  browser-facing frontend origin and build the frontend with
  `NEXT_PUBLIC_API_URL` set to the public API URL.
- `backend/Dockerfile` and `frontend/Dockerfile` are production multi-stage
  images. `compose.yaml` is a local full-stack deployment template; it publishes
  local service ports only on `127.0.0.1`. Cloud hosting must provide a
  PostgreSQL database and persistent storage mounted at `/app/uploads/doctors`
  for doctor photos. Run `python init_db.py` as a one-off release/migration step
  before starting API replicas.
- GitHub Actions runs the backend test suite and frontend lint, typecheck, and
  build on pushes and pull requests.
- The legacy PHP/MySQL application and its SQL datasets have been removed.
  Doctor photos remain in `uploads/doctors/` because the modern API serves
  images from that directory.
- This project has not been assessed for healthcare regulatory compliance.
- Phase 5 adds PostgreSQL TLS configuration and a PostgreSQL-backed operator
  audit table, but no production database roles, encrypted backup service,
  key-management service, or tamper-resistant audit sink has been verified. See
  [PRIVACY_DATA_FLOWS.md](./PRIVACY_DATA_FLOWS.md); real patient-data processing
  and external AI calls remain disabled.

## Known limitations

- The previous snapshot import was cleared from PostgreSQL; the schema and
  original administrator account were retained. The optional migration utility
  can import records from a future MySQL source.
- The symptom recommender is a non-clinical ML prototype trained on synthetic
  examples and has not been validated for patient care. Admin appointment
  indicators are also unvalidated heuristics; never use them to deny, delay, or
  prioritize patient care.
- The repository includes container and CI configuration, but has not been
  deployed to a cloud account or assessed for healthcare regulatory compliance.
- The Render Blueprint has no separate migration job, and its managed
  PostgreSQL internal TLS cannot satisfy the app's `verify-full` production
  setting. Do not deploy it with `APP_ENV=production` until an approved
  connection and migration design is configured.
