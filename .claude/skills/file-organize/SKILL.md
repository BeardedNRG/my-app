---
name: file-organize
description: Design a clean target folder layout and generate/apply collision-safe move plans with an undo journal, moving whole units (VMs, repos, apps) atomically. Final stage of the file-org pipeline, after classify and dedupe. Use when the user wants to reorganize, restructure, or consolidate files into a tidy layout.
---

# File Organization (Layout + Moves)

Turns the classified catalog into a tidy physical layout. Two scripts:
`plan_moves.py` decides *what goes where* (pure planning, touches nothing);
`apply_moves.py` executes an approved plan with verification and an undo
journal.

## Step 1 — agree the layout with the user

Start from `references/layout.md` (a sensible default taxonomy: Media,
Documents, Software, VMs, Projects, Backups, Archive). Adapt it to the
user's drives — e.g. VMs and disc images on the fastest/biggest drive,
photos consolidated onto one drive. Write the agreed mapping into a small
JSON config:

```json
{
  "destinations": {
    "video":      "/mnt/d/Media/Video",
    "image":      "/mnt/d/Media/Photos",
    "audio":      "/mnt/d/Media/Audio",
    "document":   "/mnt/d/Documents",
    "installer":  "/mnt/e/Software/Installers",
    "disc_image": "/mnt/e/Software/ISOs",
    "vm":         "/mnt/e/VMs",
    "vm_image":   "/mnt/e/VMs/loose-images",
    "code_project": "/mnt/d/Projects",
    "app_install": null,
    "game":        null,
    "archive":    "/mnt/e/Archive",
    "backup":     "/mnt/e/Archive/old-backups",
    "photo_library": "/mnt/d/Media/Photos/Libraries"
  },
  "keep_subtree_below": "/mnt/d/Media/Video",
  "year_subfolders": ["image"],
  "photo_kind_destinations": {
    "camera":     "/mnt/d/Media/Photos",
    "screenshot": "/mnt/d/Media/Photos/Screenshots",
    "saved_web":  "/mnt/d/Media/Photos/Saved-from-web"
  }
}
```

- A category mapped to `null` is **left in place** (installed apps and games
  usually break if moved — default them to null).
- Categories not listed are left in place.
- `keep_subtree_below` destinations preserve the source's own subfolder
  structure under the destination (good for already-organized media);
  otherwise files land in `<dest>/<source-drive-label>/<original parent>/`
  so nothing gets flattened into a 50,000-file soup.
- `year_subfolders` lists categories to group by year instead of by drive:
  `<dest>/<year>/<original parent>/`. The year comes from EXIF capture date
  when `file-classify --exif` has run, else the file's modification year.
- `photo_kind_destinations` routes triaged images (see `file-classify`'s
  photo_triage) by kind, overriding the plain `image` mapping. Year
  subfolders apply only to `camera` — memes don't deserve a timeline.
  Leave `unknown` unmapped so the review pile follows the normal `image`
  destination rather than being filed as junk.

## Step 2 — plan (touches nothing)

```bash
python3 scripts/plan_moves.py --db ~/file-org/catalog.db \
    --config layout.json --out ~/file-org/move-plan.csv
```

Prints: files/units per destination, bytes moved per drive pair (so the user
knows how long cross-drive copies will take), collisions resolved, and
anything skipped. Units move as single rows (whole directory).

## Step 3 — apply (only after user approval)

```bash
python3 scripts/apply_moves.py --plan ~/file-org/move-plan.csv \
    --journal ~/file-org/move-journal.jsonl [--dry-run]
```

- Same-filesystem: instant `rename`.
- Cross-filesystem: **copy → size+SHA-256 verify → delete source**; on any
  mismatch the source is kept and the row is marked failed.
- Name collisions get `~1`, `~2` suffixes — never overwrites.
- `--dry-run` prints every operation without doing it. Run it first, always.
- Undo: `apply_moves.py --undo --journal ...` reverses everything journaled.

## Step 4 — verify and re-scan

After applying, re-run `drive-inventory` on the affected roots and
`storage-report` so the catalog and the user's mental model match the new
reality.
