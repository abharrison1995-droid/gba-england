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


def bbox_of(img):
    """Opaque bounding box, or None if the frame is empty."""
    alpha = img.getchannel("A")
    return alpha.getbbox()


def mean_opaque_width(img, threshold=8):
    """Mean width of the opaque region over rows that have any opacity."""
    alpha = img.getchannel("A")
    w, h = alpha.size
    px = alpha.load()
    widths = []
    for y in range(h):
        xs = [x for x in range(w) if px[x, y] >= threshold]
        if xs:
            widths.append(xs[-1] - xs[0] + 1)
    return sum(widths) / len(widths) if widths else 0.0


def load_frames(action_dir):
    manifest = json.loads((action_dir / "manifest.json").read_text())
    paths = sorted(action_dir.glob("frame_*.png"))
    if len(paths) != manifest["frames"]:
        raise SystemExit(
            f"ERROR: {action_dir.name}: manifest says {manifest['frames']} "
            f"frames, found {len(paths)} PNGs. Re-render the subject.")
    return manifest, [Image.open(p).convert("RGBA") for p in paths]


def measure(frames, action):
    """Return (report_lines, failures, stats) for one action's frames."""
    lines, failures = [], []
    boxes = [bbox_of(f) for f in frames]
    if any(b is None for b in boxes):
        failures.append(f"{action}: frame(s) rendered empty — nothing in view")
        return lines, failures, {}

    cell_h = frames[0].size[1]
    cell_w = frames[0].size[0]
    if len({f.size for f in frames}) != 1:
        failures.append(f"{action}: frames are not all the same size")

    baselines = [b[3] for b in boxes]            # bottom edge = feet
    drift = max(baselines) - min(baselines)
    fills = [(b[3] - b[1]) / cell_h for b in boxes]
    widths = [mean_opaque_width(f) / cell_w for f in frames]
    stats = {"fill": sum(fills) / len(fills),
             "width": sum(widths) / len(widths),
             "drift": drift}

    lines.append(f"  {action:9s} drift {drift:2d} px   "
                 f"fill {stats['fill']:.0%}   width {stats['width']:.0%}")

    if action not in SHAPE_CHANGING:
        if drift != 0:
            failures.append(
                f"{action}: baseline drifts {drift} px across frames — the "
                f"figure bobs. Non-exempt actions must be 0.")
        if not 0.80 <= stats["fill"] <= 0.95:
            failures.append(
                f"{action}: figure fills {stats['fill']:.0%} of cell height; "
                f"the contract wants ~90%. Adjust the `fill` argument to "
                f"render_subject.")
    return lines, failures, stats


def pack_action(subject, action_dir, category, check_only, idle_width=None):
    manifest, frames = load_frames(action_dir)
    action = manifest["action"]
    lines, failures, stats = measure(frames, action)

    if idle_width and stats.get("width"):
        ratio = idle_width / stats["width"]
        if ratio > 1.4:
            failures.append(
                f"{action}: body is {ratio:.2f}x narrower than idle (limit "
                f"1.4x) — the importer will refuse it. Check the camera "
                f"azimuth matches idle's.")

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

        idle_width = None
        for adir in action_dirs:
            stats, failures = pack_action(
                subject, adir, args.category, args.check, idle_width)
            if adir.name == "idle":
                idle_width = stats.get("width")
            all_failures += failures

    if all_failures:
        print(f"\n{len(all_failures)} check(s) failed — nothing written for "
              f"the failing actions.")
        return 1
    print("\nAll checks passed." if not args.check else "\nCheck complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
