#!/usr/bin/env python3
"""Look inside archives and summarize what they contain.

Answers "what IS backup2016.zip?" without extracting: entry count,
uncompressed size, dominant content category, and top-level folders,
stored in files.archive_summary and printed for review.

Engines: zip/tar/tgz/tar.gz/tar.bz2/tar.xz via stdlib; 7z and rar via the
`7z` / `unrar` CLIs when installed (skipped with a note otherwise).

Usage:
  python3 scripts/archive_peek.py --db ~/file-org/catalog.db [--reset]
"""
import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import zipfile
from collections import Counter

# keep in sync with classify.py's EXT_CATEGORIES (subset is fine here)
EXT_CATEGORIES = {
    "video": "mp4 mkv avi mov wmv flv webm m4v mpg mpeg ts vob 3gp",
    "image": "jpg jpeg png gif bmp tiff tif webp heic raw cr2 nef arw dng svg psd",
    "audio": "mp3 flac wav aac ogg m4a wma opus",
    "document": "pdf doc docx xls xlsx ppt pptx odt txt rtf md csv epub",
    "code": "py js ts java c cpp h cs go rs rb php sh html css json yaml sql",
    "executable": "exe dll msi sys",
    "archive": "zip rar 7z tar gz",
}
EXT_TO_CAT = {e: c for c, exts in EXT_CATEGORIES.items() for e in exts.split()}

ZIP_EXTS = ("zip",)
TAR_EXTS = ("tar", "tgz", "gz", "bz2", "xz")
CLI_EXTS = ("7z", "rar")
MAX_ENTRIES = 20000  # cap listing work on monster archives


def summarize(names_sizes):
    cats = Counter()
    top = Counter()
    total = 0
    n = 0
    for name, size in names_sizes:
        n += 1
        total += size or 0
        base = name.rstrip("/").replace("\\", "/")
        if not base or base.endswith("/"):
            continue
        ext = base.rsplit(".", 1)[-1].lower() if "." in base else ""
        cats[EXT_TO_CAT.get(ext, "other")] += 1
        top[base.split("/")[0]] += 1
        if n >= MAX_ENTRIES:
            break
    if not n:
        return None
    lead, lead_n = cats.most_common(1)[0]
    tops = ", ".join(t for t, _ in top.most_common(3))
    pct = 100 * lead_n // n
    return (f"{n:,} entries, {total / 1e9:.2f} GB uncompressed;"
            f" mostly {lead} ({pct}%); top: {tops}")


def peek_zip(path):
    with zipfile.ZipFile(path) as z:
        return summarize((i.filename, i.file_size) for i in z.infolist())


def peek_tar(path):
    with tarfile.open(path) as t:
        def gen():
            for m in t:
                yield m.name, m.size
        return summarize(gen())


def peek_cli(path, ext):
    if ext == "7z" and shutil.which("7z"):
        out = subprocess.run(["7z", "l", "-slt", path], capture_output=True,
                             timeout=120).stdout.decode(errors="replace")
        entries = []
        name = size = None
        for line in out.splitlines():
            if line.startswith("Path = "):
                name = line[7:]
            elif line.startswith("Size = "):
                size = int(line[7:] or 0)
            elif not line.strip() and name:
                entries.append((name, size or 0))
                name = size = None
        return summarize(entries[1:])  # first Path is the archive itself
    if ext == "rar" and shutil.which("unrar"):
        out = subprocess.run(["unrar", "lb", path], capture_output=True,
                             timeout=120).stdout.decode(errors="replace")
        return summarize((n, 0) for n in out.splitlines() if n.strip())
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.execute("PRAGMA journal_mode=WAL")
    cols = {r[1] for r in con.execute("PRAGMA table_info(files)")}
    if "archive_summary" not in cols:
        con.execute("ALTER TABLE files ADD COLUMN archive_summary TEXT")
    if args.reset:
        con.execute("UPDATE files SET archive_summary=NULL")

    exts = ZIP_EXTS + TAR_EXTS + CLI_EXTS
    rows = con.execute(
        "SELECT id, path, ext FROM files WHERE archive_summary IS NULL"
        " AND is_symlink=0 AND category IN ('archive','backup')"
        " AND ext IN (%s)" % ",".join("?" * len(exts)), exts).fetchall()
    missing_cli = set()
    print(f"Peeking inside {len(rows):,} archives ...")
    done = 0
    for fid, path, ext in rows:
        summary = None
        try:
            if ext in ZIP_EXTS:
                summary = peek_zip(path)
            elif ext in TAR_EXTS:
                # plain .gz/.bz2/.xz of a single file won't open as tar
                summary = peek_tar(path)
            else:
                summary = peek_cli(path, ext)
                if summary is None:
                    missing_cli.add(ext)
        except Exception as e:
            summary = f"unreadable: {type(e).__name__}"
        if summary:
            con.execute("UPDATE files SET archive_summary=? WHERE id=?",
                        (summary, fid))
            done += 1
        if done and done % 200 == 0:
            con.commit()
            print(f"  {done:,}/{len(rows):,}", flush=True)
    con.commit()
    if missing_cli:
        print(f"  note: skipped {'/'.join(sorted(missing_cli))} archives -"
              " install 7z/unrar for those")

    print("\n=== Largest archives ===")
    for path, size, s in con.execute(
            "SELECT path, size, archive_summary FROM files"
            " WHERE archive_summary IS NOT NULL"
            " ORDER BY size DESC LIMIT 25"):
        print(f"  {size / 1e9:>7.2f} GB  {path}\n           -> {s}")
    con.close()


if __name__ == "__main__":
    main()
