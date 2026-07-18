#!/usr/bin/env python3
"""Rank sibling folders: which is the real working copy, which are
installer payloads, which are just clones.

Generic - works on ANY folder of candidate copies of ANY project, no
project-specific knowledge. Give it a parent directory; it ranks the
immediate subfolders (or pass --dirs for an explicit list). Signals:

  uniqueness   files whose content exists in no other candidate - the
               folder someone actually worked in accumulates unique files;
               clones and installers have none
  activity     newest change + how spread out edit times are; real work
               spans weeks/months, an extracted installer's timestamps
               land in one tight cluster
  source       code files, .git, project/config markers (units from
               classify.py)
  completeness file count / size relative to siblings
  clone check  candidates with identical (relative path, size) content
               sets are grouped - ranked once, labeled clones
  installer    app_install/game units, exe+dll-heavy content, or a tight
               timestamp cluster with no source - labeled, ranked last

Run AFTER drive-inventory scan + classify on a catalog containing the
parent. `dedupe.py scan` beforehand sharpens uniqueness with real hashes
(falls back to name+size matching without).

  python3 scripts/rank_builds.py --db <catalog.db> <parent-dir>
  python3 scripts/rank_builds.py --db <catalog.db> --dirs A B C
"""
import argparse
import math
import os
import sqlite3
import sys
import time
from collections import defaultdict


def gate_fresh_classify(con):
    con.execute("CREATE TABLE IF NOT EXISTS pipeline_log("
                "stage TEXT, ts REAL, evidence TEXT)")
    last_scan = con.execute(
        "SELECT MAX(scanned_at) FROM scan_meta").fetchone()[0] or 0
    ts = con.execute("SELECT MAX(ts) FROM pipeline_log WHERE"
                     " stage='classify'").fetchone()[0]
    if not ts or ts < last_scan:
        sys.exit("GATE BLOCKED: classification is missing or older than"
                 " the latest scan.\nDo this first: classify.py --db <db>")


def load_candidate(con, d):
    like = d.rstrip(os.sep) + os.sep + "%"
    rows = con.execute(
        "SELECT path, name, size, mtime, category, ext, full_hash"
        " FROM files WHERE path LIKE ?", (like,)).fetchall()
    return rows


def analyze(d, rows):
    c = {"dir": d, "n": len(rows), "bytes": 0, "newest": 0, "code": 0,
         "git": False, "exe_dll": 0, "mtimes": [], "keys": set(),
         "relsig": set(), "unit_kinds": set()}
    for path, name, size, mtime, cat, ext, fh in rows:
        c["bytes"] += size
        c["newest"] = max(c["newest"], mtime)
        c["mtimes"].append(mtime)
        rel = os.path.relpath(path, d)
        c["relsig"].add((rel.lower(), size))
        c["keys"].add(fh if fh else (name.lower(), size))
        if cat in ("code", "code_project"):
            c["code"] += 1
        if cat in ("app_install", "game"):
            c["unit_kinds"].add(cat)
        if ext in ("exe", "dll", "msi"):
            c["exe_dll"] += 1
        if os.sep + ".git" + os.sep in path or name == ".git":
            c["git"] = True
    return c


def spread_days(mtimes):
    if len(mtimes) < 2:
        return 0.0
    s = sorted(mtimes)
    lo = s[max(0, len(s) // 10)]
    hi = s[min(len(s) - 1, len(s) * 9 // 10)]
    return (hi - lo) / 86400


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("parent", nargs="?",
                    help="rank the immediate subfolders of this directory")
    ap.add_argument("--dirs", nargs="+",
                    help="rank this explicit list of directories instead")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    gate_fresh_classify(con)

    if args.dirs:
        cand_dirs = [os.path.abspath(d) for d in args.dirs]
    elif args.parent:
        parent = os.path.abspath(args.parent)
        like = parent.rstrip(os.sep) + os.sep + "%"
        subs = set()
        plen = len(parent.rstrip(os.sep)) + 1
        for (path,) in con.execute(
                "SELECT path FROM files WHERE path LIKE ?", (like,)):
            rest = path[plen:]
            if os.sep in rest:
                subs.add(os.path.join(parent, rest.split(os.sep)[0]))
        cand_dirs = sorted(subs)
    else:
        ap.error("give a parent directory or --dirs")
    if not cand_dirs:
        sys.exit(f"No cataloged subfolders under {args.parent}."
                 " Scan it first with drive-inventory.")

    cands = []
    for d in cand_dirs:
        rows = load_candidate(con, d)
        if rows:
            cands.append(analyze(d, rows))
    if not cands:
        sys.exit("No files found under any candidate - is the catalog"
                 " current?")

    # clone groups: identical (relative path, size) content sets
    sig_groups = defaultdict(list)
    for i, c in enumerate(cands):
        sig_groups[frozenset(c["relsig"])].append(i)
    clone_of = {}
    for members in sig_groups.values():
        for m in members[1:]:
            clone_of[m] = members[0]

    # uniqueness across candidates
    key_owners = defaultdict(set)
    for i, c in enumerate(cands):
        for k in c["keys"]:
            key_owners[k].add(i)
    for i, c in enumerate(cands):
        unique = sum(1 for k in c["keys"] if key_owners[k] == {i})
        c["unique_frac"] = unique / max(len(c["keys"]), 1)
        c["unique_n"] = unique

    now = time.time()
    max_n = max(c["n"] for c in cands)
    for i, c in enumerate(cands):
        sd = spread_days(c["mtimes"])
        tight = sd < 0.1 and c["n"] > 3
        binary_heavy = c["exe_dll"] / max(c["n"], 1) > 0.4
        c["installer"] = bool(c["unit_kinds"]) or \
            (tight and c["code"] == 0) or (binary_heavy and c["code"] == 0)
        age_days = (now - c["newest"]) / 86400 if c["newest"] else 9999
        score = 0.0
        score += 40 * c["unique_frac"]
        score += 20 * max(0.0, 1 - age_days / 365)          # recent activity
        score += 15 * min(1.0, sd / 30)                     # sustained work
        score += 10 * min(1.0, c["code"] / 20)
        score += 5 if c["git"] else 0
        score += 10 * (c["n"] / max_n)
        if c["installer"]:
            score -= 60
        c["score"] = score
        c["spread"] = sd

    order = sorted(range(len(cands)), key=lambda i: -cands[i]["score"])
    print(f"=== Build ranking: {len(cands)} candidates ===\n")
    rank = 0
    shown = {}
    for i in order:
        c = cands[i]
        base = os.path.basename(c["dir"]) or c["dir"]
        if i in clone_of and clone_of[i] in shown:
            print(f"      = clone of #{shown[clone_of[i]]}: {base}"
                  f"  (byte-layout identical)")
            continue
        rank += 1
        shown[i] = rank
        tags = []
        if c["installer"]:
            tags.append("INSTALLER/PAYLOAD")
        if c["git"]:
            tags.append("git repo")
        if c["unique_n"]:
            tags.append(f"{c['unique_n']:,} unique files"
                        f" ({c['unique_frac']:.0%})")
        newest = time.strftime("%Y-%m-%d", time.localtime(c["newest"]))
        print(f"  #{rank}  {base}  [{c['score']:.0f} pts]"
              f"  {'; '.join(tags) if tags else 'no distinguishing marks'}")
        print(f"       {c['n']:,} files, {c['bytes'] / 1e9:.2f} GB,"
              f" {c['code']} source files, last change {newest},"
              f" activity spread {c['spread']:.0f} days")
    best = cands[order[0]]
    print()
    if best["installer"]:
        print("VERDICT: no candidate looks like a working copy - every"
              " folder here is an installer payload or clone. The real"
              " build likely lives elsewhere; rank a different parent.")
    else:
        print(f"VERDICT: revive from '{os.path.basename(best['dir'])}'"
              f" - most unique content, most recent sustained activity."
              " Diff it against #2 before discarding anything.")


if __name__ == "__main__":
    main()
