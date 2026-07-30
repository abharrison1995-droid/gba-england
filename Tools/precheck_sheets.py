"""Pre-flight check for generated sheets, replicating ArtImportTool's checks outside Unity.

Checks, per ART_PIPELINE.md / CLAUDE.md §12:
  1. JSON fields sane and grid matches PNG dimensions.
  2. One drawing per cell (layout): no empty cells, no fragment frames.
  3. Figure fills ~90% of cell height (measured on keyed mask).
  4. Baseline drift across cells <= 2 px at final size (65 px cell)  [death exempt]
  5. Mean opaque width per cell within 1.4x of *that subject's own* idle sheet  [never exempt]
  6. Frames actually differ from one another (nothing else catches a tiled still)

Checks the band-2 sheets by default (ART_PIPELINE.md §7.4). Pass sheet filenames as
arguments to check a different set:

    python Tools/precheck_sheets.py
    python Tools/precheck_sheets.py sheet_char_villager_idle.png
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

INCOMING = Path("art_incoming")
PROCESSED = INCOMING / "processed"
FINAL_CELL = 65.0  # px at final size for a 512 px source cell
DRIFT_LIMIT_FINAL_PX = 2.0
WIDTH_TOLERANCE = 1.4

# How much a frame must differ from the one before it: pixels that changed, over the mean
# subject size of the pair. Calibrated on every sheet accepted so far rather than guessed.
# Because each frame is an independent photographic generation, essentially every subject
# pixel differs between frames, so real values land above 1.0 — the least-varying real pair
# in the project is the villager's idle at 1.02, and the most subtle player idle pair is
# 1.13. A cell tiled from another measures exactly 0.00. This threshold sits an order of
# magnitude below anything real, so it catches a still without ever arguing with a subtle idle.
STILL_FRAME_RATIO = 0.10

MAGENTA = np.array([255, 0, 255])

# Band 2 of the queue in ART_PIPELINE.md §7.4/§7.5: the tutorial cast. Daniel Pauls needs no
# hostile set and the geezer never casts, which is why the two lists differ.
DEFAULT_SHEETS = (
    "sheet_char_danielpauls_idle.png",
    "sheet_char_danielpauls_walk.png",
    "sheet_char_danielpauls_cast.png",
    "sheet_char_underhoused_idle.png",
    "sheet_char_underhoused_walk.png",
    "sheet_char_underhoused_attack.png",
    "sheet_char_underhoused_hurt.png",
    "sheet_char_underhoused_death.png",
)

SHEET_NAME = re.compile(r"^sheet_char_(?P<subject>.+)_(?P<action>[^_]+)\.png$")


def key_mask(img: Image.Image, threshold: int = 60) -> np.ndarray:
    """Opaque-subject mask: True where pixel is NOT magenta-ish (and alpha > 0 if present).

    threshold 60 matches the lenient subject measure; 200 approximates the
    importer's alpha-after-unmix feet measure (it drops magenta-close edge
    pixels, e.g. dark shoe soles bleeding into the backdrop).
    """
    arr = np.asarray(img.convert("RGBA")).astype(np.int16)
    rgb, alpha = arr[..., :3], arr[..., 3]
    dist = np.abs(rgb - MAGENTA).sum(axis=2)
    return (dist > threshold) & (alpha > 10)


def cell_stats(mask: np.ndarray, fw: int, fh: int, col: int, row: int):
    cell = mask[row * fh:(row + 1) * fh, col * fw:(col + 1) * fw]
    ys, xs = np.nonzero(cell)
    if len(ys) == 0:
        return None
    h = ys.max() - ys.min() + 1
    # mean width across occupied rows (the importer's width measure)
    row_widths = cell.sum(axis=1)
    occupied = row_widths[row_widths > 0]
    mean_w = float(occupied.mean())
    return {
        "height_px": int(h),
        "fill": h / fh,
        "mean_width": mean_w,
        "width_frac": mean_w / fw,
        "baseline_row": int(ys.max()),  # bottommost subject pixel within cell
    }


def check_frames_differ(img: Image.Image, mask: np.ndarray, fw: int, fh: int, cols: int,
                        count: int, problems: list):
    """Frames must actually be different drawings.

    Nothing else in this file can catch a sheet tiled from a single frame: every other check
    measures one cell at a time, so one drawing repeated six times reads as six flawless
    cells. That is exactly how the first Daniel Pauls delivery passed the dimension, layout,
    fill, baseline and width checks while being a still.

    Two tests, because the two failures look different in the log. Byte-identical cells are
    named against the earlier cell they repeat, which points straight at the tiling. Then
    consecutive pairs are measured, catching a sheet whose frames are technically distinct
    and visually motionless.

    Deliberately applies to every action including death: in this pipeline each frame is a
    separate generation, so even a held final pose never comes out byte-identical. If a
    genuinely intentional held pose ever trips this, that is the point to add an exemption
    — not before.
    """
    rgb = np.asarray(img.convert("RGB")).astype(np.int16)

    def cell(i: int):
        col, row = i % cols, i // cols
        rows_ = slice(row * fh, (row + 1) * fh)
        columns_ = slice(col * fw, (col + 1) * fw)
        return rgb[rows_, columns_], mask[rows_, columns_]

    identical = []
    for i in range(1, count):
        for j in range(i):
            if np.array_equal(cell(i)[0], cell(j)[0]):
                identical.append((i, j))
                break

    if count > 1 and len(identical) == count - 1 and all(j == 0 for _, j in identical):
        problems.append(f"every cell is identical to cell 1 — this is one frame tiled "
                        f"{count} times, not an animation")
        return
    for later, first in identical:
        problems.append(f"cell {later + 1} is byte-identical to cell {first + 1}")

    identical_consecutive = {later for later, first in identical if later - first == 1}

    ratios = []
    for i in range(1, count):
        (before, mask_before), (after, mask_after) = cell(i - 1), cell(i)
        subject = (int(mask_before.sum()) + int(mask_after.sum())) / 2.0
        changed = int((np.abs(before - after).sum(axis=2) > 0).sum())
        ratio = changed / max(1.0, subject)
        ratios.append(ratio)
        if ratio < STILL_FRAME_RATIO and i not in identical_consecutive:
            problems.append(f"cells {i} and {i + 1} differ by only {ratio:.1%} of the figure "
                            f"— effectively a still (limit {STILL_FRAME_RATIO:.0%})")

    if ratios:
        print(f"  frame-to-frame change: {', '.join(f'{r:.2f}' for r in ratios)} "
              f"(min {min(ratios):.2f}, still below {STILL_FRAME_RATIO:.2f})")


def load_pair(png: Path):
    j = png.with_suffix(".json")
    meta = json.loads(j.read_text()) if j.exists() else None
    img = Image.open(png)
    return meta, img


def check_sheet(png: Path, idle_mean_width: float | None):
    print(f"\n=== {png.name} ===")
    problems = []
    meta, img = load_pair(png)
    if meta is None:
        print("  !! no sidecar JSON")
        return False
    action = meta.get("action", "?")
    exempt = action == "death"  # height/baseline exempt, width never exempt

    fw, fh = meta["frameWidth"], meta["frameHeight"]
    cols, rows = meta["columns"], meta["rows"]
    fc = meta["frameCount"]
    print(f"  JSON: action={action} {cols}x{rows} of {fw}x{fh}, frameCount={fc}, "
          f"fps={meta.get('fps')}, loop={meta.get('loop')}, worldHeight={meta.get('worldHeight')}")
    if img.size != (cols * fw, rows * fh):
        problems.append(f"PNG is {img.size}, JSON grid expects {cols*fw}x{rows*fh}")
        print(f"  !! dimension mismatch: PNG {img.size} vs grid {cols*fw}x{rows*fh}")
        return False
    if fc > cols * rows:
        problems.append(f"frameCount {fc} > grid capacity {cols*rows}")
    if meta.get("worldHeight") != 1.35:
        problems.append(f"worldHeight {meta.get('worldHeight')} != 1.35")

    mask = key_mask(img)
    stats = []
    for i in range(cols * rows):
        col, row = i % cols, i // cols
        s = cell_stats(mask, fw, fh, col, row)
        stats.append(s)
        tag = f"cell {i+1} (r{row+1}c{col+1})"
        if s is None:
            problems.append(f"{tag}: EMPTY")
        else:
            print(f"  {tag}: fill {s['fill']:.0%}  meanW {s['mean_width']:.0f}px "
                  f"({s['width_frac']:.2f} of cell)  baseline row {s['baseline_row']}")

    good = [s for s in stats[:fc] if s is not None]
    if len(good) < fc:
        problems.append(f"only {len(good)}/{fc} declared frames have content")

    # Only meaningful once every declared cell has something in it — comparing against an
    # empty cell would report a difference rather than the emptiness already reported above.
    if len(good) == fc:
        check_frames_differ(img, mask, fw, fh, cols, fc, problems)

    # fragment frames: figure under half the median height of the others.
    # Skipped for exempt actions (death): a prone final frame is legitimately
    # a third of the standing height — that is the pose, not a failed generation.
    if not exempt and good:
        med_h = float(np.median([g["height_px"] for g in good]))
        for i, s in enumerate(stats[:fc]):
            if s is not None and s["height_px"] < 0.5 * med_h:
                problems.append(f"cell {i+1}: fragment ({s['height_px']}px vs median {med_h:.0f}px)")

    if not exempt and good:
        fills = [g["fill"] for g in good]
        print(f"  fill range {min(fills):.0%}-{max(fills):.0%} (target ~89%)")
        if min(fills) < 0.75:
            problems.append(f"figure too small: min fill {min(fills):.0%} vs ~89% target")
        base = [g["baseline_row"] for g in good]
        drift_src = max(base) - min(base)
        drift_final = drift_src * FINAL_CELL / fh
        print(f"  baseline drift {drift_src}px src = {drift_final:.1f}px final (limit {DRIFT_LIMIT_FINAL_PX})")
        if drift_final > DRIFT_LIMIT_FINAL_PX:
            problems.append(f"baseline drift {drift_final:.1f}px final > {DRIFT_LIMIT_FINAL_PX}px")

        # Strict baseline: the importer measures feet on alpha AFTER key+unmix,
        # which drops magenta-close edge pixels (dark soles). A frame can pass
        # the lenient check above yet still read high to the importer — this
        # bit us on cast cell 6. Re-measure bottoms at threshold 200.
        strict = key_mask(img, 200)
        sbase = []
        for i in range(fc):
            col, row = i % cols, i // cols
            s = cell_stats(strict, fw, fh, col, row)
            if s is not None:
                sbase.append((i + 1, s["baseline_row"]))
        if len(sbase) >= 2:
            rows_only = [b for _, b in sbase]
            sdrift_src = max(rows_only) - min(rows_only)
            sdrift_final = sdrift_src * FINAL_CELL / fh
            print(f"  strict(200) baselines {sbase} -> drift {sdrift_final:.1f}px final")
            if sdrift_final > DRIFT_LIMIT_FINAL_PX:
                worst = min(sbase, key=lambda t: t[1])
                problems.append(
                    f"strict baseline drift {sdrift_final:.1f}px final > {DRIFT_LIMIT_FINAL_PX}px "
                    f"(cell {worst[0]} reads {worst[1]}; importer would refuse)")
    elif exempt:
        print("  (death: height/baseline checks exempt, width still applies)")

    if idle_mean_width and good:
        mean_w = float(np.mean([g["mean_width"] for g in good]))
        ratio = idle_mean_width / mean_w
        print(f"  width vs idle: {mean_w:.0f}px vs idle {idle_mean_width:.0f}px -> idle/new {ratio:.2f}x (limit {WIDTH_TOLERANCE}x)")
        if ratio > WIDTH_TOLERANCE:
            problems.append(f"too narrow: {ratio:.2f}x narrower than idle (limit {WIDTH_TOLERANCE}x)")

    if problems:
        print("  RESULT: WOULD REFUSE —")
        for p in problems:
            print(f"    - {p}")
    else:
        print("  RESULT: PASS (local replica of importer checks)")
    return not problems


def mean_width(png: Path) -> float | None:
    """Mean opaque width per cell, or None if the sheet is unusable as a reference."""
    if not png.exists():
        return None
    meta, img = load_pair(png)
    if meta is None:
        return None
    mask = key_mask(img)
    widths = []
    for i in range(meta["columns"] * meta["rows"]):
        s = cell_stats(mask, meta["frameWidth"], meta["frameHeight"],
                       i % meta["columns"], i // meta["columns"])
        if s:
            widths.append(s["mean_width"])
    return float(np.mean(widths)) if widths else None


def reference_width(subject: str):
    """The width reference for one subject: that subject's own idle sheet.

    The importer compares sheets of one subject against *each other* (CLAUDE.md §12), and it
    has to — the check catches a sheet drawn at the wrong scale for that character, and
    characters legitimately differ in build. Measuring band 2 against the player's idle would
    refuse Daniel Pauls for not being the player's shape.

    processed/ first, then staging, so a batch delivering a subject's idle alongside its walk
    references its own idle rather than having nothing to compare to.
    """
    for folder in (PROCESSED, INCOMING):
        width = mean_width(folder / f"sheet_char_{subject}_idle.png")
        if width is not None:
            return width, folder
    return None, None


def main():
    names = sys.argv[1:] or list(DEFAULT_SHEETS)
    references: dict[str, float | None] = {}
    ok = True

    for name in names:
        png = INCOMING / name
        if not png.exists():
            print(f"\n=== {name} === MISSING from {INCOMING}/")
            ok = False
            continue

        match = SHEET_NAME.match(png.name)
        subject = match.group("subject") if match else None

        if subject and subject not in references:
            width, folder = reference_width(subject)
            references[subject] = width
            if width is None:
                print(f"\nreference for '{subject}': none — no sheet_char_{subject}_idle.png in "
                      f"processed/ or staging, so the width check is skipped for this subject. "
                      f"Deliver its idle sheet first, or it goes unchecked.")
            else:
                print(f"\nreference for '{subject}': idle mean width {width:.0f}px/cell "
                      f"(from {folder.name}/)")

        ok = check_sheet(png, references.get(subject)) and ok

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
