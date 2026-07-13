#!/usr/bin/env python3
"""Near-duplicate photo detection via perceptual hashing (dHash).

Finds photos that are the *same picture* even when the files differ:
resized copies, re-saved/re-compressed exports, minor edits. Requires
Pillow (`pip install Pillow`) — the one optional dependency in the
file-org pipeline; everything else is stdlib.

Subcommands:
  scan   compute a 64-bit dHash (+ pixel dimensions) for every cataloged
         image; stored in files.phash / files.img_w / files.img_h
  plan   cluster hashes within --distance Hamming bits, pick the keeper
         (highest resolution, then largest file), write a plan CSV that
         `dedupe.py apply` can quarantine — REVIEW IT FIRST: near-dups
         are similar, not identical, so a human look matters here

Files inside units are hashed and shown in groups (so you can see that a
loose copy matches a photo-library original) but are never marked for
quarantine — only loose files get a 'quarantine' action.
"""
import argparse
import csv
import os
import sqlite3
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

try:
    from PIL import Image
except ImportError:
    sys.exit("near_dupes.py needs Pillow: pip install Pillow")

Image.MAX_IMAGE_PIXELS = None  # don't refuse big panoramas; we only read

HASH_EXTS = ("jpg", "jpeg", "png", "gif", "bmp", "webp", "tif", "tiff",
             "heic")


def connect(db):
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    cols = {r[1] for r in con.execute("PRAGMA table_info(files)")}
    for col, typ in (("phash", "TEXT"), ("img_w", "INTEGER"),
                     ("img_h", "INTEGER")):
        if col not in cols:
            con.execute(f"ALTER TABLE files ADD COLUMN {col} {typ}")
    return con


def dhash(path):
    """64-bit difference hash + original dimensions, or (None, 0, 0)."""
    with Image.open(path) as im:
        w, h = im.size
        g = im.convert("L").resize((9, 8), Image.BILINEAR)
        px = g.tobytes()  # 72 grayscale bytes, row-major
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (px[row * 9 + col] > px[row * 9 + col + 1])
    return f"{bits:016x}", w, h


def cmd_scan(con, args):
    rows = con.execute(
        "SELECT id, path FROM files WHERE phash IS NULL AND is_symlink=0"
        " AND ext IN (%s)" % ",".join("?" * len(HASH_EXTS)),
        HASH_EXTS).fetchall()
    print(f"Perceptual-hashing {len(rows):,} images"
          f" ({args.workers} workers) ...")
    t0 = time.time()

    def work(r):
        fid, path = r
        try:
            return (fid, *dhash(path))
        except Exception as e:  # Pillow raises many types on bad images
            print(f"  ERR {path}: {e}", file=sys.stderr)
            return fid, None, 0, 0

    batch = []
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for fid, ph, w, h in ex.map(work, rows):
            if ph:
                batch.append((ph, w, h, fid))
            done += 1
            if len(batch) >= 500:
                con.executemany("UPDATE files SET phash=?, img_w=?, img_h=?"
                                " WHERE id=?", batch)
                con.commit()
                batch.clear()
            if done % 2000 == 0:
                rate = done / max(time.time() - t0, 0.1)
                print(f"  {done:,}/{len(rows):,}"
                      f" ({rate:.0f} img/s,"
                      f" ETA {(len(rows) - done) / max(rate, 1) / 60:.0f}"
                      " min)", flush=True)
    con.executemany("UPDATE files SET phash=?, img_w=?, img_h=? WHERE id=?",
                    batch)
    con.commit()
    print(f"Done: hashed {done:,} images in {time.time() - t0:.0f}s."
          " Run 'plan'.")


def hamming(a, b):
    return bin(a ^ b).count("1")


def cluster(rows, max_dist):
    """Union-find clustering; candidate pairs share one of eight 8-bit
    chunks (pigeonhole: any pair within 7 bits must collide on a chunk)."""
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    buckets = defaultdict(list)
    ints = [int(r["phash"], 16) for r in rows]
    for i, v in enumerate(ints):
        for c in range(8):
            buckets[(c, (v >> (c * 8)) & 0xFF)].append(i)
    for members in buckets.values():
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                i, j = members[a], members[b]
                if find(i) != find(j) and hamming(ints[i], ints[j]) <= max_dist:
                    union(i, j)
    groups = defaultdict(list)
    for i in range(len(rows)):
        groups[find(i)].append(rows[i])
    return [g for g in groups.values() if len(g) > 1]


def cmd_plan(con, args):
    if args.distance > 7:
        sys.exit("--distance above 7 breaks candidate bucketing; use <= 7")
    rows = [dict(zip(("id", "path", "root", "size", "phash", "img_w",
                      "img_h", "unit_id"), r))
            for r in con.execute(
                "SELECT id, path, root, size, phash, img_w, img_h, unit_id"
                " FROM files WHERE phash IS NOT NULL")]
    print(f"Clustering {len(rows):,} hashed images"
          f" (Hamming distance <= {args.distance}) ...")
    groups = cluster(rows, args.distance)

    plan = []
    quarantine_bytes = 0
    for g in groups:
        g.sort(key=lambda r: ((r["img_w"] or 0) * (r["img_h"] or 0),
                              r["size"]), reverse=True)
        keeper = g[0]
        for m in g[1:]:
            in_unit = m["unit_id"] is not None
            action = "keep(in-unit)" if in_unit else "quarantine"
            if not in_unit:
                quarantine_bytes += m["size"]
            plan.append({
                "action": action, "path": m["path"], "root": m["root"],
                "size": m["size"], "keeper": keeper["path"],
                "hash": m["phash"]})
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["action", "path", "root", "size",
                                          "keeper", "hash"])
        w.writeheader()
        w.writerows(sorted(plan, key=lambda r: -r["size"]))
    nq = sum(1 for r in plan if r["action"] == "quarantine")
    print(f"=== Near-duplicate plan: {args.out} ===")
    print(f"  {len(groups):,} visually-matching groups")
    print(f"  {nq:,} loose copies marked quarantine"
          f" ({quarantine_bytes / 1e9:.2f} GB)")
    print(f"  {len(plan) - nq:,} matches inside units marked keep(in-unit)")
    print("\nTop 15 groups:")
    for g in sorted(groups, key=lambda g: -sum(r["size"] for r in g))[:15]:
        k = g[0]
        print(f"  {len(g)} versions, best {k['img_w']}x{k['img_h']}:"
              f" {k['path']}")
        for m in g[1:3]:
            print(f"      ~ {m['img_w']}x{m['img_h']} {m['path']}")
    print("\nIMPORTANT: these are visually similar, not byte-identical —"
          "\nhave the user spot-check before applying with:"
          "\n  dedupe.py apply --plan ... --journal ...")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--workers", type=int,
                    default=min(8, os.cpu_count() or 4))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    p = sub.add_parser("plan")
    p.add_argument("--out", required=True)
    p.add_argument("--distance", type=int, default=4,
                   help="max Hamming distance, 0-7 (default 4;"
                        " higher = looser matching)")
    args = ap.parse_args()
    con = connect(args.db)
    {"scan": cmd_scan, "plan": cmd_plan}[args.cmd](con, args)
    con.close()


if __name__ == "__main__":
    main()
