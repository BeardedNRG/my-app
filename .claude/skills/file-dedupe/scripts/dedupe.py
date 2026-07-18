#!/usr/bin/env python3
"""Staged duplicate detection + quarantine over the file-org catalog.

Subcommands:
  scan   hash size-collision candidates (quick 64KB hash, then full SHA-256;
         parallel across --workers threads, with progress + ETA)
  dirs   find whole directory trees duplicated elsewhere (copied backups)
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
from concurrent.futures import ThreadPoolExecutor

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
    con.execute("CREATE TABLE IF NOT EXISTS pipeline_log("
                "stage TEXT, ts REAL, evidence TEXT)")
    return con


# ---- pipeline gates (mechanical; no override flags) ---------------------

def gate_log(con, stage, evidence=""):
    con.execute("INSERT INTO pipeline_log VALUES(?,?,?)",
                (stage, time.time(), evidence))
    con.commit()


def gate_block(problem, fix):
    sys.exit(f"GATE BLOCKED: {problem}\nDo this first: {fix}\n"
             "There is no override flag. Completing the step is the only"
             " way through this gate.")


def gate_latest(con, stage):
    return con.execute("SELECT MAX(ts) FROM pipeline_log WHERE stage=?",
                       (stage,)).fetchone()[0]


def require_fresh_classify(con):
    last_scan = con.execute(
        "SELECT MAX(scanned_at) FROM scan_meta").fetchone()[0] or 0
    ts = gate_latest(con, "classify")
    if not ts:
        gate_block("classification has never run on this catalog",
                   "file-classify classify.py --db <db>")
    if ts < last_scan:
        gate_block("a drive was re-scanned AFTER the last classification;"
                   " categories and units are stale",
                   "re-run file-classify classify.py --db <db>")


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


def parallel_hash(con, rows, column, quick, workers):
    """Hash rows [(id, path, size)] on a thread pool, write results to
    files.<column> in batches, print progress with ETA."""
    if not rows:
        return
    total_b = sum(min(r[2], QUICK_BYTES) if quick else r[2] for r in rows)
    done_b = 0
    t0 = time.time()

    def work(r):
        fid, path, size = r
        try:
            return fid, hash_file(path, quick=quick), size
        except OSError as e:
            print(f"  ERR {path}: {e}", file=sys.stderr)
            return fid, None, size

    batch = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, (fid, digest, size) in enumerate(ex.map(work, rows), 1):
            done_b += min(size, QUICK_BYTES) if quick else size
            if digest:
                batch.append((digest, fid))
            if len(batch) >= 500:
                con.executemany(
                    f"UPDATE files SET {column}=? WHERE id=?", batch)
                con.commit()
                batch.clear()
            if i % 2000 == 0 or (not quick and done_b and
                                 done_b % (10 << 30) < size):
                rate = done_b / max(time.time() - t0, 0.1)
                eta = (total_b - done_b) / max(rate, 1)
                print(f"  {i:,}/{len(rows):,} files,"
                      f" {done_b / 1e9:.1f}/{total_b / 1e9:.1f} GB,"
                      f" {rate / 1e6:.0f} MB/s, ETA {eta / 60:.0f} min",
                      flush=True)
    if batch:
        con.executemany(f"UPDATE files SET {column}=? WHERE id=?", batch)
    con.commit()


def cmd_scan(con, args):
    require_fresh_classify(con)
    where, params = candidates_where(args)
    rows = con.execute(
        f"SELECT id, path, size FROM files WHERE {where}"
        " AND quick_hash IS NULL", params).fetchall()
    print(f"Quick-hashing {len(rows):,} size-collision candidates"
          f" ({args.workers} workers) ...")
    parallel_hash(con, rows, "quick_hash", True, args.workers)

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
    print(f"Full-hashing {len(rows):,} files ({total_b / 1e9:.1f} GB,"
          f" {args.workers} workers) ...")
    parallel_hash(con, rows, "full_hash", False, args.workers)
    groups = con.execute(
        "SELECT COUNT(*) FROM (SELECT full_hash FROM files"
        " WHERE full_hash IS NOT NULL AND unit_id IS NULL"
        " GROUP BY full_hash HAVING COUNT(*) > 1)").fetchone()[0]
    gate_log(con, "dedupe_scan", f"{groups} duplicate groups")
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
    require_fresh_classify(con)
    if not gate_latest(con, "dedupe_scan"):
        gate_block("no dedupe scan has been logged for this catalog",
                   "dedupe.py --db <db> scan")
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
    gate_log(con, "plan_hash", hash_file(args.out))
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


def cmd_dirs(con, args):
    """Find whole directory trees duplicated elsewhere (copied backups).

    Signature of a dir = hash of its sorted contents: (name, size, full_hash)
    for files, (name, subtree-signature) for subdirs. Candidate groups are
    matched on names+sizes first; --verify full-hashes their files so the
    match is proven byte-identical.
    """
    dir_files = defaultdict(list)
    for path, size, fh in con.execute(
            "SELECT path, size, full_hash FROM files WHERE is_symlink=0"):
        dir_files[os.path.dirname(path)].append(
            (os.path.basename(path), size, fh))
    all_dirs = set()
    for d in dir_files:
        while d and d not in all_dirs:
            all_dirs.add(d)
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    subdirs = defaultdict(list)
    for d in all_dirs:
        p = os.path.dirname(d)
        if p != d and p in all_dirs:
            subdirs[p].append(d)

    def compute_sigs(use_hashes):
        sigs = {}
        # a parent is always a strict prefix of its children, so processing
        # longest paths first guarantees children are computed before parents
        for d in sorted(all_dirs, key=len, reverse=True):
            entries = []
            total = 0
            count = 0
            for name, size, fh in dir_files.get(d, ()):
                entries.append(("f", name, size, fh if use_hashes else ""))
                total += size
                count += 1
            for sd in subdirs.get(d, ()):
                s2, b2, c2 = sigs[sd]
                entries.append(("d", os.path.basename(sd), b2, s2))
                total += b2
                count += c2
            h = hashlib.sha256(repr(sorted(entries)).encode()).hexdigest()
            sigs[d] = (h, total, count)
        return sigs

    def group(sigs):
        by_sig = defaultdict(list)
        for d, (s, total, count) in sigs.items():
            if count >= args.min_files and total >= args.min_dir_bytes:
                by_sig[(s, total, count)].append(d)
        groups = {k: v for k, v in by_sig.items() if len(v) > 1}
        # keep only maximal trees: drop a group if every member sits inside
        # a member of another (larger) reported group
        reported = []
        covered = set()
        for (s, total, count), dirs in sorted(
                groups.items(), key=lambda kv: -kv[0][1]):
            if all(any(d.startswith(c + os.sep) for c in covered)
                   for d in dirs):
                continue
            reported.append((total, count, sorted(dirs)))
            covered.update(dirs)
        return reported

    sigs = compute_sigs(use_hashes=False)
    candidates = group(sigs)
    if args.verify and candidates:
        need = []
        for _, _, dirs in candidates:
            for d in dirs:
                like = d.rstrip(os.sep) + os.sep + "%"
                need += con.execute(
                    "SELECT id, path, size FROM files WHERE full_hash IS NULL"
                    " AND is_symlink=0 AND (path LIKE ? OR path=?)",
                    (like, d)).fetchall()
        need = list({r[0]: r for r in need}.values())
        print(f"Verifying: full-hashing {len(need):,} files"
              f" ({sum(r[2] for r in need) / 1e9:.1f} GB) ...")
        parallel_hash(con, need, "full_hash", False, args.workers)
        dir_files.clear()
        for path, size, fh in con.execute(
                "SELECT path, size, full_hash FROM files WHERE is_symlink=0"):
            dir_files[os.path.dirname(path)].append(
                (os.path.basename(path), size, fh))
        candidates = group(compute_sigs(use_hashes=True))

    label = "verified byte-identical" if args.verify else \
        "matched on names+sizes (run with --verify to prove)"
    print(f"\n=== Duplicate directory trees — {label} ===")
    if not candidates:
        print("  none found at current thresholds"
              f" (min {args.min_files} files, {args.min_dir_bytes} bytes)")
        return
    wasted = 0
    for total, count, dirs in candidates:
        wasted += total * (len(dirs) - 1)
        print(f"\n  {total / 1e9:.2f} GB x {len(dirs)} copies"
              f" ({count:,} files each):")
        for d in dirs:
            print(f"    {d}")
    print(f"\nTotal reclaimable if one copy of each is kept:"
          f" {wasted / 1e9:.2f} GB")
    print("Review with the user, then either quarantine via the file-level"
          " plan/apply flow, or move redundant trees to Archive with"
          " file-organize.")


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
    h = hash_file(args.plan)
    known = con.execute(
        "SELECT 1 FROM pipeline_log WHERE stage IN"
        " ('plan_hash','plan_edited') AND evidence=?", (h,)).fetchone()
    if not known:
        if args.user_edited_plan:
            gate_log(con, "plan_edited", h)
            print("Plan re-registered as user-edited (audit-logged).")
        else:
            gate_block(
                "this plan file was not produced by a 'plan' step on this"
                " catalog (or was modified since)",
                "regenerate it with 'plan', or - ONLY if the USER edited it"
                " and approved the edits - re-run apply with"
                " --user-edited-plan")
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
    gate_log(con, "apply",
             f"dedupe journal={args.journal} moved={moved} failed={errors}")
    print(f"Done: {moved:,} files quarantined, {errors} errors."
          f"\nQuarantine folders are named '{QUARANTINE}' at each drive root."
          f"\nUndo any time with: dedupe.py undo --journal {args.journal}"
          "\nNOT COMPLETE until file-verify passes on this journal.")


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
    ap.add_argument("--workers", type=int,
                    default=min(8, os.cpu_count() or 4),
                    help="hashing threads (default: min(8, cpu count))")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    p = sub.add_parser("dirs")
    p.add_argument("--verify", action="store_true",
                   help="full-hash candidate trees to prove byte-identity")
    p.add_argument("--min-files", type=int, default=3)
    p.add_argument("--min-dir-bytes", type=int, default=10_000_000)
    p = sub.add_parser("plan")
    p.add_argument("--out", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--plan", required=True)
    p.add_argument("--journal", required=True)
    p.add_argument("--user-edited-plan", action="store_true",
                   help="accept a plan CSV the USER edited after 'plan'"
                        " generated it (audit-logged; never pass this"
                        " without explicit user approval)")
    p = sub.add_parser("undo")
    p.add_argument("--journal", required=True)
    args = ap.parse_args()
    con = connect(args.db)
    {"scan": cmd_scan, "dirs": cmd_dirs, "plan": cmd_plan,
     "apply": cmd_apply, "undo": cmd_undo}[args.cmd](con, args)
    con.close()


if __name__ == "__main__":
    main()
