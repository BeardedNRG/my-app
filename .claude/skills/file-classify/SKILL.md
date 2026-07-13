---
name: file-classify
description: Categorize every cataloged file (VMs, installers, backups, photos, videos, code, documents...) and detect atomic units like VM folders, git repos, and app installs that must never be split. Second stage of the file-org pipeline, after drive-inventory.
---

# File Classification

Reads the catalog produced by `drive-inventory` and writes two things back:

- **`files.category`** — one label per file from the taxonomy in
  `references/taxonomy.md`.
- **`units` table + `files.unit_id`** — detected *atomic units*: directories
  that must be treated as a single object (a virtual machine, a git repo, an
  installed application, a photo library). Later stages move units whole and
  never dedupe inside them.

## Usage

```bash
python3 scripts/classify.py --db ~/file-org/catalog.db          # classify all
python3 scripts/classify.py --db ~/file-org/catalog.db --report # print result
python3 scripts/classify.py --db ... --exif   # also read photo dates (below)
```

Classification is idempotent — safe to re-run after a re-scan.

`--exif` additionally reads EXIF capture dates from JPEG/TIFF images
(stdlib-only parser, reads at most 64 KB per file) into `files.media_year`,
which lets `file-organize` sort photos into `Photos/<year>/...` via its
`year_subfolders` config. Use it when the user wants photos organized by
year; skip it otherwise — it opens every image once.

## How it decides (order matters)

1. **Unit detection first.** A directory containing `.vmx`/`.vbox`/`.vdi`/
   `.qcow2` files becomes a `vm` unit; a directory with `.git` becomes a
   `code_project` unit; `unins*.exe` or a dense cluster of `.exe`+`.dll`
   marks an `app_install`; `DCIM` marks a `photo_library`. Every file under
   a unit inherits the unit's category.
2. **Extension mapping** for loose files (see taxonomy).
3. **Name heuristics** override extensions for backups: names containing
   `backup`, `.bak`, `.old`, `copy of`, `(1)`/`(2)` duplicates-by-name, and
   date-stamped archive names get the `backup` category.

## Workflow

1. Run classify, then show the user the `--report` output: bytes and file
   counts per category, plus the detected units (name, kind, size).
2. Sanity-check the units list with the user — a mislabeled unit (e.g. a
   folder that looks like an app but is actually a portable-app backup)
   should be fixed now, before dedupe/organize rely on it. Manual overrides:

```bash
python3 scripts/classify.py --db ... --set-unit "/path/to/dir" vm
python3 scripts/classify.py --db ... --unset-unit "/path/to/dir"
```

3. Hand off to `storage-report` for the visual dashboard.

## Extending the taxonomy

Edit the tables in `scripts/classify.py` (EXT_CATEGORIES, unit markers) —
they are plain dicts near the top. Keep `references/taxonomy.md` in sync; it
is the human-readable contract for what each category means.
