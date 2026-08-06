#!/usr/bin/env python3
"""Mirror a sprite sheet horizontally, one animation frame at a time.

The art contract (ART_PIPELINE.md §1) is that every character is drawn facing
camera-right, because WorldActorVisual flips the sprite itself for camera-left.
A sheet delivered facing left reads mirrored in game and, worse, disagrees with
the subject's other sheets.

The fix is a horizontal mirror, but **never of the whole image** -- a sheet is a
strip of frames left to right, so mirroring the strip reverses the frame order
and plays the walk cycle backwards. This flips each cell within its own bounds,
which leaves the order, the grid and the baseline exactly where they were.

Both copies of an asset are flipped together:

  * the source in ``art_incoming/`` (or ``art_incoming/processed/``), sliced on
    the grid its sidecar JSON declares, so a future re-import stays correct;
  * the imported PNG in ``Assets/Art/Generated/``, sliced on the rects its
    ``.meta`` actually declares.

Flipping the imported PNG in place is deliberate. The ``.meta`` is untouched, so
the texture GUID, every sprite sub-asset fileID, and therefore every
AnimationClip and AnimatorController that references them all survive. **No
re-import and no animation rebuild is needed** -- Unity reloads the pixels and
nothing else changes.

Because a flip is its own inverse, running twice silently undoes the work. The
ledger at Tools/flipped_sheets.json records what has been flipped and the tool
refuses a repeat without --force.

Usage:
    python Tools/flip_sheets.py --list
    python Tools/flip_sheets.py --dry-run sheet_char_villager_walk
    python Tools/flip_sheets.py sheet_char_villager_walk sheet_char_murtaugh_walk
"""

import argparse
import json
import os
import re
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIRS = ("art_incoming", os.path.join("art_incoming", "processed"))
IMPORTED_DIRS = (
    os.path.join("Assets", "Art", "Generated", "characters"),
    os.path.join("Assets", "Art", "Generated", "vehicles"),
    os.path.join("Assets", "Art", "Generated", "props"),
    os.path.join("Assets", "Art", "Generated", "fx"),
    os.path.join("Assets", "Art", "Generated", "ui"),
)
LEDGER = os.path.join(ROOT, "Tools", "flipped_sheets.json")

# name / rect: x / y / width / height, in the order Unity writes them.
RECT_RE = re.compile(
    r"name:\s*(?P<name>\S+)\s*\n\s*rect:\s*\n\s*serializedVersion:\s*\d+\s*\n"
    r"\s*x:\s*(?P<x>\d+)\s*\n\s*y:\s*(?P<y>\d+)\s*\n"
    r"\s*width:\s*(?P<w>\d+)\s*\n\s*height:\s*(?P<h>\d+)"
)


def flip_cells(png_path, rects):
    """Mirror each rect of an image in place. rects are (x, y, w, h), top-left origin."""
    im = Image.open(png_path)
    fmt, mode = im.format, im.mode
    im = im.copy()
    for (x, y, w, h) in rects:
        box = (x, y, x + w, y + h)
        im.paste(im.crop(box).transpose(Image.FLIP_LEFT_RIGHT), box)
    im.save(png_path, format=fmt or "PNG")
    return mode, im.size


def source_rects(png_path):
    """Grid from the sidecar JSON. A single sprite is one cell covering the image."""
    meta_path = png_path[:-4] + ".json"
    im = Image.open(png_path)
    if not os.path.exists(meta_path):
        return [(0, 0, im.width, im.height)]
    d = json.load(open(meta_path, encoding="utf8"))
    if d.get("type") != "sheet":
        return [(0, 0, im.width, im.height)]
    cols = int(d["columns"])
    rows = int(d.get("rows", 1))
    count = int(d.get("frameCount", cols * rows))
    fw, fh = im.width // cols, im.height // rows
    if fw * cols != im.width or fh * rows != im.height:
        raise ValueError(
            f"{os.path.basename(png_path)}: {im.width}x{im.height} is not a whole "
            f"{cols}x{rows} grid -- refusing to guess"
        )
    return [((i % cols) * fw, (i // cols) * fh, fw, fh) for i in range(count)]


def imported_rects(png_path):
    """Rects Unity actually slices, read from the .meta. Unity's y origin is bottom-left."""
    meta_path = png_path + ".meta"
    im = Image.open(png_path)
    if not os.path.exists(meta_path):
        return [(0, 0, im.width, im.height)]
    text = open(meta_path, encoding="utf8").read()
    rects = []
    for m in RECT_RE.finditer(text):
        x, y = int(m.group("x")), int(m.group("y"))
        w, h = int(m.group("w")), int(m.group("h"))
        rects.append((x, im.height - y - h, w, h))
    return rects or [(0, 0, im.width, im.height)]


def locate(name):
    """Every on-disk copy of an asset, as (path, rects, label)."""
    found = []
    for d in SOURCE_DIRS:
        p = os.path.join(ROOT, d, name + ".png")
        if os.path.exists(p):
            found.append((p, source_rects(p), "source"))
    for d in IMPORTED_DIRS:
        p = os.path.join(ROOT, d, name + ".png")
        if os.path.exists(p):
            found.append((p, imported_rects(p), "imported"))
    return found


def load_ledger():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding="utf8"))
    return {"flipped": []}


def save_ledger(led):
    led["flipped"] = sorted(set(led["flipped"]))
    with open(LEDGER, "w", encoding="utf8") as f:
        json.dump(led, f, indent=2)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("names", nargs="*", help="asset names without .png, e.g. sheet_char_villager_walk")
    ap.add_argument("--dry-run", action="store_true", help="report what would be flipped, change nothing")
    ap.add_argument("--force", action="store_true", help="flip again even if the ledger says it was already done")
    ap.add_argument("--list", action="store_true", help="print the ledger and exit")
    args = ap.parse_args()

    led = load_ledger()
    if args.list:
        for n in led["flipped"]:
            print(n)
        return 0
    if not args.names:
        ap.error("give at least one asset name, or --list")

    failed = False
    for name in args.names:
        name = name[:-4] if name.endswith(".png") else name
        if name in led["flipped"] and not args.force:
            print(f"SKIP  {name} -- already flipped (--force to flip back)")
            continue
        copies = locate(name)
        if not copies:
            print(f"MISS  {name} -- no PNG found in art_incoming/ or Assets/Art/Generated/")
            failed = True
            continue
        for path, rects, label in copies:
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            if args.dry_run:
                print(f"would flip {len(rects):>2} cell(s)  {rel}  ({label})")
                continue
            mode, size = flip_cells(path, rects)
            print(f"flipped {len(rects):>2} cell(s)  {rel}  ({label}, {mode} {size[0]}x{size[1]})")
        if not args.dry_run:
            if args.force and name in led["flipped"]:
                led["flipped"].remove(name)
            else:
                led["flipped"].append(name)

    if not args.dry_run:
        save_ledger(led)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
