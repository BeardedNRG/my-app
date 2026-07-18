---
name: file-verify
description: Independent audit of applied file-org operations - confirms every journaled move/quarantine landed intact (existence, size, hash spot-checks), sources are gone, and nothing in the plan was silently skipped. Run after any file-dedupe or file-organize apply step, before the user empties quarantine or deletes anything.
---

# File-Org Verification (the second pair of eyes)

Audits what the apply steps *actually did* against what they *said* they
did, through an independent code path: `verify.py` shares no logic with
`apply_moves.py`/`dedupe.py` — it only reads their journals, the plan, and
the disk.

## Usage

```bash
python3 scripts/verify.py --db ~/file-org/catalog.db \
    --journal ~/file-org/move-journal.jsonl \
    [--plan ~/file-org/move-plan.csv] [--sample 200]
```

Exit code 0 = PASS, 1 = FAIL (details printed). Checks:

1. **Every journal entry landed**: destination exists; for moves, the
   source is gone (a file existing in both places means an interrupted
   copy-delete — flagged, not fatal, but must be resolved).
2. **Sizes match the catalog** for every journaled file.
3. **Hash spot-check**: `--sample N` destinations (default 200, weighted
   toward the largest files) are re-hashed with SHA-256 and compared to
   the catalog's recorded hash where one exists.
4. **Plan coverage** (with `--plan`): every actionable plan row is
   accounted for in the journal — anything silently skipped is listed.

## Workflow

- Run this after EVERY `apply` (moves or quarantine), before telling the
  user the operation succeeded — the verify verdict IS the success report.
- On FAIL: stop. Show the user the failure list. Do not apply anything
  further, do not let quarantine be emptied, and offer `--undo` with the
  same journal.
- For maximum independence, run the verification in a subagent that has
  not seen the apply step's output — give it only the journal, plan, and
  catalog paths and have it report the verdict back.
- After a PASS on a move plan, re-run `drive-inventory` on the affected
  roots so the catalog matches the new layout.
