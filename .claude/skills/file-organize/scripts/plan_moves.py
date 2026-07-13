#!/usr/bin/env python3
"""Generate a move plan from the classified catalog. Touches nothing on disk.

Reads a layout config JSON (see SKILL.md) mapping category -> destination
directory (or null = leave in place). Units move as one row (kind=unit);
loose files move individually (kind=file). Output CSV columns:
  kind,category,src,dst,size
"""
import argparse
import csv
import json
import os
import sqlite3
import time
from collections import defaultdict


def dest_for(src, root, dest_root, keep_below, year=None):
    """Place src under dest_root, preserving useful parent context.
    With year set, group under <dest_root>/<year>/ instead of drive label."""
    if keep_below and src.startswith(keep_below.rstrip(os.sep) + os.sep):
        rel = os.path.relpath(src, keep_below)
        return os.path.join(dest_root, rel)
    parent = os.path.basename(os.path.dirname(src))
    if year:
        if parent:
            return os.path.join(dest_root, str(year), parent,
                                os.path.basename(src))
        return os.path.join(dest_root, str(year), os.path.basename(src))
    label = "".join(c if c.isalnum() or c in "-_ " else "_" for c in root)
    label = label.strip()
    if parent and parent.lower() != label.lower():
        return os.path.join(dest_root, label, parent, os.path.basename(src))
    return os.path.join(dest_root, label, os.path.basename(src))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--config", required=True, help="layout JSON")
    ap.add_argument("--out", required=True, help="plan CSV path")
    args = ap.parse_args()

    cfg = json.load(open(args.config))
    dests = cfg.get("destinations", {})
    keep_below = cfg.get("keep_subtree_below")
    year_cats = set(cfg.get("year_subfolders", []))
    con = sqlite3.connect(args.db)
    has_year = "media_year" in {
        r[1] for r in con.execute("PRAGMA table_info(files)")}

    rows = []
    seen_dst = set()
    stats = defaultdict(lambda: [0, 0])   # dest_root -> [count, bytes]
    skipped = defaultdict(int)

    def add(kind, category, src, dst_dir, size, root, year=None):
        dst = dest_for(src, root, dst_dir, keep_below, year)
        if os.path.abspath(dst) == os.path.abspath(src):
            skipped["already in place"] += 1
            return
        base, ext = os.path.splitext(dst)
        i = 1
        while dst.lower() in seen_dst:
            dst = f"{base}~{i}{ext}"
            i += 1
        seen_dst.add(dst.lower())
        rows.append({"kind": kind, "category": category, "src": src,
                     "dst": dst, "size": size})
        stats[dst_dir][0] += 1
        stats[dst_dir][1] += size

    # Units first: one row per unit directory.
    for path, ukind, b, root in con.execute(
            "SELECT u.path, u.kind, u.total_bytes,"
            " (SELECT root FROM files WHERE unit_id=u.id LIMIT 1)"
            " FROM units u"):
        d = dests.get(ukind)
        if not d:
            skipped[f"unit kind '{ukind}' unmapped/null"] += 1
            continue
        add("unit", ukind, path, d, b or 0, root or "")

    # Loose files.
    year_col = "media_year" if has_year else "NULL"
    for path, cat, size, root, myear, mtime in con.execute(
            f"SELECT path, category, size, root, {year_col}, mtime"
            " FROM files WHERE unit_id IS NULL"):
        d = dests.get(cat)
        if not d:
            skipped[f"category '{cat}' unmapped/null"] += 1
            continue
        year = None
        if cat in year_cats:
            year = myear or time.localtime(mtime).tm_year
        add("file", cat, path, d, size, root, year)

    rows.sort(key=lambda r: (r["kind"] != "unit", -r["size"]))
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "category", "src", "dst",
                                          "size"])
        w.writeheader()
        w.writerows(rows)

    print(f"=== Move plan: {args.out} ({len(rows):,} operations) ===")
    for d, (n, b) in sorted(stats.items(), key=lambda kv: -kv[1][1]):
        print(f"  -> {d}: {n:,} items, {b / 1e9:.2f} GB")
    if skipped:
        print("\nLeft in place:")
        for reason, n in sorted(skipped.items(), key=lambda kv: -kv[1]):
            print(f"  {n:,} x {reason}")
    print("\nReview the CSV, then run apply_moves.py --dry-run first.")
    con.close()


if __name__ == "__main__":
    main()
