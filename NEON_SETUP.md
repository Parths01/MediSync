# Neon setup

## Provisioned state

The repository is linked to the specified Neon project and its `production`
branch. Postgres is Neon's built-in service; no Neon Auth, Data API, Functions,
Object Storage, or AI Gateway were enabled. The existing MediSync cookie/session
authentication and SQLAlchemy/asyncpg backend remain in use.

`neon deploy` completed after browser authentication. Neon reported that the
branch already matched `neon.ts` and pulled `DATABASE_URL`,
`DATABASE_URL_UNPOOLED`, and `NEON_BRANCH` into the ignored root `.env.local`.
That file contains Neon owner connection strings; do not use them as application
runtime credentials or commit them.

The empty branch was provisioned with three separate, non-superuser database
roles:

- `medisync_runtime`: pooled application URL; table DML and sequence use, no
  schema `CREATE` privilege.
- `medisync_migrator`: direct, unpooled URL; schema `CREATE` and ownership of
  objects created by Alembic.
- `medisync_cleanup`: pooled URL; deletion on expiry-managed tables and `SELECT`
  only on the expiry predicate columns.

Generated role URLs are stored only in ignored `backend/.env.neon`. Do not copy
this file into source control. Its AI gates remain false. The Alembic migrations
were applied through `0008_operator_audit` using the direct migration URL with
`APP_ENV=production`, `SESSION_COOKIE_SECURE=true`, and TLS verification.

## PostgreSQL driver and TLS

The existing async SQLAlchemy plus `asyncpg` driver was retained. The Neon
application URL is pooled; migration URL is direct. Neon URLs include libpq-style
`sslmode` and `channel_binding` query options that SQLAlchemy's asyncpg dialect
passes through as unsupported arguments, so `backend/app/db_urls.py` removes
those two URL options. TLS is instead enforced by the existing explicit
`verify-full` SSL context, which requires trusted certificate verification and
hostname checking. Runtime, migration, and cleanup connections were exercised
with TLS 1.3 and `TLS_AES_256_GCM_SHA384`.

## Local commands

Run the API from `backend/` using the separate local environment file:

```powershell
python -m dotenv -f .env.neon run -- python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Run a controlled migration operation with the migration URL (never as API
startup):

```powershell
$env:APP_ENV = "production"
$env:SESSION_COOKIE_SECURE = "true"
python -m dotenv -f .env.neon run -- python init_db.py
Remove-Item Env:APP_ENV,Env:SESSION_COOKIE_SECURE -ErrorAction SilentlyContinue
```

The frontend remains in `frontend/`; run `npm run build` there. For the Vercel
Services deployment, configure backend runtime secrets in Vercel's secret
manager; do not upload root `.env.local` or the migration URL. See
[`VERCEL_DEPLOYMENT.md`](./VERCEL_DEPLOYMENT.md) for the required Vercel
environment variables. No Vercel deployment or Vercel environment setup was
performed as part of this Neon setup.

## Verification

- Both Neon pooled and direct URLs connected with `verify-full`; direct TLS
  probes observed TLS 1.3 and the cipher noted above.
- Alembic head is `0008_operator_audit`; the fresh branch has 14 public tables.
- All three roles log in as non-superusers. Verified privilege checks showed no
  runtime schema `CREATE`, migration schema `CREATE`, cleanup expiry-column
  `SELECT` and `DELETE`, and no cleanup full-table `SELECT`.
- FastAPI `/health` and `/health/ready` returned 200 using the runtime role;
  `/api/v1/doctors` returned 200 with zero records.
- Next.js production server served `/` and `/doctors` with 200.
- Backend: 90 pytest tests passed and `compileall` passed. Frontend lint,
  typecheck, and Vercel-mode production build passed.

No patient records were read or created. External LLM calls and AI patient-data
processing remain disabled. This is not a Vercel deployment or a production
readiness assertion.
