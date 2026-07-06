# SCOPE_LOCK.md

Generated: 2026-07-06 13:42:37 UTC

## SCOPE LOCK: PHASE 0 ONLY

This workspace is authorized for **Phase 0 Source Lock only**: source indexing, classification, contradiction preservation, and completion reporting.

## Forbidden build areas (DO NOT IMPLEMENT)

- Kernel
- Memory
- Router
- Validation
- Audit
- Workers
- Skills
- Recovery
- UI (OS control surface)
- Controlled Live Operation

## Folder discipline
- Source folder is READ-ONLY. Sources are never modified.
- Phase 0 artifacts are written ONLY inside the approved workspace root: `/app/NRG_Agent_OS_Phase0_SourceLock`

## Exit condition
Phase 0 ends when the operator accepts the Completion Report. The system then enters WAIT mode and takes no further action until commanded.