---
name: file-dedupe
description: Find exact duplicate files across all cataloged drives using staged hashing (size, partial hash, full SHA-256), pick keepers, and quarantine the rest - never delete. Fourth stage of the file-org pipeline. Use when the user wants to deduplicate, find copies, or reclaim space.
---

# Deduplication

Finds byte-identical duplicates across every drive in the catalog. Cheap by
design: only files that share a size with another file get hashed, only
files that also share a 64 KB head-hash get fully hashed. Hashes are stored
in the catalog, so re-runs never re-hash unchanged files.

## Hard safety rules

- **Nothing is ever deleted.** "Removing" a duplicate means moving it into
  `<drive-root>/_Quarantine_Duplicates/<original relative path>` on the same
  drive (fast rename, no data copied). The user empties quarantine manually
  once they've lived with the result.
- **Files inside units are exempt.** A DLL duplicated across two app
  installs is *supposed* to exist twice. Unit-internal files are skipped
  entirely.
- **Apply requires an approved plan.** Generate the plan, show the user the
  summary (and the plan file for spot-checks), get a yes, then apply. Every
  applied move is journaled and reversible with `--undo`.

## Usage

```bash
# 1. Hash candidates and build duplicate groups (read-only w.r.t. disk):
python3 scripts/dedupe.py --db ~/file-org/catalog.db scan

# 2. Write a keeper/quarantine plan and print the summary:
python3 scripts/dedupe.py --db ... plan --out ~/file-org/dedupe-plan.csv

# 3. After user approval — quarantine the losers (journaled):
python3 scripts/dedupe.py --db ... apply --plan ~/file-org/dedupe-plan.csv \
    --journal ~/file-org/dedupe-journal.jsonl

# Roll back if needed:
python3 scripts/dedupe.py --db ... undo --journal ~/file-org/dedupe-journal.jsonl
```

Options: `--min-size BYTES` (default 1 MB — tiny files rarely pay for their
hashing cost; use 1 to catch everything), `--category X` to limit to e.g.
`video` or `backup` first.

## Keeper heuristics (per duplicate group)

Highest score wins; the plan file shows the reason so the user can override
by editing the CSV before `apply`:

1. Copy that already lives in an organized-looking path (not `Downloads`,
   not `backup`-categorized, fewer `Copy of`/`(1)` markers in the path).
2. Shallower path on the drive with the most free space.
3. Oldest mtime (originals usually predate copies).

## Workflow

1. `scan`, then `plan`, then show the user: number of groups, reclaimable
   bytes, top 20 largest groups.
2. Let them adjust (edit CSV rows from `quarantine` to `keep`, or restrict
   with `--category`), then `apply`.
3. Re-run `storage-report` so they see the reclaimed space.
