---
name: file-org
description: Orchestrates the full drive-organization pipeline - inventory, classify, dedupe, report, organize. Use when the user wants to understand, clean up, deduplicate, or reorganize one or more drives/folders, or asks "what's on this drive?" / "help me organize my files".
---

# File Organization Pipeline (Orchestrator)

You are coordinating a multi-stage cleanup of one or more drives. Each stage is
its own skill; they all communicate through **one SQLite catalog file** so no
stage ever needs to re-scan the disk.

## The catalog

- Default location: `~/file-org/catalog.db` (create the directory if missing).
- Every script accepts `--db <path>`; always pass the same path to every stage.
- The catalog is the single source of truth: paths, sizes, hashes, categories,
  duplicate groups, and move plans all live in it.

## Pipeline order (do not skip ahead)

1. **Inventory** (`drive-inventory`) — scan every root the user names.
   Nothing else works without this. Re-run after any big change to disk.
2. **Classify** (`file-classify`) — assign every file a category and detect
   atomic *units* (VM folders, git repos, app installs, photo libraries).
   Units are never split apart by later stages.
3. **Report** (`storage-report`) — generate the visual HTML dashboard and show
   it to the user *before* proposing changes. Seeing what they have is half
   the job.
4. **Dedupe** (`file-dedupe`) — find exact duplicates, propose keepers,
   quarantine (never delete) the rest only after user approval.
5. **Organize** (`file-organize`) — design the target layout with the user,
   generate a move plan, dry-run it, then apply with an undo journal.
6. **Report again** — regenerate the dashboard so the user sees the result.

## Ground rules (safety)

- **Never delete anything.** Duplicates go to a quarantine folder; the user
  empties it themselves once satisfied.
- **Never move files without an approved plan.** Every apply step consumes a
  plan file the user has seen (or explicitly waved through) and writes an
  undo journal.
- **Units are atomic.** Never move or dedupe individual files inside a
  detected VM, code repo, or installed application.
- **Cross-drive moves are copy-verify-then-delete**, handled by the apply
  script; never use bare `mv` across filesystems for large files.
- If a script reports permission errors or unreadable paths, surface them to
  the user rather than silently skipping.

## Typical kickoff

Ask the user (or infer from their message):
- Which roots/drives to scan (e.g. `D:\`, `/mnt/e`, an external disk).
- Where the catalog and reports should live (default `~/file-org/`).
- Whether anything is off-limits (folders to exclude from scanning).

Then invoke `drive-inventory` and proceed down the pipeline, checking in with
the user at the decision points: after the first report, before quarantining
duplicates, and before applying moves.
