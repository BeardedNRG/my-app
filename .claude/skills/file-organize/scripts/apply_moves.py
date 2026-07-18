#!/usr/bin/env python3
"""Execute (or undo) an approved move plan with verification + journal.

- Same filesystem: os.rename (instant).
- Cross filesystem: copy -> verify (size + SHA-256 for files; per-file for
  unit directories) -> delete source. On any verify failure the source is
  kept and the row is reported as FAILED.
- Collisions get ~1, ~2 suffixes; nothing is ever overwritten.
- Every completed operation is appended to a JSONL journal; --undo replays
  it in reverse (moves back; cross-fs undo copies back the same way).
"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def same_fs(a, b):
    da = os.stat(a).st_dev
    p = b
    while not os.path.exists(p):
        p = os.path.dirname(p) or os.sep
    return da == os.stat(p).st_dev


def uncollide(dst):
    base, ext = os.path.splitext(dst)
    i = 1
    while os.path.exists(dst):
        dst = f"{base}~{i}{ext}"
        i += 1
    return dst


def verify_copy_file(src, dst):
    if os.path.getsize(src) != os.path.getsize(dst):
        return False
    return sha256(src) == sha256(dst)


def move_file(src, dst, dry):
    dst = uncollide(dst)
    if dry:
        print(f"  [dry] {src} -> {dst}")
        return dst, "dry"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if same_fs(src, os.path.dirname(dst)):
        os.rename(src, dst)
        return dst, "renamed"
    shutil.copy2(src, dst)
    if not verify_copy_file(src, dst):
        os.remove(dst)
        raise IOError("verification mismatch after copy")
    os.remove(src)
    return dst, "copied+verified"


def move_dir(src, dst, dry):
    dst = uncollide(dst)
    if dry:
        print(f"  [dry] DIR {src} -> {dst}")
        return dst, "dry"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if same_fs(src, os.path.dirname(dst)):
        os.rename(src, dst)
        return dst, "renamed"
    shutil.copytree(src, dst, symlinks=True)
    # Verify every regular file before removing the source tree.
    for root, _, names in os.walk(src):
        for n in names:
            s = os.path.join(root, n)
            d = os.path.join(dst, os.path.relpath(s, src))
            if os.path.islink(s):
                continue
            if not (os.path.isfile(d) and verify_copy_file(s, d)):
                shutil.rmtree(dst, ignore_errors=True)
                raise IOError(f"verification mismatch: {s}")
    shutil.rmtree(src)
    return dst, "copied+verified"


def gate_check(args):
    """Mechanical interlocks: the plan must come from plan_moves.py on this
    catalog, and a real apply must be preceded by a dry-run of the exact
    same plan file. Logs this run's stage on success."""
    con = sqlite3.connect(args.db)
    con.execute("CREATE TABLE IF NOT EXISTS pipeline_log("
                "stage TEXT, ts REAL, evidence TEXT)")
    h = sha256(args.plan) if os.path.exists(args.plan) else None
    if h is None:
        sys.exit(f"GATE BLOCKED: plan file not found: {args.plan}")

    def known(*stages):
        q = ",".join("?" * len(stages))
        return con.execute(
            f"SELECT 1 FROM pipeline_log WHERE stage IN ({q})"
            " AND evidence=?", (*stages, h)).fetchone()

    if not known("move_plan_hash", "move_plan_edited"):
        if args.user_edited_plan:
            con.execute("INSERT INTO pipeline_log VALUES("
                        "'move_plan_edited',?,?)", (time.time(), h))
            con.commit()
            print("Plan re-registered as user-edited (audit-logged).")
        else:
            sys.exit(
                "GATE BLOCKED: this plan was not produced by plan_moves.py"
                " on this catalog (or was modified since).\nDo this first:"
                " regenerate it with plan_moves.py, or - ONLY if the USER"
                " edited it and approved the edits - re-run with"
                " --user-edited-plan.\nThere is no other way through.")
    if not args.dry_run and not known("move_dryrun"):
        sys.exit(
            "GATE BLOCKED: no dry-run has been done for this exact plan"
            " file.\nDo this first: re-run with --dry-run, show the user,"
            " THEN apply for real.\nThere is no override flag.")
    return con, h


def gate_log(con, stage, evidence):
    con.execute("INSERT INTO pipeline_log VALUES(?,?,?)",
                (stage, time.time(), evidence))
    con.commit()


def apply_plan(args):
    con, plan_hash = gate_check(args)
    rows = list(csv.DictReader(open(args.plan)))
    journal = None if args.dry_run else open(args.journal, "a")
    ok = failed = 0
    total = len(rows)
    for i, r in enumerate(rows, 1):
        src, dst, kind = r["src"], r["dst"], r["kind"]
        try:
            if not os.path.exists(src):
                raise FileNotFoundError("source vanished")
            mover = move_dir if kind == "unit" else move_file
            final_dst, how = mover(src, dst, args.dry_run)
        except (OSError, IOError) as e:
            print(f"  FAILED [{i}/{total}] {src}: {e}", file=sys.stderr)
            failed += 1
            continue
        ok += 1
        if journal:
            journal.write(json.dumps(
                {"op": "move", "kind": kind, "src": src, "dst": final_dst,
                 "how": how, "ts": time.time()}) + "\n")
            if ok % 100 == 0:
                journal.flush()
        if ok % 500 == 0 or kind == "unit":
            print(f"  [{i}/{total}] {how}: {src} -> {final_dst}", flush=True)
    if journal:
        journal.close()
    label = "DRY RUN — nothing moved" if args.dry_run else "Applied"
    print(f"\n{label}: {ok:,} ok, {failed:,} failed of {total:,}.")
    if args.dry_run:
        gate_log(con, "move_dryrun", plan_hash)
        print("Dry-run logged. Show this output to the user before the"
              " real apply.")
    else:
        gate_log(con, "apply",
                 f"move journal={args.journal} moved={ok} failed={failed}")
        print(f"Undo with: apply_moves.py --undo --journal {args.journal}")
        print("NOT COMPLETE until file-verify passes on this journal,"
              " then re-run drive-inventory on affected roots.")


def undo(args):
    entries = [json.loads(l) for l in open(args.journal) if l.strip()]
    restored = failed = 0
    for e in reversed(entries):
        if e.get("op") != "move":
            continue
        src, dst = e["src"], e["dst"]  # original src, current location dst
        try:
            if not os.path.exists(dst):
                raise FileNotFoundError("moved file no longer at destination")
            mover = move_dir if e["kind"] == "unit" else move_file
            mover(dst, src, dry=False)
            restored += 1
        except (OSError, IOError) as err:
            print(f"  FAILED undo {dst}: {err}", file=sys.stderr)
            failed += 1
    print(f"Undo complete: {restored:,} restored, {failed:,} failed.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", help="catalog DB (required except for --undo)")
    ap.add_argument("--plan", help="plan CSV from plan_moves.py")
    ap.add_argument("--journal", required=True, help="JSONL journal path")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--undo", action="store_true")
    ap.add_argument("--user-edited-plan", action="store_true",
                    help="accept a plan CSV the USER edited after"
                         " plan_moves.py generated it (audit-logged; never"
                         " pass without explicit user approval)")
    args = ap.parse_args()
    if not args.undo and not args.db:
        ap.error("--db is required (gate tracking lives in the catalog)")
    if args.undo:
        undo(args)
    else:
        if not args.plan:
            ap.error("--plan is required unless --undo")
        apply_plan(args)


if __name__ == "__main__":
    main()
