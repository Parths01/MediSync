# MediSync privacy and patient-data flow inventory

**Review date:** 2026-11-04. This is an engineering inventory, not legal advice,
an assessment of compliance, or approval to process real patient data.

## Current data paths

| Data | Entry and purpose | Storage / recipients | Retention and deletion |
| --- | --- | --- | --- |
| Account and appointment data | Patient/admin web forms and authenticated API workflows | PostgreSQL; API process; platform/database operators | Existing application behavior; account deletion is not a general self-service workflow |
| Authentication sessions | Session cookie token is hashed before database storage | Browser holds cookie; PostgreSQL holds hash, user and expiry | Configured session expiry; global cleanup deletes expired rows daily |
| AI conversation text | Authenticated patient chat, when explicitly enabled in non-production | PostgreSQL text columns; local rules adapter only; no external provider | Conversation expiry defaults to 90 days since activity; delete conversation or all conversations removes messages and linked feedback by FK cascade; expired rows removed by daily cleanup |
| AI aggregate usage | Chat request outcome, provider label, latency and optional token counts | PostgreSQL, no patient identifier or prompt/message text | Default 365 days, then cleanup removes old rows. Because events have no patient key, a patient's deletion cannot selectively remove their contribution |
| AI feedback | Patient rating for an assistant message | PostgreSQL, linked through message/conversation ownership | Removed with conversation/message cascade; otherwise retained with that conversation |
| Privileged operator audit | Admin route access/action outcome | PostgreSQL `operator_audit_events`; no bodies, prompt, query values or path identifiers | Default 365 days; allowed setting range 180–3650 days; removed by daily cleanup; FK sets actor null after account deletion |
| Doctor profile photos | Admin upload and public doctor directory | Local `uploads/doctors` path / Docker volume in Compose; public doctor image endpoint | No patient-scoped file access. Render free filesystem is ephemeral; this is not suitable for patient documents |
| Patient documents | No implemented route or storage | None | PDF upload and extraction are not implemented |
| External AI / embeddings | No provider adapter enabled; config rejects external calls; no embedding service configured | No external AI recipient currently configured | External transmission remains disabled |
| Backups | No automated backup service/target configured in repository | Phase 4 disposable `pg_dump` was a local verification artifact only | Production backup copies, expiry and deletion propagation are not configured |

Conversation text is stored as ordinary PostgreSQL text. The repository does not
provide field-level encryption, database volume encryption, KMS integration, or
key rotation. TLS configuration enforces `verify-full` when `APP_ENV=production`,
but the target database must actually support and pass certificate/hostname
validation. Local Compose uses a bootstrap superuser and defaults TLS to
`prefer`; it is a development template, not a production profile. Compose now
defines separate runtime, migration and cleanup connection URLs plus role setup
for a fresh isolated database. This wiring and grant sequence have not been
executed with Docker/PostgreSQL in this environment; existing volumes need a
reviewed role/ownership procedure.

## Logs, telemetry, and third parties

- Application AI logs record generic failure class/status and do not intentionally
  log patient prompts, message bodies, IDs, or API keys. SQLAlchemy SQL echo is
  disabled. Uvicorn access logging is disabled in repository Docker launch paths
  to avoid request-line query strings. Hosting ingress, load-balancer, database,
  container-runtime, and backup logs are outside this repository's controls and
  require their own redaction, access, location, alerting, and retention review.
- Admin usage endpoints return aggregate counts and latency. The admin audit
  table includes operator account ID plus route template/action and therefore is
  itself personal data requiring access control and retention.
- No third-party LLM or embedding processor is configured. Hosting, PostgreSQL,
  source-control, email, and observability vendors must be inventoried by the
  deployment owner; this repository cannot establish their contracts or data
  processing terms.
- Patient deletion currently applies to AI conversations/messages/feedback only.
  Usage events are intentionally non-identifying and retained by age. Database
  backups and snapshots can retain rows after live deletion until backup
  expiration; deletion from immutable backups is not represented as immediate.

## Retention and deletion controls

Defaults: auth sessions follow `SESSION_TTL_HOURS` (12 hours); AI conversations
expire 90 days after latest activity; aggregate AI usage expires after 365 days;
operator audit events expire after 365 days (with a 180-day minimum setting).
The Compose cleanup worker executes daily, but there is no independent scheduler
monitor or alert configuration in the repository. Operators must monitor job
failure and verify delete counts without putting row-level identifiers in logs.

Patient-requested AI deletion is available through existing conversation-delete
API/UI workflows. PostgreSQL cascades remove linked messages and ratings. There is
no patient data export/delete workflow for the broader account, appointments, or
medical-history records in this Phase 5 change. Define and validate retention for
each such existing workflow before real patient-data processing.

## India legal and incident-response review points

The Digital Personal Data Protection Act, 2023 defines personal data broadly and
sets obligations around processing, notice/consent and other grounds, security,
breach handling, and data-principal rights. The Act's commencement notification
phases provisions over time; the DPDP Rules, 2025 also have phased effective
dates. As of this review date, a rule scheduled one year after publication is
imminent and other provisions are scheduled 18 months after publication. Counsel
must check the current Gazette notifications, amendments, commencement dates,
entity roles, exemptions, cross-border processing, notices/consent, rights and
grievance requirements before any production processing.

The Information Technology (Reasonable Security Practices and Procedures and
Sensitive Personal Data or Information) Rules, 2011 may be relevant to health and
medical information depending on the entity and processing. Counsel should assess
applicability and interaction with the DPDP framework; do not treat this
repository's controls as satisfying either framework.

CERT-In's 2022 Directions include incident reporting timelines and secure
retention of ICT logs for covered entities. The deployment owner must determine
applicability, log categories, reporting process, log location, and retention
with counsel. The operator audit table alone is not a CERT-In log system and is
not tamper-resistant.

Official references checked for this inventory:

- [Digital Personal Data Protection Act, 2023 (India Code)](https://www.indiacode.nic.in/bitstream/123456789/22037/2/a2023-22.pdf)
- [DPDP Act commencement notification, 13 November 2025 (Gazette)](https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf)
- [DPDP Rules, 2025 and phased commencement (Gazette)](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf)
- [SPDI Rules, 2011 (Gazette)](https://upload.indiacode.nic.in/showfile?actid=AC_CEN_45_76_00001_200021_1517807324077&filename=GSR313E_10511%281%29_0.pdf&type=rule)
- [CERT-In Directions under section 70B](https://www.cert-in.org.in/Directions70B.jsp)

These sources do not amount to a legal applicability determination. Preserve
evidence and obtain India-qualified privacy/security counsel review before
processing real patient information.

## Backup and recovery design (not provisioned)

Proposed targets for service-owner approval, not current guarantees:

- RPO: 15 minutes, requiring continuous WAL/PITR or equivalent managed backup.
- RTO: 4 hours, validated by timed restore exercises.
- Encrypted daily snapshots retained 35 days, plus provider-supported PITR/WAL
  retention sufficient to meet the approved RPO.
- Backup encryption keys managed separately from database credentials, limited
  restore roles, key rotation/revocation process, access alerts, and immutable or
  separately controlled copies. Backups must be encrypted in transit and at rest.
- Restore into isolated network/account; verify PostgreSQL version, migration
  head, row/schema integrity, application readiness and sampled non-sensitive
  invariants before recovery. Do not use copied production data in lower
  environments unless independently de-identified and approved.
- Document deletion propagation through snapshot expiry and recovery procedures.

Example manual mechanics only (the repository does not configure encryption,
keys, storage, retention, or scheduling):

```powershell
pg_dump --format=custom --no-owner --file=medisync.dump $env:DATABASE_URL
createdb medisync_restore_check
pg_restore --no-owner --dbname=$env:RESTORE_DATABASE_URL medisync.dump
psql $env:RESTORE_DATABASE_URL -c 'SELECT version_num FROM alembic_version'
```

Use the host/provider's encrypted backup workflow and secret manager in any
real environment. A local dump/restore proves only command mechanics, not
backup confidentiality or recovery objectives.

## Exact deployment blockers

1. No target PostgreSQL host is available here for TLS, role/grant, network,
   encryption-at-rest, or key-management verification. The local disposable
   cluster reported SSL off and a superuser connection.
2. No separate app/cleanup/migration roles or per-table grants are provisioned.
   Compose is still development-only. Configure all three credentials and verify
   the runtime role cannot create schema or modify audit rows.
3. No append-only external audit sink, production log policy, incident process,
   managed secret store, automated backup target, encryption key service, or
   recovery SLA has been configured or tested.
4. The Render Blueprint has no separate migration job and uses internal managed
   database networking. Render documents that its internal TLS certificates
   are self-signed and do not support `verify-full`; this repository currently
   requires `verify-full` in production. A reviewed connection/hosting design
   that satisfies TLS and hostname verification is needed; do not weaken the
   production gate to make that template start. See [Render's PostgreSQL TLS
   documentation](https://render.com/docs/postgresql-creating-connecting).
5. AI patient data and external providers must stay disabled until independent
   privacy/security review, notices/consent and retention decisions, safeguards,
   and deployment evidence are approved.

### Target-environment validation commands

Run these against the target database through the same network path and role the
application will use. Do not paste connection strings, passwords, certificate
contents, or query output containing user records into tickets/logs.

```sql
SHOW ssl;
SELECT ssl, version, cipher
FROM pg_stat_ssl
WHERE pid = pg_backend_pid();
SELECT current_user, r.rolsuper, r.rolcreaterole, r.rolcreatedb
FROM pg_roles AS r
WHERE r.rolname = current_user;
SELECT grantee, table_schema, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
ORDER BY grantee, table_name, privilege_type;
```

From the backend release environment, set `APP_ENV=production`,
`DATABASE_SSL_MODE=verify-full`, `PGSSLROOTCERT` to the mounted trusted CA path
when required, and use a database hostname present in the server certificate.
Run `python -c "from app.config import get_settings; print(get_settings().database_ssl_mode)"`
to check the loaded mode, then run a database readiness request and inspect
`pg_stat_ssl` for the actual connection. A successful settings parse alone does
not prove TLS. Verify storage encryption, KMS/key ownership, key rotation and
backup encryption in the hosting provider's control plane; PostgreSQL SQL cannot
prove those controls.

Create runtime, migration and cleanup identities through the managed database's
approved role-management process. Give migration DDL privileges only to a
short-lived release job. The Compose initializer grants runtime DML and schema
creation to migration; after upgrade, the migration job grants DELETE on the four
cleanup tables and SELECT only on their expiry predicate columns to the cleanup role. Test expected API reads/writes and explicitly
confirm that runtime cannot create/drop schema objects. This is not yet verified
against PostgreSQL. The API can still update audit rows under its table grants;
an independent append-only audit sink remains a separate deployment/code
requirement.
