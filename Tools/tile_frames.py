#!/usr/bin/env python3
"""Assemble single-frame generations into a sheet the art importer will accept.

This is the local half of the workflow in ART_PIPELINE.md §7.3a. Whole-sheet generation
kept failing on four independent things at once — grid layout, figure scale, broken
frames and wandering baselines — so frames are generated one at a time and assembled
here, where each of those is either enforced or measured.

Per frame:
  1. The backdrop is sampled from the four corners. Generators come back near-magenta
     but not exactly #FF00FF, so the key colour is measured, never assumed.
  2. Everything close to that sampled backdrop is normalised to pure magenta, which is
     what the importer's chroma key expects.
  3. The feet are measured, and the frame is translated vertically so every frame's feet
     land on one shared row.

The feet are measured with precheck_sheets.key_mask at the strict threshold on purpose:
that is the same measure the importer applies after key-and-unmix, so the alignment this
tool performs is the alignment the importer will see. Aligning on a more lenient measure
is what let cast_6 through with a blurred shoe edge that read 23 px high in Unity.

Then the frames are tiled into a single row, the sheet and its sidecar JSON are written
to art_incoming/, and the result is re-measured at both thresholds. It exits 1 rather
than leave behind a sheet the importer would refuse.

⚠️ A frame is never rescaled. Resampling blurs dark edge pixels — a shoe sole — into the
backdrop, the keyer then drops them, and the feet read high. A frame that is not already
the declared size is refused, not resized.

So tile at whatever size the frames arrived at and pass --frame-size to declare it: the
player's idle frames are 1024², the attack frames 512². Do not downscale first to make
them match each other. The importer reduces to 48 px per world unit either way, so both
land on the same 65 px cell, and going through one area-averaged reduction instead of two
is strictly better.

Usage:
    python Tools/tile_frames.py player attack
    python Tools/tile_frames.py player idle --frame-size 1024
    python Tools/tile_frames.py danielpauls idle --fps 8
    python Tools/tile_frames.py squirrel walk --world-height 0.45

Frames are read from art_incoming/frames/, named <subject>_<action>_<n>.png or just
<action>_<n>.png, numbered from 1 and contiguous. Run Tools/precheck_sheets.py after
this, then import with Tools → GBA → Art → Import Generated Art.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Same directory, so a plain script run finds it. Imported rather than reimplemented:
# the tiler has to align on precisely what the checker measures, and two copies of that
# formula would drift apart.
from precheck_sheets import DRIFT_LIMIT_FINAL_PX, FINAL_CELL, key_mask

ROOT = Path(__file__).resolve().parent.parent
INCOMING = ROOT / "art_incoming"
FRAMES = INCOMING / "frames"

MAGENTA = (255, 0, 255)

# Thresholds key_mask understands: 60 is the lenient subject measure, 200 approximates
# the importer's alpha-after-unmix feet measure. Alignment uses the strict one.
LENIENT, STRICT = 60, 200

# Actions whose clip should loop. Everything else is a one-shot.
LOOPING_ACTIONS = {"idle", "walk", "cycle"}


def find_frames(subject: str, action: str):
    """Frames numbered from 1, contiguous.

    A subject-qualified name wins, so two subjects can stage frames for the same action
    in one batch without colliding — band 1 had only the player and used the short form.
    """
    for stem in (f"{subject}_{action}", action):
        found = []
        n = 1
        while (FRAMES / f"{stem}_{n}.png").exists():
            found.append(FRAMES / f"{stem}_{n}.png")
            n += 1
        if not found:
            continue

        # A gap would otherwise truncate the run silently: _1 _2 _4 would tile two frames
        # and drop the fourth without a word.
        on_disk = len(list(FRAMES.glob(f"{stem}_*.png")))
        if on_disk > len(found):
            print(f"  !! {stem}_*.png: {on_disk} files on disk but only {len(found)} "
                  f"numbered contiguously from 1 — renumber, nothing is being guessed")
            return []
        return found
    return []


def load_frame(path: Path, size: int) -> np.ndarray:
    """One frame as an RGB array, refusing anything that would need resampling."""
    img = Image.open(path)
    if img.size != (size, size):
        raise ValueError(
            f"{path.name} is {img.size[0]}x{img.size[1]}, declared {size}x{size}. "
            "Frames are never rescaled here — regenerate at the declared size "
            "(see the warning at the top of this file).")

    if img.mode in ("RGBA", "LA", "P"):
        # A frame that did arrive with real alpha is composited onto the key colour, so it
        # keys out the same way as one drawn on a painted backdrop.
        img = img.convert("RGBA")
        backdrop = Image.new("RGBA", img.size, MAGENTA + (255,))
        img = Image.alpha_composite(backdrop, img)

    return np.asarray(img.convert("RGB")).astype(np.int16)


def sample_backdrop(arr: np.ndarray, patch: int = 32) -> np.ndarray:
    """The backdrop colour, as the median of the four corner patches."""
    corners = np.concatenate([
        arr[:patch, :patch].reshape(-1, 3),
        arr[:patch, -patch:].reshape(-1, 3),
        arr[-patch:, :patch].reshape(-1, 3),
        arr[-patch:, -patch:].reshape(-1, 3),
    ])
    return np.median(corners, axis=0)


def normalise_backdrop(arr: np.ndarray, backdrop: np.ndarray, tolerance: float) -> np.ndarray:
    """Repaint everything close to the sampled backdrop as pure magenta.

    Euclidean distance from the *sampled* colour, not from magenta: the point is to catch
    a backdrop that came back off-colour, without eating subject pixels that happen to be
    pinkish.
    """
    out = arr.copy()
    distance = np.sqrt(((arr - backdrop) ** 2).sum(axis=2))
    out[distance <= tolerance] = MAGENTA
    return out


def feet_row(arr: np.ndarray, threshold: int):
    """Bottommost subject row, or None for an empty frame."""
    mask = key_mask(Image.fromarray(arr.astype(np.uint8)), threshold)
    rows = np.nonzero(mask.any(axis=1))[0]
    return int(rows.max()) if len(rows) else None


def shift_vertically(arr: np.ndarray, dy: int) -> np.ndarray:
    """Translate by dy rows, filling the vacated band with pure magenta. Never scales."""
    if dy == 0:
        return arr
    out = np.full_like(arr, MAGENTA)
    height = arr.shape[0]
    if dy > 0:
        out[dy:] = arr[:height - dy]
    else:
        out[:height + dy] = arr[-dy:]
    return out


def measure_sheet(sheet: np.ndarray, columns: int, frame_size: int, threshold: int):
    """Per-cell feet rows across a tiled sheet, at one threshold."""
    mask = key_mask(Image.fromarray(sheet.astype(np.uint8)), threshold)
    rows = []
    for c in range(columns):
        cell = mask[:, c * frame_size:(c + 1) * frame_size]
        occupied = np.nonzero(cell.any(axis=1))[0]
        rows.append(int(occupied.max()) if len(occupied) else None)
    return rows


def drift_final_px(rows, frame_size: int):
    """Baseline spread in final-size pixels, the unit both the importer and the brief use."""
    present = [r for r in rows if r is not None]
    if len(present) < 2:
        return 0.0
    return (max(present) - min(present)) * FINAL_CELL / frame_size


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("subject", help="e.g. player, danielpauls")
    ap.add_argument("action", help="idle, walk, attack, hurt, death, cast")
    ap.add_argument("--frame-size", type=int, default=512,
                    help="square cell size in the source frames (default 512)")
    ap.add_argument("--fps", type=float, default=12.0, help="clip frame rate (default 12)")
    ap.add_argument("--loop", dest="loop", action="store_true", default=None,
                    help="force loop on (default: on for idle/walk/cycle only)")
    ap.add_argument("--no-loop", dest="loop", action="store_false", help="force loop off")
    ap.add_argument("--world-height", type=float, default=1.35,
                    help="subject height in world units (default 1.35; the squirrel is 0.45)")
    ap.add_argument("--category", default="characters", help="art_incoming category (default characters)")
    ap.add_argument("--key-tolerance", type=float, default=60.0,
                    help="how far from the sampled backdrop still counts as backdrop (default 60)")
    ap.add_argument("--baseline", type=int, default=None,
                    help="target feet row; default is the median of the frames as measured, "
                         "which is the smallest total shift")
    ap.add_argument("--out-name", default=None,
                    help="output stem (default sheet_char_<subject>_<action>)")
    args = ap.parse_args()

    size = args.frame_size
    stem = args.out_name or f"sheet_char_{args.subject}_{args.action}"
    loop = args.loop if args.loop is not None else args.action in LOOPING_ACTIONS

    print(f"tile_frames: {args.subject} / {args.action} -> {stem}")

    paths = find_frames(args.subject, args.action)
    if not paths:
        print(f"  !! no frames found. Expected {FRAMES}/{args.subject}_{args.action}_1.png "
              f"or {FRAMES}/{args.action}_1.png")
        return 1
    print(f"  {len(paths)} frames: {', '.join(p.name for p in paths)}")

    # Normalise every frame first, then measure: the feet measure only means what the
    # importer means by it once the backdrop is actually pure magenta.
    frames, measured = [], []
    for path in paths:
        try:
            arr = load_frame(path, size)
        except ValueError as e:
            print(f"  !! {e}")
            return 1
        backdrop = sample_backdrop(arr)
        arr = normalise_backdrop(arr, backdrop, args.key_tolerance)
        row = feet_row(arr, STRICT)
        if row is None:
            print(f"  !! {path.name}: no subject found — an empty or fully-keyed frame")
            return 1
        frames.append(arr)
        measured.append(row)
        print(f"    {path.name}: backdrop {tuple(int(v) for v in backdrop)}, feet row {row}")

    target = args.baseline if args.baseline is not None else int(np.median(measured))
    print(f"  aligning feet to row {target}"
          f"{' (given)' if args.baseline is not None else ' (median of measured)'}")

    aligned = []
    for path, arr, row in zip(paths, frames, measured):
        dy = target - row
        if dy:
            # A shift only ever loses rows that were backdrop before the subject started,
            # so clipping means the subject genuinely does not fit at this baseline.
            mask = key_mask(Image.fromarray(arr.astype(np.uint8)), LENIENT)
            occupied = np.nonzero(mask.any(axis=1))[0]
            if dy > 0 and occupied.max() + dy > size - 1:
                print(f"  !! {path.name}: shifting down {dy} would push the subject off the "
                      f"bottom — pass --baseline lower than {target}")
                return 1
            if dy < 0 and occupied.min() + dy < 0:
                print(f"  !! {path.name}: shifting up {-dy} would cut the top off — "
                      f"pass --baseline higher than {target}")
                return 1
        aligned.append(shift_vertically(arr, dy))
        print(f"    {path.name}: dy {dy:+d}")

    columns = len(aligned)
    sheet = np.concatenate(aligned, axis=1)

    INCOMING.mkdir(parents=True, exist_ok=True)
    png_path = INCOMING / f"{stem}.png"
    json_path = INCOMING / f"{stem}.json"
    Image.fromarray(sheet.astype(np.uint8)).save(png_path)

    manifest = {
        "name": f"{args.subject}_{args.action}",
        "type": "sheet",
        "category": args.category,
        "action": args.action,
        "worldHeight": args.world_height,
        "frameWidth": size,
        "frameHeight": size,
        "columns": columns,
        "rows": 1,
        "frameCount": columns,
        "fps": args.fps,
        "loop": loop,
        # Recorded because the manifest is the only thing that survives into review, and
        # "which baseline was this aligned to" is the first question asked of a bad sheet.
        "description": (f"{columns}-frame {args.action}, one row, one drawing per "
                        f"{size}x{size} cell, feet aligned to row {target}, flat magenta "
                        f"#FF00FF background. Tiled by Tools/tile_frames.py from "
                        f"{columns} single-frame generations."),
    }
    json_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {png_path.relative_to(ROOT)} ({columns * size}x{size}) and "
          f"{json_path.relative_to(ROOT)}")

    # Re-measure what was actually written. Strict drift should be zero by construction,
    # since that is the measure the alignment used; it is checked anyway, because a
    # discrepancy here means an assumption above is wrong.
    ok = True
    for threshold in (LENIENT, STRICT):
        rows = measure_sheet(sheet, columns, size, threshold)
        drift = drift_final_px(rows, size)
        verdict = "ok" if drift <= DRIFT_LIMIT_FINAL_PX else "OVER LIMIT"
        print(f"  feet rows at threshold {threshold}: {rows} -> drift {drift:.1f}px final "
              f"(limit {DRIFT_LIMIT_FINAL_PX}) {verdict}")
        # Death is exempt from the drift check in the importer, but the exemption is for the
        # pose changing shape, not for the figure wandering its cell — so it is reported
        # here either way and only enforced where the importer enforces it.
        if drift > DRIFT_LIMIT_FINAL_PX and args.action != "death":
            ok = False

    if not ok:
        print("  RESULT: the sheet is written but the importer would refuse it on baseline "
              "drift. Fix the frames rather than the sheet.")
        return 1

    print(f"  RESULT: written. Next: python Tools/precheck_sheets.py, then import in Unity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
