#!/usr/bin/env python3
"""Scan directory trees into a SQLite file catalog.

Schema (created here, extended by later pipeline stages):

  files(
    id INTEGER PRIMARY KEY,
    root TEXT,          -- label of the scanned root ("drive")
    path TEXT UNIQUE,   -- absolute path
    name TEXT,          -- basename
    ext TEXT,           -- lowercase extension without dot ('' if none)
    size INTEGER,       -- bytes
    mtime REAL,         -- unix timestamp
    depth INTEGER,      -- path depth below the root
    is_symlink INTEGER  -- 1 if the entry is a symlink (not followed)
  )
  scan_errors(root TEXT, path TEXT, error TEXT, ts REAL)
  scan_meta(root TEXT PRIMARY KEY, root_path TEXT, scanned_at REAL,
            file_count INTEGER, total_bytes INTEGER)

Later stages add: files.category, files.unit_id, files.quick_hash,
files.full_hash, and the units / dup_groups / move_plan tables.
"""
import argparse
import fnmatch
import os
import sqlite3
import sys
import time

DEFAULT_EXCLUDES = [
    "$RECYCLE.BIN", "System Volume Information", ".Trash*",
    "pagefile.sys", "hiberfil.sys", "swapfile.sys",
    "/proc", "/sys", "/dev", "/run",
]

BATCH = 2000
PROGRESS_EVERY = 10000


def connect(db_path):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS files(
            id INTEGER PRIMARY KEY,
            root TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            ext TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime REAL NOT NULL,
            depth INTEGER NOT NULL,
            is_symlink INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_files_root ON files(root);
        CREATE INDEX IF NOT EXISTS idx_files_ext ON files(ext);
        CREATE INDEX IF NOT EXISTS idx_files_size ON files(size);
        CREATE TABLE IF NOT EXISTS scan_errors(
            root TEXT, path TEXT, error TEXT, ts REAL
        );
        CREATE TABLE IF NOT EXISTS scan_meta(
            root TEXT PRIMARY KEY, root_path TEXT, scanned_at REAL,
            file_count INTEGER, total_bytes INTEGER
        );
        """
    )
    return con


def excluded(path, patterns):
    parts = path.split(os.sep)
    for pat in patterns:
        if pat.startswith(os.sep):
            # absolute pattern: match only as a path prefix
            if path == pat or path.startswith(pat + os.sep):
                return True
        elif any(fnmatch.fnmatch(p, pat) for p in parts):
            # relative pattern: match whole path components
            return True
    return False


def scan_root(con, root, label, excludes):
    root = os.path.abspath(root)
    label = label or root
    print(f"Scanning {root} as '{label}' ...", flush=True)
    # Replace any previous scan of this label atomically.
    con.execute("BEGIN")
    con.execute("DELETE FROM files WHERE root=?", (label,))
    con.execute("DELETE FROM scan_errors WHERE root=?", (label,))

    count = 0
    total = 0
    errors = 0
    batch = []
    base_depth = root.rstrip(os.sep).count(os.sep)
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = os.scandir(d)
        except OSError as e:
            errors += 1
            con.execute(
                "INSERT INTO scan_errors VALUES(?,?,?,?)",
                (label, d, str(e), time.time()),
            )
            continue
        with entries:
            for entry in entries:
                path = entry.path
                if excluded(path, excludes):
                    continue
                try:
                    is_link = entry.is_symlink()
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(path)
                        continue
                    if not (entry.is_file(follow_symlinks=False) or is_link):
                        continue
                    st = entry.stat(follow_symlinks=False)
                except OSError as e:
                    errors += 1
                    con.execute(
                        "INSERT INTO scan_errors VALUES(?,?,?,?)",
                        (label, path, str(e), time.time()),
                    )
                    continue
                name = entry.name
                dot = name.rfind(".")
                ext = name[dot + 1:].lower() if 0 < dot < len(name) - 1 else ""
                depth = path.count(os.sep) - base_depth
                batch.append(
                    (label, path, name, ext, st.st_size, st.st_mtime,
                     depth, 1 if is_link else 0)
                )
                count += 1
                total += st.st_size
                if len(batch) >= BATCH:
                    con.executemany(
                        "INSERT OR REPLACE INTO files"
                        "(root,path,name,ext,size,mtime,depth,is_symlink)"
                        " VALUES(?,?,?,?,?,?,?,?)", batch)
                    batch.clear()
                if count % PROGRESS_EVERY == 0:
                    print(f"  {count:,} files, {total / 1e9:.1f} GB ...",
                          flush=True)
    if batch:
        con.executemany(
            "INSERT OR REPLACE INTO files"
            "(root,path,name,ext,size,mtime,depth,is_symlink)"
            " VALUES(?,?,?,?,?,?,?,?)", batch)
    con.execute(
        "INSERT OR REPLACE INTO scan_meta VALUES(?,?,?,?,?)",
        (label, root, time.time(), count, total),
    )
    con.execute("CREATE TABLE IF NOT EXISTS pipeline_log("
                "stage TEXT, ts REAL, evidence TEXT)")
    con.execute("INSERT INTO pipeline_log VALUES('scan',?,?)",
                (time.time(), f"{label}: {count} files, {errors} errors"))
    con.commit()
    print(f"Done: {count:,} files, {total / 1e9:.2f} GB, {errors} errors "
          f"(see scan_errors table)", flush=True)


def summary(con):
    print("=== Catalog summary ===")
    for root, ts, n, b in con.execute(
            "SELECT root, scanned_at, file_count, total_bytes FROM scan_meta"
            " ORDER BY total_bytes DESC"):
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
        print(f"  {root}: {n:,} files, {b / 1e9:.2f} GB (scanned {when})")
    print("\nTop 20 extensions by size:")
    for ext, n, b in con.execute(
            "SELECT ext, COUNT(*), SUM(size) FROM files"
            " GROUP BY ext ORDER BY SUM(size) DESC LIMIT 20"):
        print(f"  .{ext or '(none)':<12} {n:>10,} files  {b / 1e9:>10.2f} GB")
    (nerr,) = con.execute("SELECT COUNT(*) FROM scan_errors").fetchone()
    if nerr:
        print(f"\n{nerr} scan errors recorded in scan_errors table.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("roots", nargs="*", help="directories to scan")
    ap.add_argument("--db", required=True, help="catalog SQLite path")
    ap.add_argument("--label", help="root label (single-root scans only)")
    ap.add_argument("--exclude", action="append", default=[],
                    help="substring/glob pattern to skip (repeatable)")
    ap.add_argument("--summary", action="store_true",
                    help="print catalog summary and exit")
    args = ap.parse_args()

    con = connect(args.db)
    if args.summary:
        summary(con)
        return
    if not args.roots:
        ap.error("no roots given (or use --summary)")
    if args.label and len(args.roots) > 1:
        ap.error("--label only works with a single root")
    excludes = DEFAULT_EXCLUDES + args.exclude
    for root in args.roots:
        if not os.path.isdir(root):
            print(f"SKIP {root}: not a directory", file=sys.stderr)
            continue
        scan_root(con, root, args.label, excludes)
    con.close()


if __name__ == "__main__":
    main()
