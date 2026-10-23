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
  `.env.example` templates belong in source control.
- Replace all example placeholders with local values. The backend requires
  `DATABASE_URL` and does not supply fallback database credentials.
- Use HTTPS and a production-grade secrets manager for deployments.
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
- No CI/CD or deployment manifests are included.
