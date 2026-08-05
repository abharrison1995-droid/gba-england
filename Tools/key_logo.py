#!/usr/bin/env python3
"""Key a flat two-colour logo off its backdrop and trim it, for UI plates.

This exists because the project's other keyer does not fit this job. The importer's
`ArtImportTool.KeyOutBackground` classifies by *fixed* Euclidean distance from the
sampled backdrop — under 60 is backdrop, over 170 is subject, between is unmixed —
and those numbers assume a subject that sits far from the key colour, which is true
of character art on magenta.

It is not true here. The GBH: England plate is gold (184,150,105) on magenta
(160,34,108): the two differ almost entirely in green, and are only 118.5 apart. That
lands inside the unmix band, so the fixed thresholds would emit the whole wordmark at
roughly 53% opacity rather than keying anything.

So the mix is derived from the image instead of assumed. For a two-tone plate the
observed pixel is P = a·F + (1−a)·K exactly, which makes coverage a projection onto
the K→F axis:

    a = clamp( dot(P−K, F−K) / |F−K|² , 0, 1 )

with K measured from the border and F taken as the median of everything far from it.
That is self-scaling: it does not care how close the two colours happen to be, only
that there are two of them. The residual report says whether that held.

Output RGB is set to flat F *everywhere*, including where a is 0. Leaving the keyed
backdrop in the colour channels is what produces a magenta fringe once the GPU
filters the texture bilinearly, because it interpolates RGB across pixels whose alpha
is 0. Flat foreground plus an alpha ramp cannot fringe.

Usage:
    python Tools/key_logo.py <in.png> <out.png>
    python Tools/key_logo.py <in.png> <out.png> --pad 2 --report

On Linux this is python3 — Mint has no bare `python`.

It writes one PNG and nothing else. A clean run says the *cutout* is sound; whether
it reads at the size the title screen draws it still needs the Unity editor.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

# Border pixels varying by more than this (Euclidean, 0-255) are not one flat backdrop,
# and a gradient is better refused than half-keyed. Matches the importer's own limit.
FLATNESS_LIMIT = 90.0

# Everything at least this far from the key seeds the foreground median. Well clear of
# the anti-aliased ramp without assuming how far apart the two colours are.
FOREGROUND_FLOOR = 0.6

# Margin over the measured backdrop noise before alpha is forced to zero. The border ring
# is known-backdrop, so whatever alpha it produces is the noise floor; anything at or under
# that is indistinguishable from backdrop and must not survive. 1.5 covers interior noise
# running slightly hotter than the ring's.
NOISE_MARGIN = 1.5

# However noisy the source, refuse to erase this much of the alpha ramp.
NOISE_CEILING = 0.12


def border_pixels(arr):
    """Every pixel on the outer ring, as an (n, 3) array."""
    return np.concatenate([arr[0, :, :3], arr[-1, :, :3], arr[1:-1, 0, :3], arr[1:-1, -1, :3]])


def key_logo(path, out_path, pad, report):
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img).astype(np.float64)
    h, w = arr.shape[:2]

    key = border_pixels(arr).mean(axis=0)
    spread = np.sqrt(((border_pixels(arr) - key) ** 2).sum(axis=1)).max()
    if spread > FLATNESS_LIMIT:
        print(f"refused: the border varies by {spread:.0f}, so the backdrop is not one flat "
              f"colour and cannot be keyed safely.", file=sys.stderr)
        return 1

    # Foreground: the median of everything clearly off the backdrop. Median rather than
    # mean so a stray dark artefact cannot drag it.
    dist = np.sqrt(((arr - key) ** 2).sum(axis=2))
    far = dist >= dist.max() * FOREGROUND_FLOOR
    if far.sum() < 64:
        print("refused: found no foreground clearly separated from the backdrop.", file=sys.stderr)
        return 1
    fg = np.median(arr[far], axis=0)

    axis = fg - key
    alpha = ((arr - key) @ axis) / (axis @ axis)
    alpha = np.clip(alpha, 0.0, 1.0)

    # A perfectly flat backdrop still is not perfectly uniform, and that jitter projects onto
    # the axis as a small non-zero alpha over the whole plate — a faint wash of foreground
    # colour across the full rectangle, plus a trim box that never shrinks because no row is
    # ever empty. The outer ring is known backdrop, so its alpha *is* the noise floor. Subtract
    # it and rescale, so the ramp above it stays smooth instead of stepping.
    ring = np.concatenate([alpha[0], alpha[-1], alpha[1:-1, 0], alpha[1:-1, -1]])
    noise = min(ring.max() * NOISE_MARGIN, NOISE_CEILING)
    alpha = np.clip((alpha - noise) / (1.0 - noise), 0.0, 1.0)

    # Did the two-colour model actually hold? Anything the model cannot express shows up
    # here — a third colour, a gradient, a drop shadow.
    predicted = key + alpha[..., None] * axis
    residual = np.sqrt(((arr - predicted) ** 2).sum(axis=2))

    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.round(fg).astype(np.uint8)
    out[..., 3] = np.round(alpha * 255).astype(np.uint8)

    ys, xs = np.nonzero(alpha > 0.0)
    if len(ys) == 0:
        print("refused: everything keyed out; nothing left to write.", file=sys.stderr)
        return 1
    top, bottom = ys.min(), ys.max() + 1
    left, right = xs.min(), xs.max() + 1
    out = out[top:bottom, left:right]

    if pad:
        padded = np.zeros((out.shape[0] + pad * 2, out.shape[1] + pad * 2, 4), dtype=np.uint8)
        padded[..., :3] = np.round(fg).astype(np.uint8)
        padded[pad:pad + out.shape[0], pad:pad + out.shape[1]] = out
        out = padded

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    Image.fromarray(out, "RGBA").save(out_path)

    if report:
        opaque = (alpha > 0.99).sum()
        clear = (alpha < 0.01).sum()
        edge = alpha.size - opaque - clear
        print(f"  source        {w}x{h}")
        print(f"  key colour    ({key[0]:.0f}, {key[1]:.0f}, {key[2]:.0f})  border spread {spread:.0f}")
        print(f"  foreground    ({fg[0]:.0f}, {fg[1]:.0f}, {fg[2]:.0f})  separation {np.sqrt(axis @ axis):.1f}")
        print(f"  noise floor   {noise:.4f} alpha, measured off the border ring")
        print(f"  coverage      {opaque * 100 / alpha.size:.1f}% opaque, "
              f"{clear * 100 / alpha.size:.1f}% clear, {edge} edge pixels unmixed")
        print(f"  residual      median {np.median(residual):.1f}, "
              f"99th pct {np.percentile(residual, 99):.1f}, max {residual.max():.1f}")
        print(f"  trimmed       {right - left}x{bottom - top} from {w}x{h} "
              f"(left {left}, top {top}, right {w - right}, bottom {h - bottom} removed)")
    print(f"  wrote         {out_path}  {out.shape[1]}x{out.shape[0]}  "
          f"aspect {out.shape[1] / out.shape[0]:.3f}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", help="the raw plate, backdrop still in place")
    parser.add_argument("output", help="where to write the keyed RGBA PNG")
    parser.add_argument("--pad", type=int, default=2,
                        help="transparent border to leave around the trimmed art (default 2)")
    parser.add_argument("--report", action="store_true", help="print what was measured")
    args = parser.parse_args()

    if not os.path.isfile(args.source):
        print(f"no such file: {args.source}", file=sys.stderr)
        return 1
    return key_logo(args.source, args.output, args.pad, args.report)


if __name__ == "__main__":
    sys.exit(main())
