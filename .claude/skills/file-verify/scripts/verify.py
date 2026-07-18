#!/usr/bin/env python3
"""Independently audit applied file-org journals against plan and disk.

Reads a JSONL journal written by apply_moves.py or dedupe.py apply and
verifies, with no shared logic with those scripts:
  - destination exists (files: is a file; units: is a directory)
  - source is gone (both existing = interrupted copy - flagged)
  - size matches the catalog record
  - SHA-256 spot-check on a sample, largest files first, where the
    catalog has a recorded full_hash
  - optional plan coverage: every actionable plan row appears in journal

Exit 0 = PASS, 1 = FAIL.
"""
import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--journal", required=True)
    ap.add_argument("--plan", help="plan CSV to check coverage against")
    ap.add_argument("--sample", type=int, default=200,
                    help="how many destinations to re-hash (0 = none)")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    entries = [json.loads(l) for l in open(args.journal) if l.strip()]
    ops = [e for e in entries if e.get("op") in ("move", "quarantine")]
    print(f"Auditing {len(ops):,} journaled operations ...")
    problems = []
    warnings = []

    # 1+2: existence and source-gone
    for e in ops:
        dst, src = e["dst"], e["src"]
        is_unit = e.get("kind") == "unit"
        ok = os.path.isdir(dst) if is_unit else os.path.isfile(dst)
        if not ok:
            problems.append(f"MISSING destination: {dst}")
            continue
        if os.path.exists(src):
            warnings.append(f"source still exists (interrupted move?):"
                            f" {src}")

    # 3: size check against catalog (dedupe apply updates path to dst;
    # move apply leaves the old src path in the catalog - accept either)
    file_ops = [e for e in ops if e.get("kind") != "unit"]
    checked_size = mismatched = 0
    hash_targets = []
    for e in file_ops:
        row = con.execute(
            "SELECT size, full_hash FROM files WHERE path=? OR path=?",
            (e["dst"], e["src"])).fetchone()
        if not row or not os.path.isfile(e["dst"]):
            continue
        size, fhash = row
        checked_size += 1
        actual = os.path.getsize(e["dst"])
        if actual != size:
            mismatched += 1
            problems.append(f"SIZE mismatch ({actual} != {size}): {e['dst']}")
        elif fhash:
            hash_targets.append((size, e["dst"], fhash))
    print(f"  sizes: {checked_size:,} checked, {mismatched} mismatches")

    # 4: hash spot-check, largest first
    if args.sample and hash_targets:
        hash_targets.sort(reverse=True)
        sample = hash_targets[:args.sample]
        bad = 0
        for size, dst, fhash in sample:
            try:
                if sha256(dst) != fhash:
                    bad += 1
                    problems.append(f"HASH mismatch: {dst}")
            except OSError as err:
                problems.append(f"UNREADABLE during hash check: {dst}"
                                f" ({err})")
        print(f"  hashes: {len(sample):,} re-hashed, {bad} mismatches")

    # 5: plan coverage
    if args.plan:
        journal_srcs = {e["src"] for e in ops}
        actionable = 0
        unaccounted = []
        for r in csv.DictReader(open(args.plan)):
            action = (r.get("action") or "move").strip().lower()
            if action in ("keep", "keep(in-unit)"):
                continue
            actionable += 1
            src = r.get("src") or r.get("path")
            if src not in journal_srcs:
                unaccounted.append(src)
        print(f"  plan coverage: {actionable - len(unaccounted):,}"
              f"/{actionable:,} actionable rows journaled")
        for src in unaccounted[:20]:
            problems.append(f"PLANNED but not journaled: {src}")
        if len(unaccounted) > 20:
            problems.append(f"... and {len(unaccounted) - 20} more"
                            " unaccounted plan rows")

    print()
    for wmsg in warnings[:20]:
        print(f"  WARN: {wmsg}")
    con.execute("CREATE TABLE IF NOT EXISTS pipeline_log("
                "stage TEXT, ts REAL, evidence TEXT)")
    verdict = "verify_fail" if problems else "verify_pass"
    import time as _time
    con.execute("INSERT INTO pipeline_log VALUES(?,?,?)",
                (verdict, _time.time(),
                 f"journal={args.journal} problems={len(problems)}"))
    con.commit()
    if problems:
        print(f"VERDICT: FAIL - {len(problems)} problems")
        for p in problems[:50]:
            print(f"  {p}")
        print("\nDo not proceed (no further applies, do not empty"
              " quarantine). Offer --undo with this journal.")
        sys.exit(1)
    extra = f", {len(warnings)} warnings" if warnings else ""
    print(f"VERDICT: PASS - {len(ops):,} operations verified{extra}")
    sys.exit(0)


if __name__ == "__main__":
    main()
