#!/usr/bin/env python3
"""Triage images into camera photos vs screenshots vs saved-web junk.

Separates real photographs from the memes, Facebook saves, and screenshots
tangled in with them. Writes files.photo_kind:

  camera      real photograph (camera EXIF, camera filename, photo-like
              content)
  screenshot  device screenshots (name pattern or exact screen dimensions)
  saved_web   downloaded/saved images: FB_IMG_*, Messenger received_*,
              Facebook CDN names, download.jpg, plus content that scores
              as a flat graphic/meme rather than a photograph
  unknown     not confident either way — the review pile; never auto-filed
              as junk

Signals (cheap first, decode only borderline cases):
  - EXIF camera make/model, original date, GPS (stdlib parser, reads 128KB)
  - filename patterns for cameras and for social/web sources
  - pixel dimensions from JPEG/PNG/GIF headers (stdlib)
  - with Pillow installed: color flatness — memes/graphics have few
    quantized colors and big white/black areas; photos have smooth
    gradients (optional; triage still works without it)

Facebook/Messenger names beat content: a real photo somebody posted to
Facebook is still 'saved_web' — the user is sorting by provenance.
"""
import argparse
import os
import re
import sqlite3
import sys
import time

try:
    from PIL import Image
    HAVE_PIL = True
    Image.MAX_IMAGE_PIXELS = None
except ImportError:
    HAVE_PIL = False

IMAGE_EXTS = ("jpg", "jpeg", "png", "gif", "webp", "heic", "heif", "bmp",
              "tif", "tiff")

CAMERA_NAME = re.compile(
    r"^(img[_-]?\d{3,}|dsc[_-]?\d{3,}|dscn\d+|dscf\d+|pxl_\d{8}|dji_\d+"
    r"|gopr\d+|mvimg_\d+|burst\d+|p\d{6,}|sam_\d+|100_\d{4}"
    r"|\d{8}[_-]\d{6}|scan\d+)", re.I)
JUNK_NAME = re.compile(
    r"^(fb_img_\d+|received_\d+|download(\s?\(\d+\))?\.|unnamed"
    r"|images?(\s?\(\d+\))?\.|giphy|meme|tumblr_|photo\s?\(\d+\)"
    r"|snapchat-|\d{5,}_\d{5,}\d*_?\d*_[no]\.)", re.I)
SCREENSHOT_NAME = re.compile(r"screen\s?shot|screenshot|screen_\d|scrn", re.I)
SCREEN_DIMS = {
    (750, 1334), (828, 1792), (1080, 1920), (1080, 2280), (1080, 2340),
    (1080, 2400), (1125, 2436), (1170, 2532), (1179, 2556), (1284, 2778),
    (1290, 2796), (1440, 2560), (1440, 2960), (1440, 3040), (1440, 3200),
    (720, 1280), (720, 1520), (720, 1600), (1536, 2048), (1600, 2560),
    (2560, 1440), (1920, 1080), (3840, 2160), (2880, 1800), (3440, 1440),
}


# ---- stdlib metadata readers -------------------------------------------

def parse_exif(t):
    """Minimal TIFF/EXIF walk: returns dict with make/model/date/gps."""
    out = {"make": False, "model": False, "date": False, "gps": False}
    if len(t) < 8 or t[:2] not in (b"II", b"MM"):
        return out
    bo = "little" if t[:2] == b"II" else "big"

    def u16(o):
        return int.from_bytes(t[o:o + 2], bo)

    def u32(o):
        return int.from_bytes(t[o:o + 4], bo)

    def walk(off, depth=0):
        if depth > 3 or off + 2 > len(t):
            return
        n = u16(off)
        for k in range(min(n, 200)):
            e = off + 2 + 12 * k
            if e + 12 > len(t):
                return
            tag = u16(e)
            if tag == 0x010F:
                out["make"] = True
            elif tag == 0x0110:
                out["model"] = True
            elif tag in (0x9003, 0x0132):
                out["date"] = True
            elif tag == 0x8825:
                out["gps"] = True
            elif tag == 0x8769:
                walk(u32(e + 8), depth + 1)

    walk(u32(4))
    return out


def read_meta(path, ext):
    """(exif dict, width, height) from the first 128KB, stdlib only."""
    exif = parse_exif(b"")
    w = h = 0
    try:
        with open(path, "rb") as f:
            head = f.read(131072)
    except OSError:
        return exif, w, h
    if head[:8] == b"\x89PNG\r\n\x1a\n" and len(head) >= 24:
        w = int.from_bytes(head[16:20], "big")
        h = int.from_bytes(head[20:24], "big")
    elif head[:6] in (b"GIF87a", b"GIF89a"):
        w = int.from_bytes(head[6:8], "little")
        h = int.from_bytes(head[8:10], "little")
    elif head[:2] in (b"II", b"MM"):
        exif = parse_exif(head)
    elif head[:2] == b"\xff\xd8":
        i = 2
        while i + 4 <= len(head):
            if head[i] != 0xFF:
                break
            marker = head[i + 1]
            if marker == 0xD8 or 0xD0 <= marker <= 0xD7 or marker == 0x01:
                i += 2
                continue
            seglen = int.from_bytes(head[i + 2:i + 4], "big")
            if marker == 0xE1 and head[i + 4:i + 10] == b"Exif\x00\x00":
                exif = parse_exif(head[i + 10:i + 2 + seglen])
            elif marker in (0xC0, 0xC1, 0xC2, 0xC3):
                h = int.from_bytes(head[i + 5:i + 7], "big")
                w = int.from_bytes(head[i + 7:i + 9], "big")
            if marker == 0xDA:
                break
            i += 2 + seglen
    return exif, w, h


def content_score(path):
    """+2 photo-like, -4 graphic/meme-like, 0 unreadable. Needs Pillow."""
    try:
        with Image.open(path) as im:
            g = im.convert("RGB").resize((64, 64), Image.BILINEAR)
            data = g.tobytes()
    except Exception:
        return 0
    colors = set()
    extreme = 0
    n = 64 * 64
    for i in range(0, n * 3, 3):
        r, gr, b = data[i], data[i + 1], data[i + 2]
        colors.add((r >> 5, gr >> 5, b >> 5))
        lum = (r + gr + b) // 3
        if lum > 240 or lum < 15:
            extreme += 1
    if len(colors) < 45 or extreme / n > 0.40:
        return -4
    if len(colors) > 110:
        return 2
    return 0


def triage(path, name, ext, size):
    lname = name.lower()
    exif, w, h = read_meta(path, ext)
    if SCREENSHOT_NAME.search(lname) or \
            ((w, h) in SCREEN_DIMS or (h, w) in SCREEN_DIMS
             ) and ext in ("png", "webp"):
        return "screenshot"
    has_camera_exif = exif["make"] or exif["model"]
    if JUNK_NAME.match(lname) and not has_camera_exif:
        return "saved_web"
    score = 0
    if CAMERA_NAME.match(lname):
        score += 4
    if has_camera_exif:
        score += 5
    if exif["date"]:
        score += 2
    if exif["gps"]:
        score += 2
    if ext in ("heic", "heif"):
        score += 4
    elif ext in ("png", "gif", "webp"):
        score -= 2
    if size > 1_500_000:
        score += 2
    elif size < 300_000:
        score -= 1
    mp = w * h
    if mp >= 5_000_000:
        score += 2
    elif 0 < mp < 500_000:
        score -= 2
    if HAVE_PIL and -4 < score < 4 and ext not in ("heic", "heif"):
        score += content_score(path)
    if score >= 4:
        return "camera"
    if score <= -4:
        return "saved_web"
    return "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--reset", action="store_true",
                    help="re-triage everything (e.g. after rule changes)")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.execute("PRAGMA journal_mode=WAL")
    cols = {r[1] for r in con.execute("PRAGMA table_info(files)")}
    if "photo_kind" not in cols:
        con.execute("ALTER TABLE files ADD COLUMN photo_kind TEXT")
    if args.reset:
        con.execute("UPDATE files SET photo_kind=NULL")

    rows = con.execute(
        "SELECT id, path, name, ext, size FROM files"
        " WHERE photo_kind IS NULL AND is_symlink=0 AND ext IN (%s)"
        " AND category IN ('image', 'photo_library')"
        % ",".join("?" * len(IMAGE_EXTS)), IMAGE_EXTS).fetchall()
    if not HAVE_PIL:
        print("Note: Pillow not installed - triaging on metadata and names"
              " only (still effective). pip install Pillow adds content"
              " analysis for unnamed memes.")
    print(f"Triaging {len(rows):,} images ...")
    t0 = time.time()
    batch = []
    for i, (fid, path, name, ext, size) in enumerate(rows, 1):
        batch.append((triage(path, name, ext, size), fid))
        if len(batch) >= 500:
            con.executemany(
                "UPDATE files SET photo_kind=? WHERE id=?", batch)
            con.commit()
            batch.clear()
        if i % 5000 == 0:
            print(f"  {i:,}/{len(rows):,}"
                  f" ({i / max(time.time() - t0, 0.1):.0f} img/s)",
                  flush=True)
    con.executemany("UPDATE files SET photo_kind=? WHERE id=?", batch)
    con.commit()

    print("\n=== Photo triage ===")
    for kind, n, b in con.execute(
            "SELECT photo_kind, COUNT(*), SUM(size) FROM files"
            " WHERE photo_kind IS NOT NULL GROUP BY photo_kind"
            " ORDER BY COUNT(*) DESC"):
        print(f"  {kind:<11} {n:>9,} images  {(b or 0) / 1e9:>8.2f} GB")
        for (p,) in con.execute(
                "SELECT path FROM files WHERE photo_kind=?"
                " ORDER BY size DESC LIMIT 3", (kind,)):
            print(f"      e.g. {p}")
    print("\nSpot-check the examples above with the user, then route kinds"
          "\nto folders via file-organize's photo_kind_destinations config.")
    con.close()


if __name__ == "__main__":
    main()
