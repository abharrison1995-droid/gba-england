"""Pre-flight check for generated sheets, replicating ArtImportTool's checks outside Unity.

Checks, per ART_PIPELINE.md / CLAUDE.md §12:
  1. JSON fields sane and grid matches PNG dimensions.
  2. One drawing per cell (layout): no empty cells, no fragment frames.
  3. Figure fills ~90% of cell height (measured on keyed mask).
  4. Baseline drift across cells <= 2 px at final size (65 px cell)  [death exempt]
  5. Mean opaque width per cell within 1.4x of the accepted idle sheet  [never exempt]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

INCOMING = Path("art_incoming")
PROCESSED = INCOMING / "processed"
FINAL_CELL = 65.0  # px at final size for a 512 px source cell
DRIFT_LIMIT_FINAL_PX = 2.0
WIDTH_TOLERANCE = 1.4
MAGENTA = np.array([255, 0, 255])


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


def main():
    # reference: accepted idle sheet mean opaque width per cell
    idle_png = PROCESSED / "sheet_char_player_idle.png"
    idle_mean = None
    if idle_png.exists():
        meta, img = load_pair(idle_png)
        mask = key_mask(img)
        widths = []
        for i in range(meta["columns"] * meta["rows"]):
            s = cell_stats(mask, meta["frameWidth"], meta["frameHeight"], i % meta["columns"], i // meta["columns"])
            if s:
                widths.append(s["mean_width"])
        idle_mean = float(np.mean(widths))
        print(f"reference idle: mean width {idle_mean:.0f}px/cell over {len(widths)} cells")

    ok = True
    for name in ("sheet_char_player_attack.png", "sheet_char_player_cast.png", "sheet_char_player_death.png"):
        png = INCOMING / name
        if not png.exists():
            print(f"\n=== {name} === MISSING")
            ok = False
            continue
        ok = check_sheet(png, idle_mean) and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
