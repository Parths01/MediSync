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
| Tests | pytest, pytest-asyncio, httpx | Backend model, security, API, heuristic, and symptom-model tests; frontend lint, typecheck, and production build |

The symptom recommender is now a machine-learning prototype trained only on
synthetic examples. It has not been clinically validated and is not medical
advice or a diagnosis. Admin insights remain unvalidated heuristics.

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
docker compose up --build -d
docker compose ps
```

Set a unique, long `POSTGRES_PASSWORD` and make the password in `DATABASE_URL`
match it (percent-encode reserved URL characters). Compose starts PostgreSQL,
applies Alembic migrations, and then starts the API and frontend. Open
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

### Deploy with Render

The root [`render.yaml`](./render.yaml) Blueprint defines the API, frontend,
managed PostgreSQL database, and persistent doctor-photo disk. In Render, create
a new Blueprint and connect this repository. During the first sync, provide
`FRONTEND_URL` as the frontend's HTTPS origin and `NEXT_PUBLIC_API_URL` as the
API's HTTPS origin (for example, `https://medisync-frontend.onrender.com` and
`https://medisync-api.onrender.com`, without a trailing slash). If Render
assigns different service URLs, use the actual URLs shown in the dashboard.

The Blueprint uses paid web-service plans because Render persistent disks are
not available on free web services; it also creates a paid PostgreSQL instance.
Review current Render pricing before syncing. The API applies database
migrations as a pre-deploy step and keeps uploaded photos on its persistent
disk. This repository has not been deployed to Render.

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

Apply PostgreSQL migrations, create the first administrator, and start the API:

```powershell
python init_db.py
python -m app.create_admin --name "Admin User" --email "admin@example.com" --dob "1990-01-01" --gender Other --contact "0000000000"
python -m uvicorn app.main:app --reload
```

The administrator command prompts for a password without echoing it, requires
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
  hosting provider's secret manager. Configure `FRONTEND_URL` to the exact
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
