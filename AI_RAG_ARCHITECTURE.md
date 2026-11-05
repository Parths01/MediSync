# MediSync RAG architecture (Phase 3)

## Data path

1. An administrator proposes a source with publisher, canonical HTTPS URL, jurisdiction, license/usage basis, version, published/review date, fetched date, and document checksum.
2. An ingestion job fetches only allowlisted official sources, rejects redirects outside the approved host, stores raw snapshots and checksums, extracts text, and splits it into stable passage IDs with offsets and passage checksums.
3. A local embedding runtime creates versioned embeddings. PostgreSQL/pgvector stores vectors beside source/passage metadata. Embedding model/version and dimensions are fixed per index generation.
4. At request time, the independently run emergency screen executes first. For non-emergency requests, a bounded query is embedded locally; retrieval filters to approved, current passages and returns a small top-k result set.
5. The answer layer receives passages as untrusted evidence, never as instructions. User text and retrieved text remain separate. The model cannot invent source identifiers: citations are built server-side from the exact retrieved passage IDs and verified source registry.
6. Citations are suppressed when the source is unapproved/stale, the passage checksum differs, retrieval score is below the evaluated threshold, or evidence is empty. The answer then says that the available reference material does not support an answer.

## Privacy and safety boundaries

- No external embedding or LLM provider is registered. Patient text must remain on the MediSync-controlled host until the vendor, DPA, retention, residency, access, and PHI processing review is approved.
- Only a local embedding model should be enabled initially. Model downloads are deployment artifacts and must be pinned, checksummed, scanned, and tested before release.
- The emergency screen runs before retrieval/generation; emergency responses bypass the model.
- Retrieved passages are citations, not clinical authorization. No diagnosis, prescriptions, dosage advice, or autonomous appointment actions are allowed.

## Implementation state

`backend/app/services/rag.py` defines embedder/vector-store interfaces and checks passage IDs, similarity, source approval, HTTPS URLs, review freshness, and passage checksums before producing passage-level citations. No production adapter, source corpus, pgvector migration, or embedding runtime is active. Current assistant links are not RAG evidence. Activating retrieval is blocked until pgvector/local model infrastructure, source licensing/ownership, refresh operations, evaluation data, and rollback are provisioned and reviewed.

## Phase 4 deployment verification (2026-11-04)

- Local inspection found PostgreSQL 18 server/client binaries but no Docker command,
  pgvector extension files, installed embedding package, or local embedding model
  artifact. No network-downloaded model or unreviewed corpus was introduced. Semantic
  ingestion, retrieval, and citation evaluation remain blocked.
- External LLM calls remain rejected by configuration. The provider contract and
  service expose asynchronous iterators, and the SSE route relays native chunks from
  a provider adapter. No generative adapter is registered; the local rules provider
  sends one complete `response` event and marks `delivery_mode` as `buffered`.
- `AI_PATIENT_DATA_ENABLED` defaults to false; production configuration cannot enable
  patient-data processing until the privacy/security gate is reviewed. Patient chat,
  stream, and feedback writes are unavailable unless enabled in non-production.
- Existing assistant URLs remain general links, not retrieved evidence. Passage
  citations must be generated only from verified source and passage records.
- Do not enable real patient data until host/database encryption, credential and
  operator access controls, backup retention, audit obligations, and privacy review
  are verified. Conversation content is stored in ordinary PostgreSQL text fields;
  application-level encryption is not implemented.

## Phase 5 infrastructure readiness review (2026-11-04)

### Readiness result: not provisioned

This repository and local environment do not contain the pieces required to claim
semantic RAG readiness:

- **PostgreSQL/pgvector:** disposable PostgreSQL 18 is available, but the pgvector
  extension binaries are not installed. No pgvector extension has been created,
  no vector schema/index exists, and no vector query was run. Validate a candidate
  image before adoption with `SELECT name, default_version, installed_version
  FROM pg_available_extensions WHERE name = 'vector';`, then `CREATE EXTENSION
  vector;`, `SELECT extversion FROM pg_extension WHERE extname='vector';` and an
  insert/query smoke test using the final model dimensions. Pin the PostgreSQL
  image and extension version; plan extension upgrades and backup/restore tests.
- **Embedding model:** there is no local embedding runtime/package or model
  artifact. Do not substitute network embeddings. Select a model whose license,
  source, checksum, version, dimension, supported language coverage, CPU/GPU
  runtime, memory needs and update policy are reviewed; package it in a controlled
  offline artifact. Validate startup with outbound network denied.
- **Sources and licensing:** existing Government of India/NHS/MedlinePlus URLs
  are informational links only. There are no fetched snapshots, source rights or
  license records, allowlist owner, parser validation, stable passage IDs, or
  freshness job. Select official sources and confirm reuse terms before ingestion.
- **Evaluation:** there is no retrieval corpus, labeled query set, relevance
  adjudication, citation entailment check, stale-source test corpus, or measured
  acceptance threshold. Build an expert-reviewed non-patient test set and report
  retrieval recall/precision, citation correctness, abstention and stale-source
  rejection before enabling answers.
- **Security:** no index encryption/key management or restricted ingestion/admin
  role has been deployed. Treat fetched HTML/PDF and all passages as untrusted
  data. No patient query may reach an external embedder.

### Activation gates

1. Provision and pin a supported PostgreSQL+pgvector image in a disposable
   environment. Confirm `vector` extension version, configured dimensions,
   permissions, backup/restore and migration rollback.
2. Provision a versioned local embedding model artifact with license/provenance,
   checksum, resource profile and offline startup validation.
3. Approve source host, reuse license, jurisdiction, owner, fetch cadence, last
   reviewed date, publication/version metadata, retention and removal procedure.
4. Implement ingestion with allowlisted HTTPS origins, redirect validation,
   content-type/size limits, checksums, parser isolation, stable passage IDs,
   freshness tracking, idempotency, and rollback to prior index generation.
5. Evaluate semantic retrieval and citation construction against expert-reviewed
   test cases, including unsupported questions, stale content, prompt injection in
   retrieved passages, duplicate text, source deletion, and exact passage checksums.
6. Keep emergency detection ahead of embedding/retrieval/generation. Only return
   citations from registry rows plus exact retrieved passage IDs; never let a
   generated model invent citation metadata.

No activation gate was completed as part of Phase 5; no semantic retrieval or
medical-evidence generation is represented as implemented.
