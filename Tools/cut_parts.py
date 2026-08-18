"""Cut a staged character image into per-part PNGs for the sprite rig.

The staging half of the photo path: one synthetic source image in, thirteen
alpha-cut body parts out, plus the JSON a subject script feeds to
sprite_kit.render_subject(part_images=...).

    python Tools/cut_parts.py art_incoming/frames/mandrew_idle_1.png mandrew

Writes Tools/blender/out/parts/<subject>/<part>.png and parts.json.

Keys out the ART_PIPELINE.md magenta backdrop (#FF00FF) if the source has no
usable alpha, trims to the subject, then slices by BANDS below — anatomical
proportions as fractions of the trimmed figure box, y measured from the top.

The bands are the tunable part. A source whose subject stands differently
needs its own set; pass --bands to point at a JSON file of overrides rather
than editing this table, so the default stays the reference.

⚠ Screen-left is the character's RIGHT. The rig's `.L` / `.R` suffixes are the
character's own, so the screen-left limb is cut into `.R` — see BANDS.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = ROOT / "Tools" / "blender" / "out" / "parts"

MAGENTA = (255, 0, 255)
KEY_TOLERANCE = 60

# part -> (x0, x1, y0, y1), fractions of the trimmed subject box, y from TOP.
# Tuned against a front-on standing figure with arms at the sides.
BANDS = {
    # Bands must not overlap vertically where one part draws over another:
    # head 0-0.155 against torso 0.135 put the jacket collar across the mouth.
    "head":    (0.32, 0.72, 0.000, 0.145),
    "torso":   (0.16, 0.86, 0.145, 0.470),
    "pelvis":  (0.20, 0.80, 0.470, 0.560),
    # Character's RIGHT limb = screen LEFT.
    "arm_u.R": (0.04, 0.30, 0.150, 0.380),
    "arm_l.R": (0.04, 0.32, 0.360, 0.560),
    "arm_u.L": (0.70, 0.96, 0.150, 0.380),
    "arm_l.L": (0.68, 0.96, 0.360, 0.560),
    "thigh.R": (0.20, 0.52, 0.545, 0.750),
    "thigh.L": (0.48, 0.80, 0.545, 0.750),
    "shin.R":  (0.22, 0.50, 0.740, 0.945),
    "shin.L":  (0.50, 0.78, 0.740, 0.945),
    "foot.R":  (0.16, 0.52, 0.930, 1.000),
    "foot.L":  (0.48, 0.84, 0.930, 1.000),
}


def key_magenta(img, tolerance=KEY_TOLERANCE):
    """Make the flat magenta backdrop transparent. Returns (image, keyed?)."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    # Only key if the corners actually are magenta — a source delivered with
    # real alpha must not be touched.
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    def is_key(c):
        return (abs(c[0] - MAGENTA[0]) < tolerance
                and abs(c[1] - MAGENTA[1]) < tolerance
                and abs(c[2] - MAGENTA[2]) < tolerance)
    if not all(is_key(c) for c in corners):
        return img, False
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if is_key((r, g, b)):
                px[x, y] = (0, 0, 0, 0)
            elif r > g and b > g:
                # Despill: anti-aliased edge pixels are part backdrop, and
                # left alone they ring the whole subject in pink once the
                # sprite is reduced. Pull magenta's two channels down to the
                # green they would have without the bleed.
                m = min(r, b)
                excess = m - g
                if excess > 12:
                    px[x, y] = (r - excess, g, b - excess,
                                max(0, a - excess // 2))
    return img, True


def cut(source, subject, bands=None, out_root=OUT_ROOT):
    bands = bands or BANDS
    img = Image.open(source)
    img, keyed = key_magenta(img)
    box = img.getbbox()
    if box is None:
        raise SystemExit(f"ERROR: {source} is fully transparent after keying.")
    img = img.crop(box)
    W, H = img.size
    print(f"[cut_parts] {Path(source).name}: "
          f"{'keyed magenta, ' if keyed else 'source alpha, '}"
          f"trimmed to {W}x{H}")

    out_dir = Path(out_root) / subject
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for part, (x0, x1, y0, y1) in bands.items():
        bx0, by0 = int(x0 * W), int(y0 * H)
        crop = img.crop((bx0, by0, int(x1 * W), int(y1 * H)))
        # Trim each part to its own content so the card's aspect describes the
        # limb, not the slack in the band.
        inner = crop.getbbox()
        if inner is None:
            print(f"  WARN {part}: empty after cut — band misses the subject")
            continue
        crop = crop.crop(inner)
        path = out_dir / f"{part}.png"
        crop.save(path)

        # Where this part actually sits in the figure, so the rig can rebuild
        # the pose the source was photographed in instead of imposing its own
        # proportions. Both axes are divided by figure HEIGHT so aspect
        # survives; u is signed from the figure's horizontal centre, v runs
        # 0 at the feet to 1 at the crown.
        px0, py0, px1, py1 = (bx0 + inner[0], by0 + inner[1],
                              bx0 + inner[2], by0 + inner[3])
        manifest[part] = {
            "path": str(path.resolve()),
            "u0": (px0 - W / 2.0) / H, "u1": (px1 - W / 2.0) / H,
            "v0": (H - py1) / H,       "v1": (H - py0) / H,
        }
        print(f"  {part:9s} {crop.size[0]:4d}x{crop.size[1]:4d}"
              f"   u {manifest[part]['u0']:+.3f}..{manifest[part]['u1']:+.3f}"
              f"   v {manifest[part]['v0']:.3f}..{manifest[part]['v1']:.3f}")

    (out_dir / "parts.json").write_text(json.dumps(manifest, indent=2))
    print(f"[cut_parts] {len(manifest)} parts -> {out_dir}")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", help="staged character PNG")
    ap.add_argument("subject", help="subject id, e.g. mandrew")
    ap.add_argument("--bands", help="JSON file of band overrides")
    args = ap.parse_args()
    bands = None
    if args.bands:
        bands = json.loads(Path(args.bands).read_text())
    cut(args.source, args.subject, bands)
    return 0


if __name__ == "__main__":
    sys.exit(main())
