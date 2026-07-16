#!/usr/bin/env python3
"""Classify cataloged files and detect atomic units.

Adds to the catalog:
  files.category TEXT, files.unit_id INTEGER
  units(id INTEGER PRIMARY KEY, path TEXT UNIQUE, kind TEXT, manual INTEGER,
        file_count INTEGER, total_bytes INTEGER)

See references/taxonomy.md for the category contract.
"""
import argparse
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict

EXT_CATEGORIES = {
    "video": "mp4 mkv avi mov wmv flv webm m4v mpg mpeg ts vob 3gp",
    "image": "jpg jpeg png gif bmp tiff tif webp heic raw cr2 nef arw dng svg ico psd",
    "audio": "mp3 flac wav aac ogg m4a wma opus aiff mid",
    "document": "pdf doc docx xls xlsx ppt pptx odt ods txt rtf md csv epub mobi",
    "installer": "msi apk deb rpm pkg appimage msix",
    "disc_image": "iso img bin cue nrg dmg",
    "vm_image": "vmdk vdi qcow2 vhd vhdx ova ovf",
    "archive": "zip rar 7z tar gz bz2 xz tgz cab",
    "backup": "bak old bkp bkf tib gho",
    "code": ("py js ts jsx tsx java c cpp h hpp cs go rs rb php sh ps1 bat "
             "html css scss json yaml yml sql ipynb"),
    "font": "ttf otf woff woff2",
    "database": "db sqlite sqlite3 mdb accdb",
    "system": "dll sys drv tmp log ini cfg dat lnk",
}
EXT_TO_CAT = {e: c for c, exts in EXT_CATEGORIES.items() for e in exts.split()}

VM_EXTS = {"vmx", "vbox", "vmcx", "vmdk", "vdi", "qcow2", "vhd", "vhdx"}
PROJECT_MARKERS = {"package.json", "pyproject.toml", "cargo.toml", "go.mod",
                   "gemfile", "composer.json", "cmakelists.txt"}
BACKUP_NAME_RE = re.compile(
    r"backup|bckp|^copy of |^kopie von |\.(bak|old|orig)$"
    r"| \([1-9]\)\.[^.]+$|-copy\.[^.]+$", re.IGNORECASE)


def connect(db):
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='files'"
                       ).fetchone():
        sys.exit("GATE BLOCKED: this catalog has no scan data.\n"
                 "Do this first: drive-inventory scan.py --db <db> <roots>")
    cols = {r[1] for r in con.execute("PRAGMA table_info(files)")}
    if "category" not in cols:
        con.execute("ALTER TABLE files ADD COLUMN category TEXT")
    if "unit_id" not in cols:
        con.execute("ALTER TABLE files ADD COLUMN unit_id INTEGER")
    if "media_year" not in cols:
        con.execute("ALTER TABLE files ADD COLUMN media_year INTEGER")
    con.execute(
        "CREATE TABLE IF NOT EXISTS units("
        "id INTEGER PRIMARY KEY, path TEXT UNIQUE, kind TEXT,"
        "manual INTEGER DEFAULT 0, file_count INTEGER, total_bytes INTEGER)")
    return con


def dir_stats(con):
    """Aggregate per-directory signals in one pass over the catalog."""
    stats = defaultdict(lambda: {"exe": 0, "dll": 0, "pak": 0,
                                 "vm": False, "git": False, "project": False,
                                 "uninst": False, "dcim": False,
                                 "photolib": False, "game": False})
    for path, name, ext in con.execute("SELECT path, name, ext FROM files"):
        d = os.path.dirname(path)
        s = stats[d]
        lname = name.lower()
        if ext == "exe":
            s["exe"] += 1
            if lname.startswith("unins") or lname == "uninstall.exe":
                s["uninst"] = True
            if lname.startswith("unitycrashhandler"):
                s["game"] = True
        elif ext == "dll":
            s["dll"] += 1
        elif ext == "pak":
            s["pak"] += 1
        if ext in VM_EXTS:
            s["vm"] = True
        if lname in PROJECT_MARKERS or lname.endswith(".sln"):
            s["project"] = True
        if lname == "steam_appid.txt":
            s["game"] = True
        if lname == "head" and os.path.basename(d).lower() == ".git":
            # mark the repo dir (parent of .git)
            stats[os.path.dirname(d)]["git"] = True
        if lname.endswith(".lrcat"):
            s["photolib"] = True
        parts = d.split(os.sep)
        lparts = [p.lower() for p in parts]
        if "dcim" in lparts:
            # unit root = the directory containing DCIM
            idx = lparts.index("dcim")
            stats[os.sep.join(parts[:idx])]["dcim"] = True
        if any(p.endswith(".photoslibrary") for p in lparts):
            s["photolib"] = True
    return stats


def unit_kind(s):
    if s["vm"]:
        return "vm"
    if s["git"] or s["project"]:
        return "code_project"
    if s["game"] or (s["pak"] >= 1 and s["exe"] >= 1 and s["dll"] >= 3):
        return "game"
    if s["uninst"] or (s["exe"] >= 3 and s["dll"] >= 5):
        return "app_install"
    if s["dcim"] or s["photolib"]:
        return "photo_library"
    return None


def detect_units(con):
    stats = dir_stats(con)
    candidates = {}
    for d, s in stats.items():
        kind = unit_kind(s)
        if kind:
            candidates[d] = kind
    # Keep only the shallowest qualifying dirs (units never nest).
    kept = {}
    for d in sorted(candidates, key=lambda p: p.count(os.sep)):
        if not any(d.startswith(parent + os.sep) for parent in kept):
            kept[d] = candidates[d]
    # Preserve manual units, replace auto-detected ones.
    con.execute("DELETE FROM units WHERE manual=0")
    manual = {p for (p,) in con.execute("SELECT path FROM units")}
    for d, kind in kept.items():
        if not any(d == m or d.startswith(m + os.sep) for m in manual):
            con.execute("INSERT OR IGNORE INTO units(path, kind) VALUES(?,?)",
                        (d, kind))
    con.commit()
    return len(kept)


def assign(con):
    """Set files.unit_id, aggregate unit sizes, and set files.category."""
    con.execute("UPDATE files SET unit_id=NULL")
    units = list(con.execute("SELECT id, path, kind FROM units"))
    for uid, upath, kind in units:
        like = upath.rstrip(os.sep) + os.sep + "%"
        con.execute("UPDATE files SET unit_id=?, category=?"
                    " WHERE path LIKE ? OR path=?", (uid, kind, like, upath))
        n, b = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(size),0) FROM files"
            " WHERE unit_id=?", (uid,)).fetchone()
        con.execute("UPDATE units SET file_count=?, total_bytes=? WHERE id=?",
                    (n, b, uid))
    # Loose files: extension mapping + backup-name override.
    rows = con.execute(
        "SELECT id, name, ext, depth FROM files WHERE unit_id IS NULL")
    updates = []
    for fid, name, ext, depth in rows:
        cat = EXT_TO_CAT.get(ext, "other")
        lname = name.lower()
        if lname in ("thumbs.db", ".ds_store", "desktop.ini"):
            cat = "system"
        elif BACKUP_NAME_RE.search(lname):
            cat = "backup"
        elif ext == "exe":
            # loose exe (not in an app_install unit) = probably an installer
            cat = "installer"
        updates.append((cat, fid))
    con.executemany("UPDATE files SET category=? WHERE id=?", updates)
    con.commit()


def _tiff_year(t):
    """Pull the best DateTime year out of a TIFF/EXIF blob. Stdlib-only."""
    if len(t) < 8 or t[:2] not in (b"II", b"MM"):
        return None
    bo = "little" if t[:2] == b"II" else "big"

    def u16(o):
        return int.from_bytes(t[o:o + 2], bo)

    def u32(o):
        return int.from_bytes(t[o:o + 4], bo)

    found = []  # (tag, ascii bytes)

    def parse_ifd(off, depth=0):
        if depth > 3 or off + 2 > len(t):
            return
        n = u16(off)
        for k in range(min(n, 200)):
            e = off + 2 + 12 * k
            if e + 12 > len(t):
                return
            tag, typ, cnt, val = u16(e), u16(e + 2), u32(e + 4), u32(e + 8)
            if tag in (0x9003, 0x0132) and typ == 2:  # DateTimeOriginal/DateTime
                vo = val if cnt > 4 else e + 8
                found.append((tag, t[vo:vo + min(cnt, 20)]))
            elif tag == 0x8769:  # Exif sub-IFD pointer
                parse_ifd(val, depth + 1)

    parse_ifd(u32(4))
    for tag, s in sorted(found, key=lambda f: f[0] != 0x9003):
        try:
            y = int(s[:4])
        except ValueError:
            continue
        if 1900 < y < 2100:
            return y
    return None


def exif_year(path):
    """Year a photo was taken, from JPEG APP1 EXIF or bare TIFF. None if
    unreadable or absent."""
    try:
        with open(path, "rb") as f:
            head = f.read(65536)
    except OSError:
        return None
    if head[:2] in (b"II", b"MM"):
        return _tiff_year(head)
    if head[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 4 <= len(head):
        if head[i] != 0xFF:
            return None
        marker = head[i + 1]
        if marker == 0xD8 or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            i += 2
            continue
        seglen = int.from_bytes(head[i + 2:i + 4], "big")
        if marker == 0xE1 and head[i + 4:i + 10] == b"Exif\x00\x00":
            return _tiff_year(head[i + 10:i + 2 + seglen])
        if marker == 0xDA:  # start of scan — no EXIF coming
            return None
        i += 2 + seglen
    return None


def extract_years(con):
    """Fill files.media_year for images that support cheap EXIF parsing."""
    rows = con.execute(
        "SELECT id, path FROM files WHERE media_year IS NULL"
        " AND ext IN ('jpg','jpeg','tif','tiff')"
        " AND category IN ('image','photo_library')").fetchall()
    print(f"Reading EXIF dates from {len(rows):,} images ...")
    updates = []
    got = 0
    for fid, path in rows:
        y = exif_year(path)
        if y:
            updates.append((y, fid))
            got += 1
        if len(updates) >= 1000:
            con.executemany(
                "UPDATE files SET media_year=? WHERE id=?", updates)
            con.commit()
            updates.clear()
    con.executemany("UPDATE files SET media_year=? WHERE id=?", updates)
    con.commit()
    print(f"Found EXIF dates for {got:,} of {len(rows):,} images."
          " (Files without one fall back to modification year when"
          " year-sorting in file-organize.)")


def report(con):
    print("=== Categories (by size) ===")
    for cat, n, b in con.execute(
            "SELECT category, COUNT(*), SUM(size) FROM files"
            " GROUP BY category ORDER BY SUM(size) DESC"):
        print(f"  {cat or 'unclassified':<14} {n:>10,} files"
              f"  {(b or 0) / 1e9:>10.2f} GB")
    print("\n=== Units (top 40 by size) ===")
    for path, kind, n, b in con.execute(
            "SELECT path, kind, file_count, total_bytes FROM units"
            " ORDER BY total_bytes DESC LIMIT 40"):
        print(f"  [{kind:<13}] {(b or 0) / 1e9:>8.2f} GB  {n or 0:>8,} files"
              f"  {path}")
    (n,) = con.execute("SELECT COUNT(*) FROM units").fetchone()
    print(f"\n{n} units total.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--exif", action="store_true",
                    help="also read EXIF dates from images (fills"
                         " media_year for year-based photo sorting)")
    ap.add_argument("--set-unit", nargs=2, metavar=("PATH", "KIND"),
                    help="manually mark a directory as a unit")
    ap.add_argument("--unset-unit", metavar="PATH",
                    help="remove a unit (manual or auto)")
    args = ap.parse_args()
    con = connect(args.db)

    if args.set_unit:
        path, kind = args.set_unit
        con.execute("INSERT OR REPLACE INTO units(path, kind, manual)"
                    " VALUES(?,?,1)", (os.path.abspath(path), kind))
        con.commit()
        assign(con)
        print(f"Unit set: {path} -> {kind}")
    elif args.unset_unit:
        con.execute("DELETE FROM units WHERE path=?",
                    (os.path.abspath(args.unset_unit),))
        con.commit()
        assign(con)
        print(f"Unit removed: {args.unset_unit}")
    elif args.report:
        report(con)
    else:
        (nf,) = con.execute("SELECT COUNT(*) FROM files").fetchone()
        if not nf:
            sys.exit("GATE BLOCKED: the catalog is empty - nothing has been"
                     " scanned.\nDo this first: drive-inventory scan.py"
                     " --db <db> <roots>")
        n = detect_units(con)
        print(f"Detected {n} units.")
        assign(con)
        print("Classification complete.")
        if args.exif:
            extract_years(con)
        con.execute("CREATE TABLE IF NOT EXISTS pipeline_log("
                    "stage TEXT, ts REAL, evidence TEXT)")
        con.execute("INSERT INTO pipeline_log VALUES('classify',?,?)",
                    (time.time(), f"{nf} files, {n} units"))
        con.commit()
        report(con)
    con.close()


if __name__ == "__main__":
    main()
