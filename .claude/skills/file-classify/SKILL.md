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

## Photo triage (real photos vs memes/screenshots/web saves)

When the user wants saved junk separated from their actual photographs:

```bash
python3 scripts/photo_triage.py --db ~/file-org/catalog.db [--reset]
```

Writes `files.photo_kind`: `camera` / `screenshot` / `saved_web` /
`unknown`. Signals: camera EXIF (social platforms strip it), filename
forensics (`FB_IMG_*` and Facebook CDN names, `received_*`, `Screenshot_*`,
`IMG_nnnn`), pixel dimensions, and — when Pillow is installed — content
flatness (memes are flat graphics, photos are gradients). `unknown` is a
deliberate review pile: nothing ambiguous is ever called junk.

Always show the user the per-kind example files it prints and let them
spot-check before routing kinds to folders with `file-organize`'s
`photo_kind_destinations` config (e.g. camera → `Photos/`, screenshot →
`Photos/Screenshots/`, saved_web → `Photos/Saved-from-web/`). The
storage-report dashboard shows the triage breakdown once this has run.

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

## Video metadata

```bash
python3 scripts/video_meta.py --db ~/file-org/catalog.db
```

Fills `files.video_w/video_h/duration_s` and prints a resolution breakdown
(4K+/1080p/720p/SD). Uses ffprobe automatically when installed (covers
mkv/wmv/everything); otherwise a stdlib MP4/MOV/AVI parser. Useful before
dedupe decisions on video collections — resolution identifies the keeper.

## Archive contents

```bash
python3 scripts/archive_peek.py --db ~/file-org/catalog.db
```

Lists inside zip/tar (stdlib) and 7z/rar (if `7z`/`unrar` installed)
without extracting; writes a one-line summary per archive
(`files.archive_summary`: entries, uncompressed size, dominant category,
top folders) so "backup2016.zip" stops being a mystery.

## Extending the taxonomy

Edit the tables in `scripts/classify.py` (EXT_CATEGORIES, unit markers) —
they are plain dicts near the top. Keep `references/taxonomy.md` in sync; it
is the human-readable contract for what each category means.

## Ranking candidate copies of a build (which folder is the real one?)

When a folder holds many copies of a project — old backups, installer
payloads, clones — and the user needs to know which one to revive:

```bash
python3 scripts/rank_builds.py --db <catalog.db> <parent-folder>
python3 scripts/rank_builds.py --db <catalog.db> --dirs A B C
```

Generic — no project knowledge needed, works on any folder past or
future. Ranks by unique content (the copy someone worked in accumulates
files no clone has), sustained edit activity vs one tight extract-time
cluster, source markers (.git, code files), and completeness. Installer
payloads are labeled and ranked last; byte-identical candidates are
collapsed into clone groups. Ends with a plain verdict naming the folder
to revive from. Run scan + classify first; `dedupe.py scan` beforehand
sharpens uniqueness with real hashes.
