#!/usr/bin/env python3
"""Staged duplicate detection + quarantine over the file-org catalog.

Subcommands:
  scan   hash size-collision candidates (quick 64KB hash, then full SHA-256)
  plan   build keeper/quarantine plan CSV from dup groups
  apply  move quarantined files (same-drive rename) per approved plan
  undo   reverse an apply using its journal

Adds: files.quick_hash, files.full_hash columns.
Never deletes anything. Files inside units (unit_id NOT NULL) are skipped.
"""
import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys
import time
from collections import defaultdict

QUICK_BYTES = 65536
QUARANTINE = "_Quarantine_Duplicates"


def connect(db):
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    cols = {r[1] for r in con.execute("PRAGMA table_info(files)")}
    for col in ("quick_hash", "full_hash"):
        if col not in cols:
            con.execute(f"ALTER TABLE files ADD COLUMN {col} TEXT")
    con.execute("CREATE INDEX IF NOT EXISTS idx_files_fullhash"
                " ON files(full_hash)")
    return con


def hash_file(path, quick=False):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        if quick:
            h.update(f.read(QUICK_BYTES))
        else:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()


def candidates_where(args, alias=""):
    p = alias + "." if alias else ""
    where = (f"{p}size >= ? AND {p}unit_id IS NULL AND {p}is_symlink=0"
             f" AND {p}size IN (SELECT size FROM files WHERE unit_id IS NULL"
             "               GROUP BY size HAVING COUNT(*) > 1)")
    params = [args.min_size]
    if args.category:
        where += f" AND {p}category=?"
        params.append(args.category)
    return where, params


def cmd_scan(con, args):
    where, params = candidates_where(args)
    rows = con.execute(
        f"SELECT id, path, size FROM files WHERE {where}"
        " AND quick_hash IS NULL", params).fetchall()
    print(f"Quick-hashing {len(rows):,} size-collision candidates ...")
    done = 0
    for fid, path, _ in rows:
        try:
            qh = hash_file(path, quick=True)
        except OSError as e:
            print(f"  ERR {path}: {e}", file=sys.stderr)
            continue
        con.execute("UPDATE files SET quick_hash=? WHERE id=?", (qh, fid))
        done += 1
        if done % 500 == 0:
            con.commit()
            print(f"  {done:,}/{len(rows):,}", flush=True)
    con.commit()

    # Full-hash only files sharing (size, quick_hash) with another file.
    fwhere, fparams = candidates_where(args, alias="f")
    rows = con.execute(
        f"""SELECT f.id, f.path, f.size FROM files f
            JOIN (SELECT size, quick_hash FROM files
                  WHERE quick_hash IS NOT NULL AND unit_id IS NULL
                  GROUP BY size, quick_hash HAVING COUNT(*) > 1) g
              ON f.size=g.size AND f.quick_hash=g.quick_hash
            WHERE f.full_hash IS NULL AND {fwhere}""", fparams).fetchall()
    total_b = sum(r[2] for r in rows)
    print(f"Full-hashing {len(rows):,} files ({total_b / 1e9:.1f} GB) ...")
    done_b = 0
    for fid, path, size in rows:
        try:
            fh = hash_file(path)
        except OSError as e:
            print(f"  ERR {path}: {e}", file=sys.stderr)
            continue
        con.execute("UPDATE files SET full_hash=? WHERE id=?", (fh, fid))
        done_b += size
        if done_b and done_b % (10 << 30) < size:
            con.commit()
            print(f"  {done_b / 1e9:.0f}/{total_b / 1e9:.0f} GB", flush=True)
    con.commit()
    groups = con.execute(
        "SELECT COUNT(*) FROM (SELECT full_hash FROM files"
        " WHERE full_hash IS NOT NULL AND unit_id IS NULL"
        " GROUP BY full_hash HAVING COUNT(*) > 1)").fetchone()[0]
    print(f"Scan complete: {groups:,} duplicate groups found. Run 'plan'.")


def keeper_score(path, category, mtime, depth):
    p = path.lower()
    score = 0.0
    if "download" not in p:
        score += 4
    if category != "backup":
        score += 4
    for marker in ("copy of", "(1)", "(2)", "-copy", "_old", "backup"):
        if marker in p:
            score -= 2
    score -= depth * 0.1
    score -= mtime / 1e10  # older wins ties
    return score


def cmd_plan(con, args):
    where, params = candidates_where(args)
    rows = con.execute(
        f"SELECT id, path, root, size, mtime, depth, category, full_hash"
        f" FROM files WHERE full_hash IS NOT NULL AND {where}",
        params).fetchall()
    groups = defaultdict(list)
    for r in rows:
        groups[(r[7], r[3])].append(r)
    groups = {k: v for k, v in groups.items() if len(v) > 1}

    reclaim = 0
    n_files = 0
    plan_rows = []
    largest = []
    for (fh, size), members in groups.items():
        members.sort(key=lambda r: keeper_score(r[1], r[6], r[4], r[5]),
                     reverse=True)
        keeper = members[0]
        for m in members[1:]:
            reclaim += size
            n_files += 1
            plan_rows.append({
                "action": "quarantine", "path": m[1], "root": m[2],
                "size": size, "keeper": keeper[1], "hash": fh[:16]})
        largest.append((size * (len(members) - 1), size, len(members),
                        keeper[1]))
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["action", "path", "root", "size",
                                          "keeper", "hash"])
        w.writeheader()
        w.writerows(sorted(plan_rows, key=lambda r: -r["size"]))
    print(f"=== Dedupe plan: {args.out} ===")
    print(f"  {len(groups):,} duplicate groups")
    print(f"  {n_files:,} files to quarantine")
    print(f"  {reclaim / 1e9:.2f} GB reclaimable")
    print("\nTop 20 groups by reclaimable size:")
    for rec, size, n, keeper in sorted(largest, reverse=True)[:20]:
        print(f"  {rec / 1e9:>7.2f} GB  ({n} copies x {size / 1e6:.0f} MB)"
              f"  keep: {keeper}")
    print("\nReview/edit the CSV (change 'quarantine' to 'keep' to spare a"
          " file), then run 'apply'.")


def find_root_dir(con, label):
    """Quarantine goes at the top of the scanned root for this label."""
    row = con.execute("SELECT root_path FROM scan_meta WHERE root=?",
                      (label,)).fetchone()
    if row and row[0] and os.path.isdir(row[0]):
        return row[0]
    if os.path.isdir(label):
        return label
    return None


def cmd_apply(con, args):
    rows = list(csv.DictReader(open(args.plan)))
    todo = [r for r in rows if r["action"].strip().lower() == "quarantine"]
    print(f"Applying: {len(todo):,} of {len(rows):,} plan rows ...")
    journal = open(args.journal, "a")
    moved = 0
    errors = 0
    for r in todo:
        src = r["path"]
        root_dir = find_root_dir(con, r["root"]) or os.path.dirname(src)
        rel = os.path.relpath(src, root_dir)
        if rel.startswith(".."):
            rel = os.path.basename(src)
        dst = os.path.join(root_dir, QUARANTINE, rel)
        try:
            if not os.path.exists(src):
                raise FileNotFoundError(src)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            base, ext = os.path.splitext(dst)
            i = 1
            while os.path.exists(dst):
                dst = f"{base}~{i}{ext}"
                i += 1
            os.rename(src, dst)  # same filesystem: instant, no copy
        except OSError as e:
            print(f"  ERR {src}: {e}", file=sys.stderr)
            errors += 1
            continue
        journal.write(json.dumps({"op": "quarantine", "src": src,
                                  "dst": dst, "ts": time.time()}) + "\n")
        con.execute("UPDATE files SET path=?, root=? WHERE path=?",
                    (dst, r["root"], src))
        moved += 1
        if moved % 200 == 0:
            con.commit()
            journal.flush()
    con.commit()
    journal.close()
    print(f"Done: {moved:,} files quarantined, {errors} errors."
          f"\nQuarantine folders are named '{QUARANTINE}' at each drive root."
          f"\nUndo any time with: dedupe.py undo --journal {args.journal}")


def cmd_undo(con, args):
    entries = [json.loads(l) for l in open(args.journal) if l.strip()]
    restored = 0
    for e in reversed(entries):
        if e.get("op") != "quarantine":
            continue
        if os.path.exists(e["dst"]) and not os.path.exists(e["src"]):
            os.makedirs(os.path.dirname(e["src"]), exist_ok=True)
            os.rename(e["dst"], e["src"])
            con.execute("UPDATE files SET path=? WHERE path=?",
                        (e["src"], e["dst"]))
            restored += 1
    con.commit()
    print(f"Restored {restored:,} files from quarantine.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--min-size", type=int, default=1_000_000)
    ap.add_argument("--category")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    p = sub.add_parser("plan")
    p.add_argument("--out", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--plan", required=True)
    p.add_argument("--journal", required=True)
    p = sub.add_parser("undo")
    p.add_argument("--journal", required=True)
    args = ap.parse_args()
    con = connect(args.db)
    {"scan": cmd_scan, "plan": cmd_plan,
     "apply": cmd_apply, "undo": cmd_undo}[args.cmd](con, args)
    con.close()


if __name__ == "__main__":
    main()
