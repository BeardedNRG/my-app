#!/usr/bin/env python3
"""One-command drive survey - no agent needed, zero Claude usage.

    python3 run_survey.py D:\\  E:\\
    python3 run_survey.py /mnt/d /mnt/e

Scans the drives/folders you list, classifies everything, and writes a
visual dashboard, then tells you where it is. Read-only: nothing on your
drives is moved, changed, or deleted. Safe to run as many times as you
like; re-runs update the same catalog.

Catalog and report land in ~/file-org/ (created automatically).
"""
import os
import subprocess
import sys
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.dirname(os.path.dirname(HERE))  # .../.claude/skills
HOME = os.path.join(os.path.expanduser("~"), "file-org")
DB = os.path.join(HOME, "catalog.db")
REPORT = os.path.join(HOME, "storage-report.html")


def run(script_rel, *argv):
    script = os.path.join(SKILLS, *script_rel)
    cmd = [sys.executable, script] + list(argv)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(f"\nStep failed: {os.path.basename(script)} - the message"
                 " above says what it needs.")


def main():
    roots = [r for r in sys.argv[1:] if not r.startswith("-")]
    if not roots:
        sys.exit(__doc__)
    for r in roots:
        if not os.path.isdir(r):
            sys.exit(f"Not a folder/drive I can see: {r}")
    os.makedirs(HOME, exist_ok=True)

    print(f"=== 1/3 Scanning {len(roots)} location(s)"
          " (biggest drives take a few minutes) ===")
    for r in roots:
        run(("drive-inventory", "scripts", "scan.py"), "--db", DB,
            os.path.abspath(r))

    print("\n=== 2/3 Classifying (VMs, installers, photos, backups...) ===")
    run(("file-classify", "scripts", "classify.py"), "--db", DB)

    print("\n=== 3/3 Building your dashboard ===")
    run(("storage-report", "scripts", "report.py"), "--db", DB,
        "--out", REPORT)

    print("\n" + "=" * 60)
    print(f"DONE. Open this file in your browser:\n  {REPORT}")
    print("=" * 60)
    print("Nothing on your drives was changed. Next steps (finding")
    print("duplicates, moving things) are done with Claude so every")
    print("change gets shown to you first.")
    try:
        webbrowser.open("file://" + REPORT)
    except Exception:
        pass


if __name__ == "__main__":
    main()
