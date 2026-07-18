---
name: drive-inventory
description: Scan one or more drives or folders into a SQLite file catalog (path, size, mtime, extension). First stage of the file-org pipeline. Use when the user wants to scan, index, or take stock of a drive or directory tree.
---

# Drive Inventory

Builds the catalog every other file-org skill depends on. The scanner is
stdlib-only Python, error-tolerant, and safe to re-run: each root is replaced
atomically in the catalog, so re-scanning a drive updates it without touching
other drives' rows.

## Usage

```bash
python3 scripts/scan.py --db ~/file-org/catalog.db <root> [<root> ...] \
    [--exclude PATTERN ...] [--label NAME]
```

- `<root>` — one or more directories to scan (`/mnt/d`, `E:\`, `~/old-backup`).
- `--label` — friendly name for the root (defaults to the path); shows up as
  the "drive" column in reports. When scanning multiple roots in one call,
  omit it and let each root label itself, or run one call per root.
- `--exclude` — glob-ish substring patterns to skip (repeatable). Sensible
  system junk (`$RECYCLE.BIN`, `System Volume Information`, `.Trash*`,
  `/proc`, `/sys`) is excluded automatically.

The script prints progress every 10,000 files and a summary at the end
(files, total bytes, errors). Errors (permission denied, vanished files) are
counted and logged to the `scan_errors` table, never fatal.

## Workflow

1. Confirm the roots with the user and pick a catalog path (default
   `~/file-org/catalog.db`).
2. Run the scan per root. For very large drives, run it with
   `run_in_background` and report progress from the output.
3. When done, give the user a quick shape-of-the-data summary, e.g.:

```bash
python3 scripts/scan.py --db ~/file-org/catalog.db --summary
```

which prints per-root file counts, total sizes, and top extensions.

4. Hand off to `file-classify` next.

## Notes

- Symlinks are recorded but not followed (no cycles, no double counting).
- Hashes are NOT computed at this stage — that's `file-dedupe`'s job, and it
  only hashes files that share a size with another file.
- The catalog schema is documented at the top of `scripts/scan.py`; other
  skills' scripts add columns/tables but never drop the `files` table.
