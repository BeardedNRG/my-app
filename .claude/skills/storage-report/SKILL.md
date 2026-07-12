---
name: storage-report
description: Generate a self-contained HTML dashboard from the file catalog - per-drive and per-category breakdowns, folder treemap, largest files, duplicate summary. Use when the user wants to see, visualize, or review what is on their drives at any pipeline stage.
---

# Storage Report

Renders the catalog as one self-contained HTML file (inline CSS/JS, no
network, works offline in any browser). Run it after inventory+classify for
the "what do I have?" view, after dedupe/organize for the before/after.

## Usage

```bash
python3 scripts/report.py --db ~/file-org/catalog.db \
    --out ~/file-org/storage-report.html [--top-dirs 30] [--top-files 50]
```

Then send the HTML to the user (`SendUserFile` with `display: render`, or
publish as an Artifact if they want a shareable page).

## What's in it

- **Summary tiles** — total files, total size, per-drive size, duplicate
  waste (if dedupe scan has run), unit counts.
- **Category breakdown** — horizontal bars, bytes + file counts, per drive.
- **Folder treemap** — top directories by size (squarified, hover for
  details) so the user can *see* where the bulk lives.
- **Units table** — every detected VM, repo, app install with size.
- **Largest files** — top N with category and path.
- **Duplicate groups** — top reclaimable groups (only if `file-dedupe scan`
  has populated hashes).

The report degrades gracefully: sections whose data isn't in the catalog yet
(categories, hashes) are simply omitted, so it works right after a bare
inventory scan too.
