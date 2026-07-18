#!/usr/bin/env python3
"""The completion gate: prints the pipeline's true state, exit 0 only when
nothing is left hanging.

An agent running the file-org pipeline may ONLY claim the job is done by
pasting this command's output showing ALL CLEAR. Anything else is a false
report. The checks read the pipeline_log the stage scripts write and the
catalog itself - they cannot be satisfied by narration.

  python3 scripts/pipeline_status.py --db ~/file-org/catalog.db

Exit 0 = ALL CLEAR. Exit 1 = NOT DONE (blocking items listed).
"""
import argparse
import sqlite3
import sys
import time


def when(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "-"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.execute("CREATE TABLE IF NOT EXISTS pipeline_log("
                "stage TEXT, ts REAL, evidence TEXT)")
    blocking = []
    warn = []

    def latest(stage):
        return con.execute(
            "SELECT MAX(ts) FROM pipeline_log WHERE stage=?",
            (stage,)).fetchone()[0]

    print("=== file-org pipeline status ===")

    # 1. scans
    scans = con.execute("SELECT root, scanned_at, file_count, total_bytes"
                        " FROM scan_meta ORDER BY root").fetchall()
    if not scans:
        blocking.append("nothing scanned: run drive-inventory first")
        last_scan = 0
    else:
        last_scan = max(s[1] for s in scans)
        for root, ts, n, b in scans:
            print(f"  scanned   {root}: {n:,} files,"
                  f" {(b or 0) / 1e9:.1f} GB ({when(ts)})")

    # 2. classify freshness
    cls = latest("classify")
    if not cls:
        blocking.append("classify has never run")
    elif cls < last_scan:
        blocking.append("classify is STALE (a drive was re-scanned after"
                        " it): re-run classify.py")
    else:
        print(f"  classify  fresh ({when(cls)})")

    # 3. dedupe
    ds = latest("dedupe_scan")
    dw = latest("dedupe_waived")
    if ds and ds >= last_scan:
        print(f"  dedupe    scanned ({when(ds)})")
    elif dw and dw >= last_scan:
        print(f"  dedupe    WAIVED by user ({when(dw)})")
        warn.append("dedupe was waived, not run - user said so, fine")
    else:
        warn.append("no current dedupe scan (required before organizing;"
                    " gate in plan_moves.py enforces it)")

    # 4. every apply must be followed by a verify_pass, and its failed
    #    count must be zero (or a newer apply/verify supersedes it)
    applies = con.execute(
        "SELECT ts, evidence FROM pipeline_log WHERE stage='apply'"
        " ORDER BY ts").fetchall()
    passes = [r[0] for r in con.execute(
        "SELECT ts FROM pipeline_log WHERE stage='verify_pass'")]
    fails = [r[0] for r in con.execute(
        "SELECT ts FROM pipeline_log WHERE stage='verify_fail'")]
    for ts, ev in applies:
        newer_pass = any(p > ts for p in passes)
        newer_fail = max((f for f in fails if f > ts), default=None)
        pass_after_fail = newer_fail and any(p > newer_fail for p in passes)
        if not newer_pass:
            blocking.append(f"apply at {when(ts)} ({ev}) has NO verify pass"
                            " - run file-verify on its journal")
        elif newer_fail and not pass_after_fail:
            blocking.append(f"apply at {when(ts)} has a verify FAIL after"
                            " it with no later pass - resolve or undo")
        else:
            print(f"  apply     verified ({when(ts)}: {ev})")
        if "failed=" in ev:
            nfail = int(ev.rsplit("failed=", 1)[1].split()[0])
            if nfail:
                blocking.append(f"apply at {when(ts)} reported"
                                f" {nfail} FAILED operations - investigate,"
                                " re-plan the failures, or report them to"
                                " the user explicitly")
    if not applies:
        print("  apply     none yet (nothing on disk has been changed)")

    # 5. the user must have been shown a report since the last change
    rep = latest("report")
    last_apply = applies[-1][0] if applies else 0
    if applies and (not rep or rep < last_apply):
        blocking.append("no storage report generated since the last apply"
                        " - the user has not seen the result")
    elif rep:
        print(f"  report    current ({when(rep)})")

    print()
    for wmsg in warn:
        print(f"  note: {wmsg}")
    if blocking:
        print(f"VERDICT: NOT DONE - {len(blocking)} blocking item(s):")
        for b in blocking:
            print(f"  - {b}")
        sys.exit(1)
    print("VERDICT: ALL CLEAR - every applied change is verified and"
          " reported.")
    sys.exit(0)


if __name__ == "__main__":
    main()
