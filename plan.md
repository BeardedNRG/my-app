# NRG Agent OS — Phase 0 Source Lock Console (Full-Stack) — Plan

## 1. Objectives
- Build a full-stack **Phase 0 Source Lock Console** (FastAPI + React + MongoDB) that ingests the uploaded zip, performs **deep read** (PDF/MD text extraction + LLM summarization), classifies sources by authority/tags/priority, preserves contradictions, and generates **Phase 0 artifacts**.
- Enforce **scope lock**: no Kernel/Memory/Router/Workers/etc.; console is for indexing, analysis, artifact generation, and operator acceptance only.
- Write artifacts only to `/app/NRG_Agent_OS_Phase0_SourceLock`; keep extracted sources mirrored read-only under `/app/sources`.

## 2. Implementation Steps

### Phase 1: Core Workflow POC (Isolation) — ingestion + extraction + 1 LLM call
**User stories (POC)**
1. As an operator, I want to download/unzip the provided bundle so the system can analyze the same files I provided.
2. As an operator, I want text extracted from every PDF/MD so no source is silently skipped.
3. As an operator, I want a deterministic file inventory (path, hash, size) so the source lock is reproducible.
4. As an operator, I want one verified LLM summary output so I know deep analysis works end-to-end.
5. As an operator, I want a clear fail-fast report when a file cannot be parsed so I can fix the bundle.

**Steps**
- Websearch best practices for PDF extraction reliability (pypdf vs pdfplumber) and sha256 hashing patterns.
- Create `test_core.py`:
  - Download zip from provided URL.
  - Extract to `/app/sources/<timestamp_or_fixed>/`.
  - Walk all files; for each `.md` read UTF-8 (fallback latin-1), for each `.pdf` extract text (pdfplumber primary, pypdf fallback).
  - Emit a JSON summary: total files, extracted-text lengths, failures, sha256.
  - Run **one** LLM call via `emergentintegrations` to summarize a selected control packet source and return structured JSON (summary + key_claims).
- Iterate until: 100% files enumerated; extraction succeeds for all (or failures are explicitly listed with reasons); LLM call returns valid structured output.

### Phase 2: V1 App Development (Full-Stack MVP)
**User stories (V1)**
1. As an operator, I want to run ingestion from the UI and see progress so I know when Source Lock is complete.
2. As an operator, I want a searchable Source Index table with authority tier + priority rank so I can navigate quickly.
3. As an operator, I want to open any source and see metadata + extracted text + LLM summary + key claims.
4. As an operator, I want a Contradictions Register that preserves conflicts and shows the resolution rule (Master Build Law wins).
5. As an operator, I want to view/download the generated Phase 0 markdown artifacts from the console.

**Backend (FastAPI + MongoDB)**
- Data model (Mongo):
  - `sources`: path, filename, ext, sha256, size, extracted_text (truncated + full stored), authority_tier, tags[], priority_rank, summary, key_claims[], parse_status.
  - `contradictions`: id, sources_involved[], conflicting_claims, resolution, status=PRESERVED, notes.
  - `runs`: ingestion run status, timestamps, counts, errors.
  - `state`: scope_lock flag, operator_acceptance record.
- Ingestion pipeline (idempotent):
  - Mirror sources to `/app/sources` (do not modify originals).
  - Extract text for all PDFs/MDs.
  - Classify per provided rules:
    - CONTROL_PACKET (highest authority) includes the 9 listed.
    - PRIMARY_ARCHITECTURE, PROCESS_RULES / WAIT_MODE_EVIDENCE / LOCKED_INTENT_SOURCE, CONCEPT_ONLY, ARCHIVE_REFERENCE.
    - Apply explicit tags (UX_INSPIRATION, OPERATOR_COMMUNICATION_REFERENCE, etc.).
    - Apply priority order (1–11) using filename mapping + fallbacks.
  - LLM pass: per-source structured output `{summary, key_claims, build_relevance}`.
  - Contradiction pass: compare key_claims across sources, focusing on conflicts vs control packet + Phase-0-only restriction; write preserved entries.
- Artifact generator (writes markdown to `/app/NRG_Agent_OS_Phase0_SourceLock`):
  - `SOURCE_INDEX.md` (all sources, classification, authority, priority, hash, parse status).
  - `SOURCE_PRIORITY.md` (1–11 list + mapping explanation).
  - `CONTRADICTIONS.md` (preserved contradictions + resolution rule).
  - `SCOPE_LOCK.md` (explicit forbidden build areas + Phase 0 boundary).
  - `PHASE0_COMPLETION_REPORT.md` (what was ingested, counts, failures, contradictions count, operator next step).
- API routes (all `/api`):
  - `POST /ingest` (start run), `GET /ingest/status`.
  - `GET /sources`, `GET /sources/:id`.
  - `GET /contradictions`.
  - `GET /artifacts` (list), `GET /artifacts/:name` (render md).
  - `GET /report`.
  - `POST /operator/accept` (records acceptance + freezes state).

**Frontend (React + shadcn UI)**
- Pages:
  - Dashboard: scope-lock banner, ingest button, progress, counts by authority tier.
  - Source Index: table w/ filters (tier, tags, priority), search, status chips.
  - Source Detail: metadata + summary + key claims + extracted text preview (with “show more”).
  - Contradictions: list/table with involved sources + conflicting claims + preserved status.
  - Artifacts: markdown viewer + download.
  - Completion Report: rendered markdown + “Operator Accept” action.

**Conclude Phase 2**
- Run 1 round of end-to-end testing (ingest → browse sources → view contradictions → open artifacts → accept).
- Fix any blocking UX/data-flow issues.

### Phase 3: Hardening, Quality, and Edge Cases
**User stories (Hardening)**
1. As an operator, I want ingestion to be repeatable and not duplicate records when rerun.
2. As an operator, I want clear per-file parse errors so I can remediate unreadable PDFs.
3. As an operator, I want deterministic classification overrides for known filenames so authority is never ambiguous.
4. As an operator, I want large-text handling (truncate + full view) so UI stays responsive.
5. As an operator, I want “freeze after acceptance” so Phase 0 outputs can’t change accidentally.

**Steps**
- Improve ingestion idempotency: upsert by sha256 + path.
- Add safe text storage strategy (preview + full text field or gridfs if needed).
- Improve contradiction detection prompts + heuristics (only flag high-confidence conflicts; always preserve).
- Add export endpoints (download all artifacts as zip).
- Testing agent: 1 full run + regression checks.

### Phase 4: Post-V1 Enhancements (only if requested)
**User stories (Enhancements)**
1. As an operator, I want role-based access or auth if this console is deployed multi-user.
2. As an operator, I want manual reclassification controls with audit trail.
3. As an operator, I want to annotate contradictions with operator notes.
4. As an operator, I want diffing between two ingestion runs.
5. As an operator, I want configurable priority mapping rules.

## 3. Next Actions
1. Implement and run `test_core.py` POC (download/unzip/extract/hash + 1 LLM summary).
2. Lock the filename→authority/tags/priority mapping table (based on the provided control packet + known references).
3. Scaffold FastAPI + Mongo collections + ingestion endpoints.
4. Scaffold React console pages and wire to APIs.
5. Generate artifacts and verify they are written only to `/app/NRG_Agent_OS_Phase0_SourceLock`.

## 4. Success Criteria
- POC succeeds: all files enumerated; text extracted for each PDF/MD (or explicit failure list); 1 LLM structured summary returns successfully.
- V1 app succeeds: operator can ingest, browse sources, view summaries/key claims, view contradictions, and view/download all 5 artifacts.
- Artifacts are complete, deterministic, and stored only in the approved workspace root.
- Scope lock is enforced in UI and report; no out-of-scope system components are implemented.
- Operator acceptance freezes Phase 0 state and the console enters WAIT mode.