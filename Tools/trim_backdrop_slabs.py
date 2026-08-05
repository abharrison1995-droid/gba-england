#!/usr/bin/env python3
"""Reshape the brown slabs painted into the character-creator backdrop.

The two slabs behind the details panel and the character are part of
`Creator_Background.png`, not UI. There is no anchor to move, so reshaping them means
repainting the image.

Two operations, either or both:

  --merge         join the two slabs into one box spanning between them
  --keep-bottom   end the slab(s) at a given row and put scenery back below

⚠️ **The clock towers stand on the slabs.** Their bases were never painted — they were
always hidden behind brown — so raising the *top* of a slab leaves a tower floating over
a hard edge with nothing underneath. `--keep-top` exists but defaults to 0.0 for that
reason. Shortening from the bottom is safe; shortening from the top needs new art.

Scenery fill
------------
Where a slab is removed, the fill is a mirrored cross-fade rather than an interpolation.
For each row, the strip of scenery immediately left of the slab is mirrored rightwards,
the strip immediately right is mirrored leftwards, and the two are cross-faded across the
gap. Mirroring is what keeps the seam invisible — the fill meets the untouched pixel at
each slab edge with the same colour it had. Plain left-to-right interpolation was tried
first and smears the dry-stone wall into bands, because a wall is texture, not gradient.

This works because the backdrop is strongly horizontally banded: sky, hills, hedgerow,
field, wall. It would not work on a subject with vertical structure crossing the slab,
and nothing here detects that — look at the output.

Slab fill
---------
Merging does not paint flat colour. It tiles a representative column taken from an
existing slab, so the faint horizontal seam lines and the vertical shading carry across
the new box and it reads as the same material rather than a rectangle dropped on top.

Usage:
    python Tools/trim_backdrop_slabs.py --merge --keep-bottom 0.80 --trim 7 --report
    python Tools/trim_backdrop_slabs.py --keep-bottom 0.80 --out preview.png

Bounds are fractions of image height from the top. The creator's Preview panel sits at
Unity y 0.20-0.65, which is top-origin 0.35-0.80.

On Linux this is python3 — Mint has no bare `python`.

It writes one PNG. Whether the result looks right is a human judgement; nothing here can
tell a good fill from a bad one.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = os.path.join(REPO, "Assets", "Textures", "UI", "Title", "Creator_Background.png")

# The slab is a flat dark brown. Sampled, never assumed — see key_logo.py for why that
# matters. This point is inside the right-hand slab at half height.
SAMPLE_AT = (0.50, 0.79)

# How close to the sampled colour counts as slab. Generous enough to take the slab's
# faint horizontal seam lines with it, tight enough to leave the scenery alone.
SLAB_TOLERANCE = 45.0

# A column *seeds* a slab if it is slab-coloured for one contiguous run at least this
# tall. Total matching pixels is not enough on its own: the shadowed dry-stone wall along
# the bottom edge is the same dark brown and covers ~22% of the columns it occupies, which
# merged the left slab with the entire bottom-left corner and repainted it.
MIN_RUN = 0.40

# ...but seeding alone is too strict, because both slabs carry faint horizontal seam lines
# that split a column's run in two — on the left slab most columns peak at 158 rows, well
# under the threshold. So qualifying columns are grouped with this much tolerance for
# non-qualifying columns between them. Seams cost a handful of columns at a time; the gap
# between the two slabs is ~670, so they can never merge by accident.
COLUMN_GAP = 24

# Having found the core, grow outward while a column is still mostly slab within the
# slab's own rows. The colour test alone stops short of the shadowed, anti-aliased edges,
# and a fixed bleed either leaves a brown fringe or eats scenery.
EDGE_COVERAGE = 0.5

# Light brown for the trim, matching CharacterCreatorSetup.IntroTrim so the painted box
# and the UI panels in front of it belong to the same set.
TRIM_COLOUR = (158, 128, 87)


def longest_run(column):
    """Length of the longest unbroken True run in a 1-D boolean array."""
    best = run = 0
    for value in column:
        run = run + 1 if value else 0
        if run > best:
            best = run
    return best


def find_slabs(arr, tolerance, report):
    h, w = arr.shape[:2]
    sample = arr[int(h * SAMPLE_AT[0]), int(w * SAMPLE_AT[1])]
    mask = np.sqrt(((arr - sample) ** 2).sum(axis=2)) < tolerance

    seeds = [x for x in range(w) if longest_run(mask[:, x]) >= h * MIN_RUN]
    groups = []
    for x in seeds:
        if groups and x - groups[-1][1] <= COLUMN_GAP:
            groups[-1][1] = x
        else:
            groups.append([x, x])

    slabs = []
    for x0, x1 in groups:
        if x1 - x0 < w * 0.02:
            continue
        # A slab row is slab-coloured nearly all the way across. Demanding 90% rather than
        # a simple majority is what keeps the clock tower out: it is dark enough to match
        # the colour test but is narrower than the slab it stands on.
        band = mask[:, x0:x1 + 1]
        solid = np.nonzero(band.sum(axis=1) > (x1 - x0) * 0.9)[0]
        if len(solid) == 0:
            continue
        y0, y1 = int(solid.min()), int(solid.max())

        rows = slice(y0, y1 + 1)
        height = y1 - y0 + 1
        while x0 > 0 and mask[rows, x0 - 1].sum() >= height * EDGE_COVERAGE:
            x0 -= 1
        while x1 < w - 1 and mask[rows, x1 + 1].sum() >= height * EDGE_COVERAGE:
            x1 += 1
        slabs.append((x0, x1, y0, y1))

    if report:
        print("  slab colour   (%d, %d, %d)" % tuple(sample.astype(int)))
        for x0, x1, y0, y1 in slabs:
            print("  slab found    x %4d..%-4d  y %4d..%-4d   (norm x %.4f..%.4f, y %.4f..%.4f)"
                  % (x0, x1, y0, y1, x0 / w, x1 / w, y0 / h, y1 / h))
    return slabs


def fill_gap(arr, x0, x1, rows):
    """Mirrored cross-fade across columns x0..x1 for the given rows."""
    h, w = arr.shape[:2]
    span = x1 - x0 + 1

    left = arr[rows, max(0, x0 - span):x0]
    right = arr[rows, x1 + 1:min(w, x1 + 1 + span)]
    if left.shape[1] == 0 and right.shape[1] == 0:
        return

    def stretched(strip, flip):
        if strip.shape[1] == 0:
            return None
        out = strip[:, ::-1] if flip else strip
        if out.shape[1] < span:
            out = np.concatenate([out, np.repeat(out[:, -1:], span - out.shape[1], axis=1)], axis=1)
        return out[:, :span]

    from_left = stretched(left, True)       # mirrored, so x0 continues the pixel at x0-1
    from_right = stretched(right, False)
    if from_right is not None:
        from_right = from_right[:, ::-1]    # and x1 continues the pixel at x1+1

    if from_left is None:
        blended = from_right
    elif from_right is None:
        blended = from_left
    else:
        t = np.linspace(0.0, 1.0, span)[None, :, None]
        blended = from_left * (1.0 - t) + from_right * t

    arr[rows, x0:x1 + 1] = blended


def slab_column(arr, slab, top, bottom):
    """A representative column of slab material for the given rows.

    Median across the slab's own columns: it keeps each row's real value, so the seam
    lines and shading survive, while averaging out per-pixel noise. A single sampled
    column would carry its own blemishes across the whole new box.
    """
    x0, x1, _, _ = slab
    return np.median(arr[top:bottom + 1, x0:x1 + 1], axis=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--out", default=None, help="defaults to overwriting --src")
    ap.add_argument("--merge", action="store_true",
                    help="join the slabs into one box spanning between them")
    ap.add_argument("--keep-top", type=float, default=0.0,
                    help="fraction of height where the slab starts; raising this orphans "
                         "the clock towers, see the module docstring")
    ap.add_argument("--keep-bottom", type=float, default=0.80,
                    help="fraction of height where the slab ends")
    ap.add_argument("--trim", type=int, default=0,
                    help="light-brown border in pixels drawn around the merged box (0 = none)")
    ap.add_argument("--tolerance", type=float, default=SLAB_TOLERANCE)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.src):
        print("no such file: " + args.src, file=sys.stderr)
        return 1
    if not 0.0 <= args.keep_top < args.keep_bottom <= 1.0:
        print("--keep-top must be less than --keep-bottom, both within 0..1", file=sys.stderr)
        return 1
    if args.trim and not args.merge:
        print("--trim only applies to the merged box; pass --merge too.", file=sys.stderr)
        return 1

    img = Image.open(args.src).convert("RGB")
    arr = np.asarray(img).astype(np.float64)
    h, w = arr.shape[:2]
    if args.report:
        print("  source        %dx%d" % (w, h))

    slabs = find_slabs(arr, args.tolerance, args.report)
    if not slabs:
        print("refused: found no slab to reshape.", file=sys.stderr)
        return 1
    if args.merge and len(slabs) < 2:
        print("refused: --merge needs two slabs, found %d." % len(slabs), file=sys.stderr)
        return 1

    keep_bottom = int(round(h * args.keep_bottom))

    # Scenery goes back first, using the *original* slab columns. Doing this after the
    # merge would mean sampling neighbours that are themselves freshly painted brown.
    for x0, x1, y0, y1 in slabs:
        above = np.arange(y0, min(y1 + 1, int(round(h * args.keep_top))))
        below = np.arange(max(y0, keep_bottom + 1), y1 + 1)
        for rows in (above, below):
            if len(rows):
                fill_gap(arr, x0, x1, rows)
        if args.report:
            print("  scenery back  x %4d..%-4d  %d rows above, %d below"
                  % (x0, x1, len(above), len(below)))

    if args.merge:
        box_x0 = min(s[0] for s in slabs)
        box_x1 = max(s[1] for s in slabs)
        box_y0 = max(int(round(h * args.keep_top)), min(s[2] for s in slabs))
        box_y1 = keep_bottom

        column = slab_column(arr, slabs[-1], box_y0, box_y1)
        arr[box_y0:box_y1 + 1, box_x0:box_x1 + 1] = column[:, None, :]

        if args.trim:
            t = args.trim
            trim = np.array(TRIM_COLOUR, dtype=np.float64)
            arr[box_y0:box_y0 + t, box_x0:box_x1 + 1] = trim
            arr[box_y1 - t + 1:box_y1 + 1, box_x0:box_x1 + 1] = trim
            arr[box_y0:box_y1 + 1, box_x0:box_x0 + t] = trim
            arr[box_y0:box_y1 + 1, box_x1 - t + 1:box_x1 + 1] = trim

        if args.report:
            print("  merged box    x %4d..%-4d  y %4d..%-4d  (norm x %.4f..%.4f, y %.4f..%.4f)"
                  % (box_x0, box_x1, box_y0, box_y1,
                     box_x0 / w, box_x1 / w, box_y0 / h, box_y1 / h))
            if args.trim:
                print("  trim          %dpx  rgb%s" % (args.trim, TRIM_COLOUR))

    out_path = args.out or args.src
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(out_path)
    print("  wrote         %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
