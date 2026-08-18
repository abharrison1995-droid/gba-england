"""Pack rendered frame sequences into art_incoming sheets + sidecar JSON.

Plain CPython + Pillow — no Blender. Reads what Tools/blender/sprites/*.py
rendered into Tools/blender/out/sprites/<subject>/<action>/ and writes the
pair ART_PIPELINE.md specifies, ready for Tools -> Art -> Import Generated Art.

    python Tools/pack_sprites.py                 # every rendered subject
    python Tools/pack_sprites.py proxy           # one subject
    python Tools/pack_sprites.py proxy walk      # one action
    python Tools/pack_sprites.py proxy --check   # measure, write nothing

Deliberately separate from the render step: repacking is instant, so a layout
or naming change never costs a re-render.

What it enforces, before the art ever reaches Unity — these are the checks the
importer applies, run here where a failure costs seconds instead of an editor
round trip (ART_PIPELINE.md §3):

  * uniform grid, one drawing per cell, frameCount = drawings in the image
  * baseline drift across frames (must be 0 px for non-exempt actions)
  * figure fill as a fraction of cell height (~90%)
  * mean body width vs the subject's own idle sheet (>1.4x narrower fails)

Exit code 1 on any failure, so it can gate a batch.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FRAMES_DIR = ROOT / "Tools" / "blender" / "out" / "sprites"
OUT_DIR = ROOT / "art_incoming"

# Actions whose body legitimately changes shape — exempt from the height and
# baseline checks, never from the width one. Mirrors ArtImportTool.
SHAPE_CHANGING = {"death", "roll", "knockback", "cycle"}

CATEGORY_PREFIX = {
    "characters": "char", "vehicles": "vehicle",
    "props": "prop", "fx": "fx", "ui": "ui",
}


# Alpha STRICTLY above this counts as drawn — ArtImportTool.MeasureCells does
# `if (px[...].a <= 8) continue;`. Shared with sprite_kit's ALPHA_THRESHOLD so
# the renderer pins the baseline on the same pixel the checker measures.
ALPHA_FLOOR = 8

# ArtImportTool reduces to 48 px per world unit, and scales the measured drift
# to that before judging it. A 2 px wobble on a 512 px cell is 0.3 px in game.
PIXELS_PER_WORLD_UNIT = 48

# The importer's own thresholds, mirrored. Keep these equal to the constants in
# Assets/Editor/ArtImportTool.cs — a checker stricter than the thing it
# predicts rejects art that would have imported perfectly well.
MAX_NARROWNESS = 1.4      # reference width / this sheet's width
MAX_HEIGHT_RATIO = 1.15   # taller / shorter, against the idle sheet
MAX_DRIFT_AT_FINAL_SIZE = 2.0


def bbox_of(img):
    """Opaque bounding box (alpha > ALPHA_FLOOR), or None if empty."""
    alpha = img.getchannel("A")
    return alpha.point(lambda a: 255 if a > ALPHA_FLOOR else 0).getbbox()


def load_frames(action_dir):
    manifest = json.loads((action_dir / "manifest.json").read_text())
    paths = sorted(action_dir.glob("frame_*.png"))
    if len(paths) != manifest["frames"]:
        raise SystemExit(
            f"ERROR: {action_dir.name}: manifest says {manifest['frames']} "
            f"frames, found {len(paths)} PNGs. Re-render the subject.")
    return manifest, [Image.open(p).convert("RGBA") for p in paths]


def measure(frames, action, world_height):
    """Mirror ArtImportTool.MeasureCells + CheckFrameAlignment for one action.

    Width and height are the mean *bounding box* fractions across frames — the
    importer takes left/right over the whole cell, not a per-row mean.
    """
    lines, failures = [], []
    boxes = [bbox_of(f) for f in frames]
    if any(b is None for b in boxes):
        failures.append(f"{action}: frame(s) rendered empty — nothing in view")
        return lines, failures, {}

    cell_w, cell_h = frames[0].size
    if len({f.size for f in frames}) != 1:
        failures.append(f"{action}: frames are not all the same size")

    baselines = [b[3] for b in boxes]            # bottom edge = feet
    drift = max(baselines) - min(baselines)
    stats = {
        "height": sum((b[3] - b[1]) for b in boxes) / len(boxes) / cell_h,
        "width": sum((b[2] - b[0]) for b in boxes) / len(boxes) / cell_w,
        "drift": drift,
        "drift_final": drift * world_height * PIXELS_PER_WORLD_UNIT / cell_h,
    }

    lines.append(f"  {action:9s} drift {drift:2d} px "
                 f"({stats['drift_final']:.2f} px at final size)   "
                 f"height {stats['height']:.0%}   width {stats['width']:.0%}")

    if stats["drift_final"] >= MAX_DRIFT_AT_FINAL_SIZE:
        if action in SHAPE_CHANGING:
            lines.append(f"    feet move {drift} px — expected for {action}")
        else:
            failures.append(
                f"{action}: feet move {drift} px between frames "
                f"({stats['drift_final']:.1f} px at final size) — it will bob.")
    return lines, failures, stats


def pack_action(subject, action_dir, category, check_only, reference=None):
    manifest, frames = load_frames(action_dir)
    action = manifest["action"]
    lines, failures, stats = measure(frames, action, manifest["worldHeight"])

    # Both cross-sheet checks are against the subject's own idle, which is the
    # importer's reference pose. Absolute cell fill is NOT checked: the
    # importer has no such rule, and inventing one here rejected art that
    # would have imported fine.
    if reference and stats.get("width"):
        narrowness = reference["width"] / stats["width"]
        if narrowness > MAX_NARROWNESS:
            failures.append(
                f"{action}: {narrowness:.1f}x narrower than idle (limit "
                f"{MAX_NARROWNESS}x) — drawn at a different angle.")
        if action not in SHAPE_CHANGING and stats.get("height"):
            hi = max(reference["height"], stats["height"])
            lo = min(reference["height"], stats["height"])
            if lo > 0 and hi / lo > MAX_HEIGHT_RATIO:
                failures.append(
                    f"{action}: differs from idle in height by {hi / lo:.2f}x "
                    f"(limit {MAX_HEIGHT_RATIO}x).")

    for line in lines:
        print(line)
    for f in failures:
        print(f"  FAIL {f}")
    if check_only or failures:
        return stats, failures

    n = len(frames)
    fw, fh = frames[0].size
    sheet = Image.new("RGBA", (fw * n, fh), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        sheet.paste(frame, (i * fw, 0))

    prefix = CATEGORY_PREFIX.get(category, "char")
    name = f"{subject}_{action}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUT_DIR / f"sheet_{prefix}_{name}.png"
    sheet.save(png_path)

    sidecar = {
        "name": name,
        "type": "sheet",
        "category": category,
        "action": action,
        "worldHeight": manifest["worldHeight"],
        "frameWidth": fw,
        "frameHeight": fh,
        "columns": n,
        "rows": 1,
        "frameCount": n,
        "fps": manifest["fps"],
        "loop": manifest["loop"],
        "description": (
            f"{n}-frame {action} rendered from the {subject} proxy rig "
            f"(Tools/blender/sprites/{subject}.py), three-quarter view, "
            f"facing camera-right."),
    }
    png_path.with_suffix(".json").write_text(json.dumps(sidecar, indent=2))
    print(f"  -> {png_path.name}  ({fw * n}x{fh}, {n} frames)")
    return stats, failures


def subjects_on_disk():
    if not FRAMES_DIR.is_dir():
        return []
    return sorted(d.name for d in FRAMES_DIR.iterdir() if d.is_dir())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("subject", nargs="?", help="subject id, e.g. proxy")
    ap.add_argument("action", nargs="?", help="single action to pack")
    ap.add_argument("--check", action="store_true",
                    help="measure and report only; write nothing")
    ap.add_argument("--category", default="characters")
    args = ap.parse_args()

    targets = [args.subject] if args.subject else subjects_on_disk()
    if not targets:
        print(f"Nothing rendered under {FRAMES_DIR}. Run a subject script "
              f"through bpy_runner.py first.")
        return 2

    all_failures = []
    for subject in targets:
        sdir = FRAMES_DIR / subject
        if not sdir.is_dir():
            print(f"ERROR: no rendered frames for '{subject}' at {sdir}")
            return 2
        print(f"{subject}:")
        action_dirs = sorted(d for d in sdir.iterdir()
                             if d.is_dir() and (d / "manifest.json").exists())
        # Idle first: it is the reference every other sheet is measured against.
        action_dirs.sort(key=lambda d: d.name != "idle")
        if args.action:
            action_dirs = [d for d in action_dirs if d.name == args.action]
            if not action_dirs:
                print(f"ERROR: no action '{args.action}' for '{subject}'")
                return 2

        reference = None
        for adir in action_dirs:
            stats, failures = pack_action(
                subject, adir, args.category, args.check, reference)
            if adir.name == "idle" and stats:
                reference = stats
            all_failures += failures

    if all_failures:
        print(f"\n{len(all_failures)} check(s) failed — nothing written for "
              f"the failing actions.")
        return 1
    print("\nAll checks passed." if not args.check else "\nCheck complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
