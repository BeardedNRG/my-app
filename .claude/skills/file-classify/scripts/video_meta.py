#!/usr/bin/env python3
"""Read video resolution + duration into the catalog.

Fills files.video_w / files.video_h / files.duration_s so the user can
tell 4K keepers from potato-quality copies, and the organizer/report can
distinguish them. Two engines:

  - ffprobe (used automatically when on PATH): all containers/codecs
  - stdlib fallback: MP4/MOV/M4V (box parsing) and AVI (RIFF header) -
    no dependencies, covers the most common formats; MKV/WMV/FLV are
    skipped with a note to install ffmpeg for full coverage

Usage:
  python3 scripts/video_meta.py --db ~/file-org/catalog.db [--workers N]
"""
import argparse
import json
import os
import shutil
import sqlite3
import struct
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

STDLIB_EXTS = ("mp4", "m4v", "mov", "avi")
FFPROBE_EXTS = STDLIB_EXTS + ("mkv", "webm", "wmv", "flv", "mpg", "mpeg",
                              "ts", "vob", "3gp")


# ---- stdlib MP4/MOV -----------------------------------------------------

def mp4_meta(path):
    """(width, height, seconds) from moov/mvhd + tkhd; zeros if absent."""
    w = h = 0
    dur = 0.0

    def walk(f, start, end, depth=0):
        nonlocal w, h, dur
        pos = start
        while pos + 8 <= end and depth < 6:
            f.seek(pos)
            hdr = f.read(8)
            if len(hdr) < 8:
                return
            size = struct.unpack(">I", hdr[:4])[0]
            typ = hdr[4:8]
            hsize = 8
            if size == 1:
                big = f.read(8)
                size = struct.unpack(">Q", big)[0]
                hsize = 16
            elif size == 0:
                size = end - pos
            if size < hsize:
                return
            if typ in (b"moov", b"trak", b"mdia"):
                walk(f, pos + hsize, pos + size, depth + 1)
            elif typ == b"mvhd":
                p = f.read(min(size - hsize, 32))
                if p:
                    if p[0] == 1 and len(p) >= 32:  # version 1
                        ts = struct.unpack(">I", p[20:24])[0]
                        d = struct.unpack(">Q", p[24:32])[0]
                    elif len(p) >= 20:
                        ts = struct.unpack(">I", p[12:16])[0]
                        d = struct.unpack(">I", p[16:20])[0]
                    else:
                        ts, d = 0, 0
                    if ts:
                        dur = max(dur, d / ts)
            elif typ == b"tkhd":
                p = f.read(size - hsize)
                if len(p) >= 8:  # width/height: last 8 bytes, 16.16 fixed
                    tw = struct.unpack(">I", p[-8:-4])[0] >> 16
                    th = struct.unpack(">I", p[-4:])[0] >> 16
                    if tw * th > w * h:
                        w, h = tw, th
            pos += size

    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            walk(f, 0, f.tell())
    except OSError:
        pass
    return w, h, dur


def avi_meta(path):
    """(width, height, seconds) from the avih header near the file start."""
    try:
        with open(path, "rb") as f:
            head = f.read(4096)
    except OSError:
        return 0, 0, 0.0
    if head[:4] != b"RIFF" or head[8:12] != b"AVI ":
        return 0, 0, 0.0
    i = head.find(b"avih")
    if i < 0 or i + 48 > len(head):
        return 0, 0, 0.0
    p = head[i + 8:]
    usec_per_frame, = struct.unpack("<I", p[0:4])
    total_frames, = struct.unpack("<I", p[16:20])
    w, = struct.unpack("<I", p[32:36])
    h, = struct.unpack("<I", p[36:40])
    dur = total_frames * usec_per_frame / 1e6 if usec_per_frame else 0.0
    return w, h, dur


def ffprobe_meta(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-show_format", path],
            capture_output=True, timeout=60).stdout
        info = json.loads(out)
    except Exception:
        return 0, 0, 0.0
    w = h = 0
    for s in info.get("streams", []):
        if s.get("codec_type") == "video":
            w = max(w, int(s.get("width") or 0))
            h = max(h, int(s.get("height") or 0))
    dur = float(info.get("format", {}).get("duration") or 0)
    return w, h, dur


def res_label(w, h):
    p = min(w, h)
    if p >= 2100:
        return "4K+"
    if p >= 1080:
        return "1080p"
    if p >= 720:
        return "720p"
    if p > 0:
        return "SD"
    return "unreadable"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--workers", type=int,
                    default=min(8, os.cpu_count() or 4))
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.execute("PRAGMA journal_mode=WAL")
    cols = {r[1] for r in con.execute("PRAGMA table_info(files)")}
    for col, typ in (("video_w", "INTEGER"), ("video_h", "INTEGER"),
                     ("duration_s", "REAL")):
        if col not in cols:
            con.execute(f"ALTER TABLE files ADD COLUMN {col} {typ}")

    have_ffprobe = shutil.which("ffprobe") is not None
    exts = FFPROBE_EXTS if have_ffprobe else STDLIB_EXTS
    engine = "ffprobe" if have_ffprobe else "stdlib MP4/AVI parser"
    rows = con.execute(
        "SELECT id, path, ext FROM files WHERE video_w IS NULL"
        " AND is_symlink=0 AND ext IN (%s)" % ",".join("?" * len(exts)),
        exts).fetchall()
    skipped = con.execute(
        "SELECT COUNT(*) FROM files WHERE category='video' AND ext NOT IN"
        " (%s)" % ",".join("?" * len(exts)), exts).fetchone()[0]
    print(f"Reading metadata from {len(rows):,} videos ({engine}) ...")
    if skipped and not have_ffprobe:
        print(f"  note: {skipped:,} videos in formats the stdlib parser"
              " can't read (mkv/wmv/...) - install ffmpeg for those")

    def work(r):
        fid, path, ext = r
        if have_ffprobe:
            return (fid, *ffprobe_meta(path))
        if ext == "avi":
            return (fid, *avi_meta(path))
        return (fid, *mp4_meta(path))

    t0 = time.time()
    batch = []
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for fid, w, h, dur in ex.map(work, rows):
            batch.append((w, h, dur, fid))
            done += 1
            if len(batch) >= 200:
                con.executemany("UPDATE files SET video_w=?, video_h=?,"
                                " duration_s=? WHERE id=?", batch)
                con.commit()
                batch.clear()
            if done % 1000 == 0:
                print(f"  {done:,}/{len(rows):,}", flush=True)
    con.executemany("UPDATE files SET video_w=?, video_h=?, duration_s=?"
                    " WHERE id=?", batch)
    con.commit()

    print(f"\nDone in {time.time() - t0:.0f}s.")
    print("=== Videos by resolution ===")
    buckets = {}
    for w, h, dur, size in con.execute(
            "SELECT video_w, video_h, duration_s, size FROM files"
            " WHERE video_w IS NOT NULL"):
        lab = res_label(w or 0, h or 0)
        n, b, d = buckets.get(lab, (0, 0, 0.0))
        buckets[lab] = (n + 1, b + size, d + (dur or 0))
    for lab, (n, b, d) in sorted(buckets.items(), key=lambda kv: -kv[1][1]):
        print(f"  {lab:<11} {n:>7,} videos  {b / 1e9:>8.2f} GB"
              f"  {d / 3600:>7.1f} h total")
    con.close()


if __name__ == "__main__":
    main()
